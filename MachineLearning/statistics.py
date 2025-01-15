import pandas as pd

# Load the data
data = pd.read_csv("data_all_1_14_2025.csv", low_memory=False)

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

# Summary statistics
# print(data.describe(include='all'))

# Check for missing values
# print("Checking null values:\n", data.isnull().sum())

# Distribution of values
# print(data['os'].value_counts())

# Susceptibility rate for OS
os_susceptibility = data.groupby('os')['blocked'].mean().sort_values(ascending=False)
print("OS STATISTICS", os_susceptibility)

# Susceptibility rate for devices (TODO: we are grouping by individual device; I want to group by vendor (maybe we need to add another field for this))
device_susceptibility = data.groupby('device')['blocked'].mean().sort_values(ascending=False)
print("DEVICE STATISTICS", device_susceptibility)

# Susceptibility rate for browser
browser_susceptibility = data.groupby('browser')['blocked'].mean().sort_values(ascending=False)
print("BROWSER STATISTICS", browser_susceptibility)
