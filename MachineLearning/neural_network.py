import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder

# Define RNN-based Model
class RNNBinaryClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers=1):
        super(RNNBinaryClassifier, self).__init__()
        self.rnn = nn.RNN(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        out, _ = self.rnn(x)
        out = self.fc(out[:, -1, :])  # Use the last RNN output
        return self.sigmoid(out)

# Train the model
def train_model(model, X_train, y_train, optimizer, criterion, epochs=50):
    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        outputs = model(X_train)
        loss = criterion(outputs, y_train)
        loss.backward()
        optimizer.step()
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}")

# Evaluate feature importance
def compute_feature_importance(model, X_test, y_test):
    model.eval()
    baseline_accuracy = accuracy_score(
        y_test.detach().numpy(),
        (model(X_test).detach().numpy() > 0.5).astype(int)
    )
    importances = []
    for i in range(X_test.shape[2]):
        X_test_permuted = X_test.clone()
        X_test_permuted[:, :, i] = torch.rand(X_test_permuted[:, :, i].shape)
        permuted_accuracy = accuracy_score(
            y_test.detach().numpy(),
            (model(X_test_permuted).detach().numpy() > 0.5).astype(int)
        )
        importances.append(baseline_accuracy - permuted_accuracy)
    return importances

# Main function
def main():
    # Load and process data
    data = pd.read_csv('processed_data_12_30_2024.csv', low_memory=False)
    
    # Leave out certain columns we are only keeping in for debugging/looking at the data manually
    data = data.drop(columns=['url'])
    data = data.drop(columns=['public_url'])
    
    # Convert all non-numeric columns into numeric values;
    # Essentially like hot mapping that we did manually in our data_cleaning.py script
    label_encoder = LabelEncoder()
    for col in data.select_dtypes(include=['object']).columns:
        try:
            data[col] = label_encoder.fit_transform(data[col])
        except ValueError as e:
            print(f"Could not convert column {col}: {e}")
    
    X = data.drop(columns=['phishing']).values
    y = data['phishing'].values

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Convert to PyTorch tensors
    X_train_tensor = torch.tensor(X_train, dtype=torch.float32)
    print("Made it here")
    y_train_tensor = torch.tensor(y_train, dtype=torch.float32).view(-1, 1)
    X_test_tensor = torch.tensor(X_test, dtype=torch.float32)
    y_test_tensor = torch.tensor(y_test, dtype=torch.float32).view(-1, 1)

    # Reshape for RNN input (sequence length = 1)
    X_train_tensor = X_train_tensor.view(X_train_tensor.shape[0], 1, -1)
    X_test_tensor = X_test_tensor.view(X_test_tensor.shape[0], 1, -1)

    # Initialize model, optimizer, and loss function
    input_size = X_train.shape[1]
    hidden_size = 16
    model = RNNBinaryClassifier(input_size, hidden_size)
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.BCELoss()

    # Train the model
    print("Training initial model...")
    train_model(model, X_train_tensor, y_train_tensor, optimizer, criterion)

    # Evaluate the initial model
    model.eval()
    predictions_initial = (model(X_test_tensor).detach().numpy() > 0.5).astype(int)
    initial_accuracy = accuracy_score(y_test, predictions_initial)
    print(f"Initial model accuracy: {initial_accuracy:.4f}")

    # Compute feature importance
    feature_importances = compute_feature_importance(model, X_test_tensor, y_test_tensor)
    print("Feature importances:", feature_importances)

    # Select top features
    num_top_features = 5
    top_features = np.argsort(feature_importances)[-num_top_features:]
    print(f"Top {num_top_features} features selected:", top_features)

    # Reduce dataset to top features
    X_train_reduced = X_train[:, top_features]
    X_test_reduced = X_test[:, top_features]
    X_train_tensor_reduced = torch.tensor(X_train_reduced, dtype=torch.float32).view(X_train_reduced.shape[0], 1, -1)
    X_test_tensor_reduced = torch.tensor(X_test_reduced, dtype=torch.float32).view(X_test_reduced.shape[0], 1, -1)

    # Retrain the model
    print(f"Retraining model with top {num_top_features} features...")
    model = RNNBinaryClassifier(len(top_features), hidden_size)
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    train_model(model, X_train_tensor_reduced, y_train_tensor, optimizer, criterion)

    # Evaluate the retrained model
    model.eval()
    predictions_retrained = (model(X_test_tensor_reduced).detach().numpy() > 0.5).astype(int)
    retrained_accuracy = accuracy_score(y_test, predictions_retrained)
    print(f"Retrained model accuracy with top {num_top_features} features: {retrained_accuracy:.4f}")

# Run the main function
if __name__ == "__main__":
    main()
