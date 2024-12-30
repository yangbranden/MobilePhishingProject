# Using code generated from ChatGPT as a base
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Step 1: Load and Preprocess Data
class WebsiteDataset(Dataset):
    def __init__(self, features, labels):
        self.features = torch.tensor(features, dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.float32)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]

# Load CSV data
csv_file = "your_file.csv"  # Replace with your CSV file path
data = pd.read_csv(csv_file)

# Assuming 'target' is the label column
X = data.drop(columns=['target']).values
y = data['target'].values

# Normalize features
scaler = StandardScaler()
X = scaler.fit_transform(X)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Create datasets and dataloaders
train_dataset = WebsiteDataset(X_train, y_train)
test_dataset = WebsiteDataset(X_test, y_test)

train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

# Step 2: Define the RNN Model
class RNNClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers):
        super(RNNClassifier, self).__init__()
        self.rnn = nn.RNN(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        # x: (batch_size, sequence_length, input_size)
        out, _ = self.rnn(x)
        # Use only the output of the last RNN time step
        out = out[:, -1, :]  # (batch_size, hidden_size)
        out = self.fc(out)
        out = self.sigmoid(out)
        return out

# Step 3: Initialize Model, Loss, and Optimizer
input_size = X_train.shape[1]  # Number of features
hidden_size = 64
num_layers = 1

model = RNNClassifier(input_size, hidden_size, num_layers)
criterion = nn.BCELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Step 4: Train the Model
num_epochs = 20

for epoch in range(num_epochs):
    model.train()
    for features, labels in train_loader:
        features = features.unsqueeze(1)  # Add sequence dimension: (batch_size, seq_length, input_size)
        labels = labels.unsqueeze(1)      # Make labels shape match: (batch_size, 1)

        # Forward pass
        outputs = model(features)
        loss = criterion(outputs, labels)

        # Backward pass and optimization
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}")

# Step 5: Evaluate the Model
model.eval()
with torch.no_grad():
    correct = 0
    total = 0
    for features, labels in test_loader:
        features = features.unsqueeze(1)
        labels = labels.unsqueeze(1)
        outputs = model(features)
        predicted = (outputs > 0.5).float()
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

    accuracy = correct / total
    print(f"Test Accuracy: {accuracy:.4f}")
