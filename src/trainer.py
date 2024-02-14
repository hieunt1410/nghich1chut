import models
from transformers import AutoModel, AutoTokenizer
from tqdm import tqdm
from utils import *

def initiate(train_loader, valid_loader, test_loader):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    bert = BertModel.from_pretrained("vinai/phobert-base-v2")
    tokenizer = BertTokenizer.from_pretrained("vinai/phobert-base-v2")
    bert.to(device)
    tokenizer.to(device)
    
    model = getattr(models, 'Simple')(input_dim=768, hidden_dim=256, output_dim=2)
    model.to(device)
    
    opimizer = torch.optim.Adam(bert.parameters(), lr=2e-5)
    criterion = nn.CrossEntropyLoss()
    scheduler = torch.optim.lr_scheduler.StepLR(opimizer, step_size=5, gamma=0.1)
    
    settings = {
        'device': device,
        'bert': bert,
        'tokenizer': tokenizer,
        'opimizer': opimizer,
        'criterion': criterion,
        'scheduler': scheduler,
    }
    
    return 

def train_model(settings, train_loader, valid_loader, test_loader):
    bert = settings['bert']
    tokenizer = settings['tokenizer']
    optimizer = settings['optimizer']
    criterion = settings['criterion']
    scheduler = settings['scheduler']
    
    def train(model, bert, tokenizer, optimizer, criterion):
        model.train()
        epoch_loss = 0
        epoch_acc = 0
        results = []
        truth = []
        for batch in tqdm(train_loader):
            text = bat.text
            label = batch.label
            text.to(settings.device)
            label.to(settings.device)
            
            optimizer.zero_grad()
            text_encoded = tokenizer(text, padding=True, truncation=True, return_tensors='pt').to(settings.device)
            predictions = model(bert(text_encoded).pooler_output).squeeze(1)
            loss = criterion(predictions, label)
            acc = binary_accuracy(predictions, label)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            epoch_acc += acc.item()
        
        results.cat(predictions)
        truth.cat(label)
        return results, truth, epoch_loss / len(train_loader), epoch_acc / len(train_loader)
    
    def evaluate(model, bert, tokenizer, criterion):
        model.eval()
        epoch_loss = 0
        epoch_acc = 0
        results = []
        truth = []
        with torch.no_grad():
            for batch in tqdm(valid_loader):
                text = batch.text
                label = batch.label
                text.to(settings.device)
                label.to(settings.device)
                
                text_encoded = tokenizer(text, padding=True, truncation=True, return_tensors='pt').to(settings.device)
                predictions = model(bert(text_encoded).pooler_output).squeeze(1)
                loss = criterion(predictions, label)
                acc = binary_accuracy(predictions, label)
                epoch_loss += loss.item()
                epoch_acc += acc.item()
        results.cat(predictions)
        truth.cat(label)
        return results, truth, epoch_loss / len(valid_loader), epoch_acc / len(valid_loader)
    
    best_valid = 1e8
    for epoch in range(1, 20):
        train_results, train_truth, train_loss, train_acc = train(model, bert, tokenizer, optimizer, criterion)
        valid_results, valid_truth, valid_loss, valid_acc = evaluate(model, bert, tokenizer, criterion)
        scheduler.step()
        train_acc, train_prec, train_recall, train_f1 = metrics(train_results, train_truths)
        val_acc, val_prec, val_recall, val_f1 = metrics(val_results, val_truths)
        
        if epoch == 1:
            print(f'Epoch  |     Train Loss     |     Train Accuracy     |     Valid Loss     |     Valid Accuracy     |     Precision     |     Recall     |     F1-Score     |')
            
        print(f'{epoch:^7d}|{train_loss:^20.4f}|{train_acc:^24.4f}|{val_loss:^20.4f}|{val_acc:^24.4f}|{val_prec:^19.4f}|{val_recall:^16.4f}|{val_f1:^18.4f}|')

        if valid_loss < best_valid:
            best_valid = valid_loss
            save_model(model, 'best_model')
        
        if test_loader is not None:
            model = load_model(hyp_params, name=hyp_params.name)
            results, truths, val_loss = evaluate(model, bert, tokenizer, feature_extractor, criterion, test=True)
            test_acc, test_prec, test_recall, test_f1 = metrics(results, truths)
        
            print("\n\nTest Acc {:5.4f} | Test Precision {:5.4f} | Test Recall {:5.4f} | Test f1-score {:5.4f}".format(test_acc, test_prec, test_recall, test_f1))