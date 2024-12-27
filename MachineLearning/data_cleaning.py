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
    '702pzIp8_All_Targets',
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
    'aAFRZWmq_All_Targets',
]
data_folders = phishing_data_folders + benign_data_folders

# Get all unique request and response headers from all network_logs.txt files
def get_unique_headers(data_folders):
    request_headers = set()
    response_headers = set()
    for data_folder in data_folders:
        curr_folder = os.path.join(parent_folder, data_folder) # build folders
        for session_folder in os.listdir(curr_folder):
            session_folder_path = os.path.join(curr_folder, session_folder)
            if not os.path.isdir(session_folder_path):
                continue
            network_logs_path = os.path.join(session_folder_path, 'network_logs.txt')
            try:
                with open(network_logs_path, 'r', encoding='utf-8', errors='replace') as f:
                    log_data = json.load(f)  # Parse the JSON file
                    for entry in log_data.get('log', {}).get('entries', []):
                        # Extract request headers
                        for header in entry.get('request', {}).get('headers', []):
                            request_headers.add(header.get('name'))
                        # Extract response headers
                        for header in entry.get('response', {}).get('headers', []):
                            response_headers.add(header.get('name'))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                # print(f"Error reading {network_logs_path}: {e}")
                continue
    # return the combined set of headers
    return sorted(request_headers.union(response_headers))

# Get all unique header-value pairs from all network_log.txt files
def get_unique_header_values(data_folders):
    header_values = {}
    for data_folder in data_folders:
        curr_folder = os.path.join(parent_folder, data_folder)
        for session_folder in os.listdir(curr_folder):
            session_folder_path = os.path.join(curr_folder, session_folder)
            if not os.path.isdir(session_folder_path):
                continue
            network_logs_path = os.path.join(session_folder_path, 'network_logs.txt')
            try:
                with open(network_logs_path, 'r', encoding='utf-8', errors='replace') as f:
                    # print(f"Parsing {network_logs_path}...")
                    log_data = json.load(f)
                    for entry in log_data.get('log', {}).get('entries', []):
                        for header in entry.get('request', {}).get('headers', []):
                            name, value = header.get('name'), header.get('value')
                            if name not in header_values:
                                header_values[name] = set()
                            header_values[name].add(value)
                        for header in entry.get('response', {}).get('headers', []):
                            name, value = header.get('name'), header.get('value')
                            if name not in header_values:
                                header_values[name] = set()
                            header_values[name].add(value)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                continue
    return [(name, sorted(values)) for name, values in header_values.items()]

# Create a hot mappings for all header-value pairs from all network_logs.txt files
def create_hot_mappings(unique_header_values):
    hot_mappings = []
    for header, values in unique_header_values:
        for index, value in enumerate(values):
            # Create a binary vector for the current value
            mapping = [0] * len(values)
            mapping[index] = 1
            # Calculate numerical value of binary mapping
            mapping_value = int(''.join(map(str, mapping)), 2)
            # Append the header, value, and its binary mapping to the list
            hot_mappings.append((header, value, mapping, mapping_value))
    with open('hot_mappings.csv', mode='w', newline='') as csvfile_hm:
        csv_writer_hm = csv.writer(csvfile_hm)
        csv_writer_hm.writerow(['Header', 'Header Value', 'Mapping', 'Mapping Value'])  # Write header row
        for header, value, mapping, mapping_value in hot_mappings:
            csv_writer_hm.writerow([header, value, mapping, mapping_value])  # Write data rows
    return hot_mappings

# This is the function to actually check and record the header values
def get_header_values(log_file_path, hot_mappings, unique_headers):
    mapping_dict = {(header, value): mapping_value for header, value, _, mapping_value in hot_mappings}
    session_header_values = {header: 0 for header, _, _, _ in hot_mappings}
    try:
        with open(log_file_path, 'r', encoding='utf-8', errors='replace') as f:
            log_data = json.load(f)
            for entry in log_data.get('log', {}).get('entries', []):
                for header in entry.get('request', {}).get('headers', []):
                    name, value = header.get('name'), header.get('value')
                    if (name, value) in mapping_dict:
                        if name not in session_header_values:
                            session_header_values[name] = 0
                        session_header_values[name] |= mapping_dict[(name, value)]
                for header in entry.get('response', {}).get('headers', []):
                    name, value = header.get('name'), header.get('value')
                    if (name, value) in mapping_dict:
                        if name not in session_header_values:
                            session_header_values[name] = 0
                        session_header_values[name] |= mapping_dict[(name, value)]
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error reading {log_file_path}: {e}")
    oredered_values = [session_header_values[header] for header in unique_headers]
    return oredered_values

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
    print("DEBUG: getting unique header-value pairs...")
    unique_header_values = get_unique_header_values(data_folders)
    print("DEBUG: DONE.")
    print("DEBUG: creating hot mappings...")
    hot_mappings = create_hot_mappings(unique_header_values)
    print("DEBUG: DONE.")

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
        http_headers = get_unique_headers(data_folders)
        for header in http_headers:
            header_row.append(header)
        # header_row.append('page_source') # optional for now
        csv_writer.writerow(header_row)

        # Parse all data folders
        for data_folder in data_folders:
            curr_folder = os.path.join(parent_folder, data_folder) # build folders
            
            # We want to create an entry for session; loop through all sessions
            for session_folder in os.listdir(curr_folder):
                print(f"DEBUG: Parsing {curr_folder}/{session_folder}...")
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
                session_data.append(parsed_session_json['device'] if parsed_session_json['device'] is not None else "None")
                session_data.append(parsed_session_json['os'])
                session_data.append(parsed_session_json['os_version'])
                session_data.append(parsed_session_json['browser'])
                session_data.append(parsed_session_json['browser_version'])
                
                # Parse network_logs.txt
                #   - All request headers (bitmap of all values in the network requests associated with a website visit)
                #   - All response headers (bitmap of all values in the network responses associated with a website visit)
                network_logs_path = os.path.join(session_folder_path, 'network_logs.txt')
                header_values = get_header_values(network_logs_path, hot_mappings, http_headers)
                for header_value in header_values:
                    session_data.append(header_value)
                
                # Parse page_sources.json
                #   - page_source (optional)
            
                # After all processsing, append data to CSV
                # print("Adding data:", session_data)
                csv_writer.writerow(session_data)



if __name__ == "__main__":
    main()