import torch
from torch import nn, optim
from torch.utils.data import DataLoader, TensorDataset

from tfn.models.model import Model


class LSTM(nn.Module):
    def __init__(self, input_size, seq_length, hidden_size, output_size, num_layers):
        super(LSTM, self).__init__()
        self.lstm = nn.LSTM(input_size=input_size, hidden_size=hidden_size, num_layers=num_layers,
                            bidirectional=True, batch_first=True)
        self.fc = nn.Linear(2*hidden_size*seq_length, output_size)

    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        lstm_out_flat = lstm_out.reshape(
            (lstm_out.shape[0], -1)
        )
        fc_out = self.fc(lstm_out_flat)
        print(fc_out.shape)
        act_out = torch.sigmoid(fc_out)
        return act_out


class LSTMModel(Model):
    def __init__(self, num_features=50):
        super().__init__()
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        #TODO: seq_length needs to be set automatically by X.shape
        seq_length = 29
        num_features = num_features
        hidden_dim = 50
        output_dim = 1
        num_layers = 2
        self.model = LSTM(input_size=num_features, seq_length=seq_length, hidden_size=hidden_dim, output_size=output_dim,
                          num_layers=num_layers)
        self.model.double()
        self.batch_size = 20

    def fit(self, X, y, epochs=5):
        learning_rate = 0.001
        momentum = 0.1

        optimizer = optim.SGD(self.model.parameters(), lr=learning_rate, momentum=momentum)
        criterion = nn.BCELoss()

        train_data = TensorDataset(torch.tensor(X), torch.tensor(y))
        train_loader = DataLoader(train_data, batch_size=self.batch_size)

        for epoch in range(epochs):
            print("Epoch: %s" % epoch)
            training_loss = 0
            for i, (X_train, y_train) in enumerate(train_loader):
                print(i / len(train_loader))
                self.model.zero_grad()
                y_pred = self.model(X_train)
                loss = criterion(y_pred, y_train.double())
                training_loss += loss.item()
                loss.backward()
                optimizer.step()
            print('Training Loss: %.4g' % training_loss)

    def predict(self, X):
        test_data = TensorDataset(X)
        test_loader = DataLoader(test_data, batch_size=self.batch_size)
        predictions_list = []
        for X_test in test_loader:
            y_pred = self.model(X_test)
            if self.device == "cpu":
                predictions_list.append(y_pred.data.numpy())
            else:
                predictions_list.append(y_pred.data.cpu().numpy())
        predictions = np.vstack(predictions_list)
        return predictions


if __name__ == "__main__":
    from tfn.preprocess import Dataset
    from tfn.feature_extraction.embedding import Embedding
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, roc_auc_score
    import numpy as np

    # Get data
    data = Dataset('twitter')
    emb = Embedding(data.X)
    X = emb.corpus_vectors
    y = np.array(data.y)

    X_train, X_test, y_train, y_test = train_test_split(X, y)

    print(X_train.shape, X_test.shape, y_train.shape, y_test.shape)

    lstm = LSTMModel()
    lstm.fit(X_train, y_train, epochs=50)

    y_pred = lstm.predict(X_test)

    print('GLoVe + LSTM accuracy:', round(accuracy_score(y_test, y_pred), 4))
    print('GLoVe + LSTM AUC:', round(roc_auc_score(y_test, y_pred), 4))