'''
https://www.phishtank.com/developer_info.php

json format

[{"ip_address":"199.36.158.100","cidr_block":"199.36.158.0\/24","announcing_network":"54113","rir":"arin","country":"US","detail_time":"2023-04-23T03:26:22+00:00"}],"target":"Other"},{"phish_id":8125349,"url":"https:\/\/tunahrtjanzak2.web.app\/","phish_detail_url":"http:\/\/www.phishtank.com\/phish_detail.php?phish_id=8125349","submission_time":"2023-04-23T03:23:46+00:00","verified":"yes","verification_time":"2023-04-23T03:26:44+00:00","online":"yes","details":[{"ip_address":"199.36.158.100","cidr_block":"199.36.158.0\/24","announcing_network":"54113","rir":"arin","country":"US","detail_time":"2023-04-23T03:26:22+00:00"}],"target":"Other"},{"phish_id":8125348,"url":"https:\/\/tunahrtjanzak2.firebaseapp.com\/","phish_detail_url":"http:\/\/www.phishtank.com\/phish_detail.php?phish_id=8125348","submission_time":"2023-04-23T03:23:40+00:00","verified":"yes","verification_time":"2023-04-23T03:26:44+00:00","online":"yes","details":[{"ip_address":"199.36.158.100","cidr_block":"199.36.158.0\/24","announcing_network":"54113","rir":"arin","country":"US","detail_time":"2023-04-23T03:26:22+00:00"}],"target":"Other"},{"phish_id":8125347,"url":"https:\/\/tunahrtjanzak3.web.app\/","phish_detail_url":"http:\/\/www.phishtank.com\/phish_detail.php?phish_id=8125347","submission_time":"2023-04-23T03:23:35+00:00","verified":"yes","verification_time":"2023-04-23T03:26:44+00:00","online":"yes","details":[{"ip_address":"199.36.158.100","cidr_block":"199.36.158.0\/24","announcing_network":"54113","rir":"arin","country":"US","detail_time":"2023-04-23T03:26:22+00:00"}],"target":"Other"},
'''

# read verified_online.json and iterate through the json, filter out only ip_address, url, counntry, verification_time, and phish_detail_url
# make this to new lists
# print the lists

import json

# Load the JSON data from the file
with open('verified_online.json') as f:
    data = json.load(f)

# Create a single list to store all the combined information
phish_entries = []

# Iterate through the JSON data and extract relevant fields
for entry in data:
    if entry.get('verified') == 'yes' and entry.get('online') == 'yes':
        details = entry.get('details', [])
        if details:
            ip_address = details[0].get('ip_address', 'N/A')
            country = details[0].get('country', 'N/A')
        else:
            ip_address = 'N/A'
            country = 'N/A'

        url = entry.get('url', 'N/A')
        verification_time = entry.get('verification_time', 'N/A')
        phish_detail_url = entry.get('phish_detail_url', 'N/A')

        # Combine all relevant fields into a single entry
        phish_entries.append([ip_address, url, country, verification_time, phish_detail_url])



# Print the combined 30 lists line by line for the test purpose
for i in range(0, 30):
    print(phish_entries[i])
    print()
