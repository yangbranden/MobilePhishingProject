import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import shap
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder

class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(LSTMModel, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.fc1 = nn.Linear(hidden_size, 32)
        self.fc2 = nn.Linear(32, output_size)
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        # LSTM layer
        lstm_out, (hn, cn) = self.lstm(x)
        # Use the last hidden state for classification
        x = hn[-1]
        # Fully connected layers
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        x = self.sigmoid(x)
        return x

# Train the model
def train_model(model, X_train, y_train, optimizer, criterion, epochs=20):
    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        outputs = model(X_train) # Forward pass
        loss = criterion(outputs, y_train)
        loss.backward() # Backward pass
        optimizer.step() # Optimizer step
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}")

# Feature Importance Method 1: Permutation Feature Importance
def compute_feature_importance_permutation(model, X_test, y_test):
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

# Feature Importance Method 2: Shapley values (SHAP)
def compute_feature_importance_shap(model, X_sample):
    # Use the first hidden layer output as SHAP base model output
    def model_predict(data):
        data_tensor = torch.tensor(data, dtype=torch.float32).view(data.shape[0], 1, -1)
        return model(data_tensor).detach().numpy()

    explainer = shap.KernelExplainer(model_predict, X_sample)
    shap_values = explainer.shap_values(X_sample, nsamples=100)
    # Aggregate SHAP values over sequences (if sequence length > 1)
    aggregated_shap_values = np.mean(np.abs(shap_values), axis=0)
    return aggregated_shap_values

# Main function
def main():
    # Load and process data
    data = pd.read_csv('data_all_1_1_2025.csv', low_memory=False)
    
    # Leave out certain columns we are only keeping in for debugging/looking at the data manually
    data = data.drop(columns=['url', 'public_url', 'reasoning', 'phishing'], errors='ignore')
    
    # Convert all non-numeric columns into numeric values;
    # Essentially like hot mapping that we did manually in our data_cleaning.py script
    label_encoder = LabelEncoder()
    for col in data.select_dtypes(include=['object']).columns:
        try:
            data[col] = label_encoder.fit_transform(data[col])
        except ValueError as e:
            print(f"Could not convert column {col}: {e}")
    
    # Predict 'blocked' column
    data['blocked'] = data['blocked'].replace(-1, 1)
    X = data.drop(columns=['blocked']).values
    y = data['blocked'].values

    # Get column names
    column_names = data.drop(columns=['blocked']).columns

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Convert to PyTorch tensors
    X_train_tensor = torch.tensor(X_train, dtype=torch.float32)
    y_train_tensor = torch.tensor(y_train, dtype=torch.float32).view(-1, 1)
    X_test_tensor = torch.tensor(X_test, dtype=torch.float32)
    y_test_tensor = torch.tensor(y_test, dtype=torch.float32).view(-1, 1)

    # Reshape for RNN input (sequence length = 1)
    X_train_tensor = X_train_tensor.view(X_train_tensor.shape[0], 1, -1)
    X_test_tensor = X_test_tensor.view(X_test_tensor.shape[0], 1, -1)

    # Model definition
    input_size = X_train.shape[1]
    hidden_size = 64  # number of LSTM units
    output_size = 1  # binary classification

    # Iterative feature selection and retraining
    prev_importances = None
    convergence_threshold = 0.01
    max_iterations = 10
    iteration = 0

    # Choose importance calculation method
    use_shap = False  # Set to True for SHAP, False for Permutation Feature Importance

    while iteration < max_iterations:
        print(f"Iteration {iteration+1}")

        # Define and train model
        model = LSTMModel(input_size, hidden_size, output_size)
        criterion = nn.BCELoss()  # Binary Cross Entropy
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        train_model(model, X_train_tensor, y_train_tensor, optimizer, criterion)

        # Evaluate the model
        model.eval()
        predictions = (model(X_test_tensor).detach().numpy() > 0.5).astype(int)
        accuracy = accuracy_score(y_test, predictions)
        print(f"Model accuracy: {accuracy:.4f}")

        # Compute feature importances
        if use_shap:
            feature_importances = compute_feature_importance_shap(model, X_train_tensor.numpy())
            print("Feature importances (SHAP):", feature_importances)
        else:
            feature_importances = compute_feature_importance_permutation(model, X_test_tensor, y_test_tensor)
            print("Feature importances (Permutation):", feature_importances)

        # Check for convergence
        if prev_importances is not None:
            delta_importances = np.abs(np.array(feature_importances) - np.array(prev_importances))
            if np.max(delta_importances) < convergence_threshold:
                print("Feature importances have stabilized. Stopping iterations.")
                break

        prev_importances = feature_importances

        # Select top features based on importance threshold
        importance_threshold = np.percentile(feature_importances, 75)  # Keep top 25% features
        top_features_indices = [i for i, imp in enumerate(feature_importances) if imp >= importance_threshold]
        top_features_names = column_names[top_features_indices]
        print(f"Selected top features: {list(top_features_names)}")

        # After top_features_indices is defined, filter prev_importances to match the selected features (match shape)
        if prev_importances is not None:
            prev_importances = [imp for i, imp in enumerate(prev_importances) if i in top_features_indices]

        # Update dataset to include only top features
        X_train = X_train[:, top_features_indices]
        X_test = X_test[:, top_features_indices]
        X_train_tensor = torch.tensor(X_train, dtype=torch.float32).view(X_train.shape[0], 1, -1)
        X_test_tensor = torch.tensor(X_test, dtype=torch.float32).view(X_test.shape[0], 1, -1)

        input_size = len(top_features_indices)
        iteration += 1

    print("Final selected features:", list(top_features_names))
    print(f"Final model accuracy: {accuracy:.4f}")

# Run the main function
if __name__ == "__main__":
    main()
