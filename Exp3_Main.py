"""
模型入口，程序执行的开始，在该文件中配置必要的训练步骤
"""


from Exp3_Config import Training_Config
from Exp3_DataProc import train_data, val_data, test_data, id2relation
from torch.utils.data import DataLoader
from Exp3_Model import TextCNN_Model, SentenceRE
import torch
import os
from torch.utils.tensorboard import SummaryWriter
from sklearn import metrics
import time

device = 'cpu'

def train(model, loader):
    for index, data in enumerate(loader):
        #model(data['text'])
        token_ids = data['token_ids'].to(device)
        token_type_ids = data['token_type_ids'].to(device)
        attention_mask = data['attention_mask'].to(device)
        e1_mask = data['e1_mask'].to(device)
        e2_mask = data['e2_mask'].to(device)
        tag_ids = data['tag_id'].to(device)
        model.zero_grad()
        logits = model(token_ids, token_type_ids, attention_mask, e1_mask, e2_mask)
        loss = loss_function(logits, tag_ids)
        loss.backward()
        optimizer.step()
    
        running_loss += loss.item()
        if index % 10 == 9:
            writer.add_scalar('Training/training loss', running_loss / 10, epoch * len(train_loader) + i_batch)
            running_loss = 0.0


def validation(model, loader):
    tags_true = []
    tags_pred = []
    for index, data in enumerate(loader):
        #model(data['head'])
        token_ids = data['token_ids'].to(device)
        token_type_ids = data['token_type_ids'].to(device)
        attention_mask = data['attention_mask'].to(device)
        e1_mask = data['e1_mask'].to(device)
        e2_mask = data['e2_mask'].to(device)
        tag_ids = data['tag_id']
        logits = model(token_ids, token_type_ids, attention_mask, e1_mask, e2_mask)
        pred_tag_ids = logits.argmax(1)
        tags_true.extend(tag_ids.tolist())
        tags_pred.extend(pred_tag_ids.tolist())

    print(metrics.classification_report(tags_true, tags_pred, labels=list(idx2tag.keys()), target_names=list(idx2tag.values())))
    f1 = metrics.f1_score(tags_true, tags_pred, average='weighted')
    precision = metrics.precision_score(tags_true, tags_pred, average='weighted')
    recall = metrics.recall_score(tags_true, tags_pred, average='weighted')
    accuracy = metrics.accuracy_score(tags_true, tags_pred)
    writer.add_scalar('Validation/f1', f1, epoch)
    writer.add_scalar('Validation/precision', precision, epoch)
    writer.add_scalar('Validation/recall', recall, epoch)
    writer.add_scalar('Validation/accuracy', accuracy, epoch)

    '''if checkpoint_dict.get('epoch_f1'):
        checkpoint_dict['epoch_f1'][epoch] = f1
    else:
        checkpoint_dict['epoch_f1'] = {epoch: f1}
    if f1 > best_f1:
        best_f1 = f1
        checkpoint_dict['best_f1'] = best_f1
        checkpoint_dict['best_epoch'] = epoch
        torch.save(model.state_dict(), model_file)
    save_checkpoint(checkpoint_dict, checkpoint_file)'''


def predict(model, loader):
    for index, data in enumerate(loader):
        model(data['tail'])

def load_checkpoint(checkpoint_file, model, model_file):
    # load checkpoint if one exists
    if os.path.exists(checkpoint_file):
        checkpoint_dict = load_checkpoint(checkpoint_file)
        best_f1 = checkpoint_dict['best_f1']
        epoch_offset = checkpoint_dict['best_epoch'] + 1
        model.load_state_dict(torch.load(model_file))
    else:
        checkpoint_dict = {}
        best_f1 = 0.0
        epoch_offset = 0
    return best_f1, epoch_offset

if __name__ == "__main__":
    config = Training_Config()

    # 训练集验证集
    train_dataset = train_data
    train_loader = DataLoader(dataset=train_dataset, batch_size=config.batch_size)

    val_dataset = val_data
    val_loader = DataLoader(dataset=val_dataset, batch_size=config.batch_size)

    # 测试集数据集和加载器
    test_dataset = test_data
    test_loader = DataLoader(dataset=test_dataset, batch_size=config.batch_size)

    # 初始化模型对象
    #Text_Model = TextCNN_Model(configs=config)
    Text_Model = SentenceRE(config)
    # 损失函数设置
    loss_function = torch.nn.CrossEntropyLoss()  # torch.nn中的损失函数进行挑选，并进行参数设置
    # 优化器设置
    optimizer = torch.optim.Adam(params=Text_Model.parameters())  # torch.optim中的优化器进行挑选，并进行参数设置
    writer = SummaryWriter(os.path.join(config.log_dir, time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())))
    idx2tag = id2relation()

    # 训练和验证
    for epoch in range(config.epoch):
        print("Epoch: {}".format(config.epoch))
        Text_Model.train()
        train(Text_Model, loader=train_loader)
        #if epoch % config.num_val == 0:
        Text_Model.eval()
        with torch.no_grad():
            validation(Text_Model, loader=val_loader)

    # 预测（测试）
    predict(Text_Model, test_loader)
