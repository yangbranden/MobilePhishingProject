# Version for parsing CSV file

import csv
import datetime
import sys
import os
import yaml

# The most recent 'n' of URLs from phishtank.org
NUM_URLS = 10 if len(sys.argv) < 2 else int(sys.argv[1]) 
target_urls = []

# use our script to update phishtank sources
# os.system("sh PhishTankParser/fetch_phishtank.sh")

# if we already have a 'latest.yml' file containing our URLs, we want to read it and move it (change its name)
last_updated = None
if os.path.exists("./urls/latest.yml"):
    with open("./urls/latest.yml", "r") as f:
        urls_file = yaml.safe_load(f)
        last_updated = urls_file["last_updated"]
    if not os.path.exists("./urls/old"):
        os.mkdir("./urls/old")
    os.system(f"mv ./urls/latest.yml ./urls/old/urls_{last_updated}.yml")

with open('./urls/online-valid.csv', mode='r', encoding='latin-1', newline='') as file:
    csv_reader = csv.reader(file)
    
    # Skip header row
    header = next(csv_reader)

    for index, row in enumerate(csv_reader):
        if len(target_urls) >= NUM_URLS:
            break
        target_urls.append(row[1])
        # print(f"Added URL to urls: {row[1]}")

with open('./urls/latest.yml', "w") as f:
    last_updated = datetime.datetime.today().strftime("%Y_%m_%d_%H_%M_%S")
    data = {
        'last_updated': last_updated,
        'urls': target_urls
    }
    yaml.dump(data, f)