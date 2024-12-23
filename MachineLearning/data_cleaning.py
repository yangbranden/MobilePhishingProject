# Goal of this script is to take the raw data from our tests and convert it into a CSV file with valuable output
# Input:
#   - info.json
#   - session.json
#   - text_logs.txt
#   - network_logs.txt
#   - page_sources.json
#
# Output (fields of CSV file):
#   (from info.json):
#   - url (URL of website visited)
#   - phishing (whether the website is phishing or benign)
#   (from sesson.json):
#   - start_time (timestamp indicating time when first request in visit began)
#   - duration (in seconds)
#   - device
#   - os
#   - os_version
#   - browser
#   - browser_version
#   (from network_logs.txt):
#   - All request headers (bitmap of all values in the network requests associated with a website visit)
#   - All response headers (bitmap of all values in the network responses associated with a website visit)
#   (from page_sources.json):
#   - page_source (optional)

import os
import csv
import json
from datetime import datetime

parent_folder = '../output_data'
phishing_data_folders = [
    'gLwfQlpM_All_Targets',
    'JaaSewzb_All_Targets',
    'ANhNsXsI_All_Targets',
    '2dM2kv9h_All_Targets',
    'RjZmcQS9_All_Targets',
    'Y1CMnmb5_All_Targets',
    'PP5yNKGg_All_Targets',
    'lec5bU7X_All_Targets',
    'uFzxSpgX_All_Targets',
]
benign_data_folders = [
    'vkeuKXd9_All_Targets',
    'K9hlM3Rf_All_Targets',
    'VQYZtSiN_All_Targets',
    't5tZGTlL_All_Targets',
    'pdht4nq7_All_Targets',
    'EehjidOp_All_Targets',
    'dNdnnX9R_All_Targets',
    'TrDkscAZ_All_Targets',
]
data_folders = phishing_data_folders + benign_data_folders

# TODO
def get_unique_headers():
    return

# Logic to parse 'url' field
def get_url(info_json_path):
    try:
        with open(info_json_path, 'r') as f:
            build_data = json.load(f)
        url = build_data.get("urls", [])[0]
        return url
    except Exception as e:
        print(f"Error parsing info.json: {e}")
        return None

# Logic to parse 'phishing' field
def get_phishing(info_json_path):
    try:
        with open(info_json_path, 'r') as f:
            build_data = json.load(f)
        build_name = build_data.get("build_name", None)
        phishing_status = None
        if build_name in phishing_data_folders:
            phishing_status = True
        elif build_name in benign_data_folders:
            phishing_status = False
        return phishing_status
    except Exception as e:
        print(f"Error parsing info.json: {e}")
        return None

# Logic to parse the following fields:
# - start_time
# - duration
# - device
# - os
# - os_version
# - browser
# - browser_version
def parse_session_json(session_json_path):
    try:
        with open(session_json_path, 'r') as file:
            session_data = json.load(file)
        session_info = {
            "start_time": session_data.get("created_at"),
            "duration": session_data.get("duration"),
            "device": session_data.get("device_info", {}).get("device"),
            "os": session_data.get("device_info", {}).get("os"),
            "os_version": session_data.get("device_info", {}).get("os_version"),
            "browser": session_data.get("device_info", {}).get("browser"),
            "browser_version": session_data.get("device_info", {}).get("browser_version")
        }
        return session_info
    except Exception as e:
        print(f"Error parsing session.json: {e}")
        return None

def main():
    # Create output CSV file first
    with open('test.csv', mode='w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        
        # Write the header row
        header_row = [
            'url', 
            'phishing',
            'start_time', 
            'duration', 
            'device', 
            'os', 
            'os_version', 
            'browser', 
            'browser_version', 
        ]
        # TODO: Add all request headers and response headers here
        csv_writer.writerow(header_row)

        # Parse all data folders
        for data_folder in data_folders:
            curr_folder = os.path.join(parent_folder, data_folder) # build folders
            
            # We want to create an entry for session; loop through all sessions
            for session_folder in os.listdir(curr_folder):
                # Object to hold data for current entry of CSV row
                session_data = []
                
                # Session folder path
                session_folder_path = os.path.join(curr_folder, session_folder)
                
                # Ensure it is directory
                if not os.path.isdir(session_folder_path):
                    # print("ERROR: Not directory;", session_folder_path)
                    continue
                
                # Parse info.json from parent build folder (data_folder) 
                #   - url
                #   - phishing
                info_json_path = os.path.join(curr_folder, 'info.json')
                session_data.append(get_url(info_json_path))
                session_data.append(get_phishing(info_json_path))
                
                # Parse session.json
                #   - start_time
                #   - duration
                #   - device
                #   - os
                #   - os_version
                #   - browser
                #   - browser_version
                session_json_path = os.path.join(session_folder_path, 'session.json')
                parsed_session_json = parse_session_json(session_json_path)
                session_data.append(parsed_session_json['start_time'])
                session_data.append(parsed_session_json['duration'])
                session_data.append(parsed_session_json['device'])
                session_data.append(parsed_session_json['os'])
                session_data.append(parsed_session_json['os_version'])
                session_data.append(parsed_session_json['browser'])
                session_data.append(parsed_session_json['browser_version'])
                
                # Parse network_logs.txt
                #   - All request headers (bitmap of all values in the network requests associated with a website visit)
                #   - All response headers (bitmap of all values in the network responses associated with a website visit)
                
                # Parse page_sources.json
                #   - page_source (optional)
            
                # After all processsing, append data to CSV
                print("Adding data:", session_data)
                csv_writer.writerow(session_data)



if __name__ == "__main__":
    main()