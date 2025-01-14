import pandas as pd

# Load the data
data = pd.read_csv("data_all_1_1_2025.csv", low_memory=False)

# Summary statistics
print(data.describe(include='all'))

# Check for missing values
print("ANYTHING HERE?", data.isnull().sum())

# Distribution of values
print(data['os'].value_counts())
