import pandas as pd

# Load the data
data = pd.read_csv("targeted_data_all_1_15_2025.csv", low_memory=False)

# Clean data
data = data[data['blocked'] != -1] # Remove blocks by 3rd party sources (we are only observing browser behavior)
data = data[data['blocked'] != -2] # Remove errors (entries where page source was unable to be processed properly)

# FILTER DATA FOR SPECIFIC URLs (these are our phishing URLs)
data = data[data['phishing'] == True] # filter for visits to phishing sites
# data = data[data['url'] == 'hxxps://sedduok.github.io/test/']
# data = data[data['url'] == 'hxxp://sameerschool.org/ionos/iindex.html']
# data = data[data['url'] == 'hxxp://fysmganhfa.duckdns.org/ja/main']
# data = data[data['url'] == 'hxxps://juquling.serv00.net/hypeSPAit24/hype/']
# data = data[data['url'] == 'hxxps://bkq.cdj.mybluehost.me/']
# data = data[data['url'] == 'hxxps://intlverifyngwebappsecurenewaccmanagespayments.jamulbryah.biz.id/signin']
# data = data[data['url'] == 'hxxps://squid-app-luerc.ondigitalocean.app/login']
# data = data[data['url'] == 'hxxps://swwsooledmansud.weebly.com/']
# data = data[data['url'] == 'hxxps://jentif.com/strato/login']
# data = data[data['url'] == 'hxxps://medexampass.com/routes/synwgxpl/envi-access/ss.html']

# Create new columns for device type and device model 
device_type_mapping = {
    # iPhone
    'iPhone 16 Pro Max': 'iPhone',
    'iPhone 16 Pro': 'iPhone',
    'iPhone 16 Plus': 'iPhone',
    'iPhone 16': 'iPhone',
    'iPhone 15 Pro Max': 'iPhone',
    'iPhone 15 Pro': 'iPhone',
    'iPhone 15 Plus': 'iPhone',
    'iPhone 15': 'iPhone',
    'iPhone 14 Pro Max': 'iPhone',
    'iPhone 14 Pro': 'iPhone',
    'iPhone 14 Plus': 'iPhone',
    'iPhone 14': 'iPhone',
    'iPhone 13 Pro Max': 'iPhone',
    'iPhone 13 Pro': 'iPhone',
    'iPhone 13 Mini': 'iPhone',
    'iPhone 13': 'iPhone',
    'iPhone 12 Pro Max': 'iPhone',
    'iPhone 12 Pro': 'iPhone',
    'iPhone 12 Mini': 'iPhone',
    'iPhone 12': 'iPhone',
    'iPhone 11': 'iPhone',
    'iPhone XS': 'iPhone',
    'iPhone XR': 'iPhone',
    'iPhone X': 'iPhone',
    'iPhone 8': 'iPhone',
    'iPhone 7': 'iPhone',
    'iPhone SE 2022': 'iPhone',
    'iPhone SE 2020': 'iPhone',
    # iPad
    'iPad Pro 13 2024': 'iPad',
    'iPad Pro 12.9 2022': 'iPad',
    'iPad Pro 12.9 2021': 'iPad',
    'iPad Pro 12.9 2020': 'iPad',
    'iPad Pro 12.9 2018': 'iPad',
    'iPad Pro 11 2024': 'iPad',
    'iPad Pro 11 2022': 'iPad',
    'iPad Pro 11 2021': 'iPad',
    'iPad Pro 11 2020': 'iPad',
    'iPad Air 6': 'iPad',
    'iPad Air 5': 'iPad',
    'iPad Air 4': 'iPad',
    'iPad Mini 2021': 'iPad',
    'iPad Mini 2019': 'iPad',
    'iPad 10th': 'iPad',
    'iPad 9th': 'iPad',
    'iPad 8th': 'iPad',
    'iPad 6th': 'iPad',
    # Samsung Galaxy
    'Samsung Galaxy S24 Ultra': 'Samsung Galaxy',
    'Samsung Galaxy S24': 'Samsung Galaxy',
    'Samsung Galaxy S23 Ultra': 'Samsung Galaxy',
    'Samsung Galaxy S23': 'Samsung Galaxy',
    'Samsung Galaxy S22 Ultra': 'Samsung Galaxy',
    'Samsung Galaxy S22 Plus': 'Samsung Galaxy',
    'Samsung Galaxy S22': 'Samsung Galaxy',
    'Samsung Galaxy S21 Ultra': 'Samsung Galaxy',
    'Samsung Galaxy S21 Plus': 'Samsung Galaxy',
    'Samsung Galaxy S21': 'Samsung Galaxy',
    'Samsung Galaxy S20 Ultra': 'Samsung Galaxy',
    'Samsung Galaxy S20 Plus': 'Samsung Galaxy',
    'Samsung Galaxy S20': 'Samsung Galaxy',
    'Samsung Galaxy S10 Plus': 'Samsung Galaxy',
    'Samsung Galaxy S10': 'Samsung Galaxy',
    'Samsung Galaxy S9': 'Samsung Galaxy',
    'Samsung Galaxy S8': 'Samsung Galaxy',
    'Samsung Galaxy A52': 'Samsung Galaxy',
    'Samsung Galaxy A51': 'Samsung Galaxy',
    'Samsung Galaxy A11': 'Samsung Galaxy',
    'Samsung Galaxy A10': 'Samsung Galaxy',
    'Samsung Galaxy M52': 'Samsung Galaxy',
    'Samsung Galaxy M32': 'Samsung Galaxy',
    # Samsung Galaxy Note
    'Samsung Galaxy Note 20 Ultra': 'Samsung Galaxy Note',
    'Samsung Galaxy Note 20': 'Samsung Galaxy Note',
    'Samsung Galaxy Note 9': 'Samsung Galaxy Note',
    # Samsung Galaxy Tab
    'Samsung Galaxy Tab S10 Plus': 'Samsung Galaxy Tab',
    'Samsung Galaxy Tab S9': 'Samsung Galaxy Tab',
    'Samsung Galaxy Tab S8': 'Samsung Galaxy Tab',
    'Samsung Galaxy Tab S7': 'Samsung Galaxy Tab',
    'Samsung Galaxy Tab S6': 'Samsung Galaxy Tab',
    'Samsung Galaxy Tab A9 Plus': 'Samsung Galaxy Tab',
    # Google Pixel
    'Google Pixel 9 Pro XL': 'Google Pixel',
    'Google Pixel 9 Pro': 'Google Pixel',
    'Google Pixel 9': 'Google Pixel',
    'Google Pixel 8 Pro': 'Google Pixel',
    'Google Pixel 8': 'Google Pixel',
    'Google Pixel 7 Pro': 'Google Pixel',
    'Google Pixel 7': 'Google Pixel',
    'Google Pixel 6 Pro': 'Google Pixel',
    'Google Pixel 6': 'Google Pixel',
    'Google Pixel 5': 'Google Pixel',
    'Google Pixel 4 XL': 'Google Pixel',
    'Google Pixel 4': 'Google Pixel',
    'Google Pixel 3': 'Google Pixel',
    # Motorola Moto
    'Motorola Moto G71 5G': 'Motorola Moto',
    'Motorola Moto G9 Play': 'Motorola Moto',
    'Motorola Moto G7 Play': 'Motorola Moto',
    # Vivo
    'Vivo Y21': 'Vivo',
    'Vivo V21': 'Vivo',
    'Vivo Y50': 'Vivo',
    # Xiaomi
    'Xiaomi Redmi Note 11': 'Xiaomi',
    'Xiaomi Redmi Note 9': 'Xiaomi',
    'Xiaomi Redmi Note 8': 'Xiaomi',
    # Oppo
    'Oppo Reno 6': 'Oppo',
    'Oppo Reno 3 Pro': 'Oppo',
    'Oppo A96': 'Oppo',
    # OnePlus
    'OnePlus 11R': 'OnePlus',
    'OnePlus 9': 'OnePlus',
    'OnePlus 8': 'OnePlus',
    'OnePlus 7T': 'OnePlus',
    'OnePlus 7': 'OnePlus',
    # Huawei
    'Huawei P30': 'Huawei'
}
data['device_type'] = data['device'].map(device_type_mapping)
data['device_type'] = data['device_type'].fillna('Other')
# Check rows where device_type is 'Other' and get unique device values
# other_devices = data[data['device_type'] == 'Other']['device'].unique()
# print("OTHER:", other_devices)



######## OVERALL STATISTICS ########
print("Basic data summary information:\n", data.describe(include='all'))
# Check for missing values
print("Checking null values:\n", data.isnull().sum())
# Distribution of values
print("\nDistribution by OS:\n",data['os'].value_counts())
print("\nDistribution by Device type:\n",data['device_type'].value_counts())
print("\nDistribution by Browser:\n",data['browser'].value_counts())
print()



######## OS STATISTICS ########
# OS only
# os_susceptibility = data.groupby('os')['blocked'].mean().sort_values(ascending=False)
# OS + OS version
os_susceptibility = data.groupby(['os', 'os_version'])['blocked'].mean().sort_values(ascending=False)
print("\nOS STATISTICS", os_susceptibility)



######## DEVICE STATISTICS ########
# Device only
# device_susceptibility = data.groupby('device')['blocked'].mean().sort_values(ascending=False)
# Device type only
# device_susceptibility = data.groupby('device_type')['blocked'].mean().sort_values(ascending=False)
# Device type + device
device_susceptibility = data.groupby(['device_type', 'device'])['blocked'].mean().sort_values(ascending=False)
print("\nDEVICE STATISTICS", device_susceptibility)



######## BROWSER STATISTICS ########
# Browser only
# browser_susceptibility = data.groupby('browser')['blocked'].mean().sort_values(ascending=False)
# Browser + browser version
browser_susceptibility = data.groupby(['browser', 'browser_version'])['blocked'].mean().sort_values(ascending=False)
print("\nBROWSER STATISTICS", browser_susceptibility)



# Output to CSV file for creating table visuals
# os_susceptibility.to_csv('./statistics/targeted_data/browser+browser_version.csv')
