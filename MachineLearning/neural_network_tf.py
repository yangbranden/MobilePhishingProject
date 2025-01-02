# Attempting to try and use TensorFlow Keras in case it's easier

import pandas as pd
import numpy as np
import shap
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder

def create_lstm_model(input_size):
    model = Sequential([
        LSTM(64, input_shape=(1, input_size), return_sequences=False),
        Dense(32, activation='relu'),
        Dropout(0.2),
        Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model

# Train the model
def train_model(model, X_train, y_train, epochs=20, batch_size=32):
    model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=1)

# Evaluate feature importance using Permutation Feature Importance
def compute_feature_importance_permutation(model, X_test, y_test):
    """
    Method 1: Permutation Feature Importance
    """
    baseline_accuracy = accuracy_score(
        y_test,
        (model.predict(X_test) > 0.5).astype(int)
    )
    importances = []
    for i in range(X_test.shape[2]):
        X_test_permuted = X_test.copy()
        np.random.shuffle(X_test_permuted[:, :, i])
        permuted_accuracy = accuracy_score(
            y_test,
            (model.predict(X_test_permuted) > 0.5).astype(int)
        )
        importances.append(baseline_accuracy - permuted_accuracy)
    return importances

# Evaluate feature importance using SHAP
def compute_feature_importance_shap(model, X_sample):
    """
    Method 2: Shapley values (SHAP)
    """
    # Reshape X_sample to 2D for SHAP compatibility
    X_sample_flat = X_sample.reshape(X_sample.shape[0], -1)

    # Define the SHAP explainer
    explainer = shap.KernelExplainer(lambda x: model.predict(x.reshape(x.shape[0], 1, -1)), X_sample_flat)

    # Compute SHAP values
    shap_values = explainer.shap_values(X_sample_flat, nsamples=100)
    aggregated_shap_values = np.mean(np.abs(shap_values), axis=0)
    return aggregated_shap_values

# Main function
def main():
    # Load and process data
    data = pd.read_csv('data_all_1_1_2025.csv', low_memory=False)

    # Leave out certain columns we are only keeping in for debugging/looking at the data manually
    data = data.drop(columns=['url', 'public_url', 'reasoning', 'phishing'], errors='ignore')

    # Convert all non-numeric columns into numeric values
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

    # Reshape for RNN input (sequence length = 1)
    X_train = X_train.reshape(X_train.shape[0], 1, -1)
    X_test = X_test.reshape(X_test.shape[0], 1, -1)

    # Model definition
    input_size = X_train.shape[2]

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
        model = create_lstm_model(input_size)
        train_model(model, X_train, y_train, epochs=20, batch_size=32)

        # Evaluate the model
        predictions = (model.predict(X_test) > 0.5).astype(int)
        accuracy = accuracy_score(y_test, predictions)
        print(f"Model accuracy: {accuracy:.4f}")

        # Compute feature importances
        if use_shap:
            feature_importances = compute_feature_importance_shap(model, X_train)
            print("Feature importances (SHAP):", feature_importances)
        else:
            feature_importances = compute_feature_importance_permutation(model, X_test, y_test)
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
        X_train = X_train[:, :, top_features_indices]
        X_test = X_test[:, :, top_features_indices]

        input_size = len(top_features_indices)
        iteration += 1

    print("Final selected features:", list(top_features_names))
    print(f"Final model accuracy: {accuracy:.4f}")

# Run the main function
if __name__ == "__main__":
    main()
