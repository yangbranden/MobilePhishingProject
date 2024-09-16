# Version for parsing CSV file

import csv

NUM_URLS = 10 # The most recent 'n' of URLs from phishtank.org
target_urls = ['https://example.com']

with open('./urls/online-valid.csv', mode='r', encoding='latin-1', newline='') as file:
    csv_reader = csv.reader(file)
    
    # Skip header row
    header = next(csv_reader)

    for index, row in enumerate(csv_reader):
        if index >= NUM_URLS:
            break
        target_urls.append(row[1])
        # print(f"Added URL to urls: {row[1]}")
        
for url in target_urls:
    print(url)