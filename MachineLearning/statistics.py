import pandas as pd

# Load the data
data = pd.read_csv("data_all_1_14_2025.csv", low_memory=False)

# FILTER DATA FOR SPECIFIC URL
data = data[data['url'] == 'hxxp://sameerschool.org/ionos/iindex.html']

# Summary statistics
# print(data.describe(include='all'))

# Check for missing values
# print("Checking null values:\n", data.isnull().sum())

# Distribution of values
# print(data['os'].value_counts())

# Susceptibility rate for OS
os_susceptibility = data.groupby('os')['blocked'].mean().sort_values(ascending=False)
print("OS STATISTICS", os_susceptibility)

# Susceptibility rate for devices
device_susceptibility = data.groupby('device')['blocked'].mean().sort_values(ascending=False)
print("DEVICE STATISTICS", device_susceptibility)

# Susceptibility rate for browser
browser_susceptibility = data.groupby('browser')['blocked'].mean().sort_values(ascending=False)
print("BROWSER STATISTICS", browser_susceptibility)
