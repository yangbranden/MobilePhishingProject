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
import sys
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

# Create hot mappings for headers present in the HTTP requests/responses
def create_header_hot_mappings(data_folders):
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
    all_headers = sorted(request_headers.union(response_headers))
    request_headers = sorted(request_headers)
    response_headers = sorted(response_headers)
    # Create mappings to return
    all_headers_mapping = []
    request_headers_mapping = []
    response_headers_mapping = []
    # All headers
    if os.path.isfile('all_header_presence_mappings.csv'):
        try:
            with open('all_header_presence_mappings.csv', mode='r', newline='') as csvfile_hm:
                csv_reader_hm = csv.reader(csvfile_hm)
                next(csv_reader_hm) # Skip header row
                all_headers_mapping = [tuple(row) for row in csv_reader_hm]
        except FileNotFoundError:
            print(f"'all_header_presence_mappings.csv' does not exist.")
    else:
        with open('all_header_presence_mappings.csv', mode='w', newline='') as csvfile_hm:
            csv_writer_hm = csv.writer(csvfile_hm)
            csv_writer_hm.writerow(['Header', 'Mapping', 'Mapping Value'])  # Write header row
            for index, header in enumerate(all_headers):
                mapping = [0] * len(all_headers)
                mapping[index] = 1
                mapping_value = int(''.join(map(str, mapping)), 2)
                all_headers_mapping.append((header, mapping, mapping_value))
                csv_writer_hm.writerow([header, mapping, mapping_value])
    # Request headers
    if os.path.isfile('request_header_presence_mappings.csv'):
        try:
            with open('request_header_presence_mappings.csv', mode='r', newline='') as csvfile_hm:
                csv_reader_hm = csv.reader(csvfile_hm)
                next(csv_reader_hm) # Skip header row
                all_headers_mapping = [tuple(row) for row in csv_reader_hm]
        except FileNotFoundError:
            print(f"'request_header_presence_mappings.csv' does not exist.")
    else:
        with open('request_header_presence_mappings.csv', mode='w', newline='') as csvfile_hm:
            csv_writer_hm = csv.writer(csvfile_hm)
            csv_writer_hm.writerow(['Header', 'Mapping', 'Mapping Value'])  # Write header row
            for index, header in enumerate(request_headers):
                mapping = [0] * len(request_headers)
                mapping[index] = 1
                mapping_value = int(''.join(map(str, mapping)), 2)
                request_headers_mapping.append((header, mapping, mapping_value))
                csv_writer_hm.writerow([header, mapping, mapping_value])
    # Response headers
    if os.path.isfile('response_header_presence_mappings.csv'):
        try:
            with open('response_header_presence_mappings.csv', mode='r', newline='') as csvfile_hm:
                csv_reader_hm = csv.reader(csvfile_hm)
                next(csv_reader_hm) # Skip header row
                all_headers_mapping = [tuple(row) for row in csv_reader_hm]
        except FileNotFoundError:
            print(f"'response_header_presence_mappings.csv' does not exist.")
    else:
        with open('response_header_presence_mappings.csv', mode='w', newline='') as csvfile_hm:
            csv_writer_hm = csv.writer(csvfile_hm)
            csv_writer_hm.writerow(['Header', 'Mapping', 'Mapping Value'])  # Write header row
            for index, header in enumerate(response_headers):
                mapping = [0] * len(response_headers)
                mapping[index] = 1
                mapping_value = int(''.join(map(str, mapping)), 2)
                response_headers_mapping.append((header, mapping, mapping_value))
                csv_writer_hm.writerow([header, mapping, mapping_value])
    return [all_headers_mapping, request_headers_mapping, response_headers_mapping]

# Get relevant unique header-value pairs from network_log.txt files
# threshold starts at 0.5, or 50%; if >50% of values are unique for a header, ignore it
def get_unique_header_data(data_folders, threshold=0.5):
    header_data = {}
    for data_folder in data_folders:
        curr_folder = os.path.join(parent_folder, data_folder)
        for session_folder in os.listdir(curr_folder):
            session_folder_path = os.path.join(curr_folder, session_folder)
            if not os.path.isdir(session_folder_path):
                continue
            network_logs_path = os.path.join(session_folder_path, 'network_logs.txt')
            try:
                with open(network_logs_path, 'r', encoding='utf-8', errors='replace') as f:
                    print(f"Parsing {network_logs_path}...")
                    log_data = json.load(f)
                    for entry in log_data.get('log', {}).get('entries', []):
                        for header in entry.get('request', {}).get('headers', []):
                            name, value = header.get('name'), header.get('value')
                            if name not in header_data:
                                header_data[name] = list()
                            header_data[name].append(value)
                        for header in entry.get('response', {}).get('headers', []):
                            name, value = header.get('name'), header.get('value')
                            if name not in header_data:
                                header_data[name] = list()
                            header_data[name].append(value)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                continue
    # Filter out headers using threshold value (we want headers that have repeated values 
    # because that means they have potential significance in determining phishing vs. non-phishing)
    filtered_header_data = {}
    for name, values in header_data.items():
        unique_values = set(values)
        # Filter based on threshold; i.e. if 50% of values are unique, header likely has no relevance in determining phishing
        # In cases where the header only appears once, we don't care about it anyways (not significant in determining phishing)
        if len(unique_values) > int(len(values) * (1 - threshold)):
            continue
        filtered_header_data[name] = unique_values
    # However, this does not take into consideration the actual presence of the headers themselves;
    # we will additionally track for this by creating a hot mapping for the presence of headers themselves (see below)
    return [(name, sorted(values)) for name, values in filtered_header_data.items()]

# Create a hot mappings for relevant header-value pairs from all network_logs.txt files
def create_header_data_hot_mappings(unique_header_data, load_file):
    hot_mappings = []
    # First check if hot mappings exist; if it does then no need to re-create (can take a VERY long time)
    if os.path.isfile(load_file):
        try:
            with open(load_file, mode='r', newline='') as csvfile_hm:
                csv_reader_hm = csv.reader(csvfile_hm)
                next(csv_reader_hm) # Skip header row
                hot_mappings = [tuple(row) for row in csv_reader_hm]
        except FileNotFoundError:
            print(f"'{load_file}' does not exist.")
    else:
        with open(load_file, mode='w', newline='') as csvfile_hm:
            csv_writer_hm = csv.writer(csvfile_hm)
            csv_writer_hm.writerow(['Header', 'Header Value', 'Mapping', 'Mapping Value'])  # Write header row
            idx = 0 # DEBUG
            for header, values in unique_header_data:
                for index, value in enumerate(values):
                    print(f"DEBUG: Creating hot mapping for header {header} (Progress: {idx}/{len(unique_header_data)}, {index}/{len(values)})")
                    # Create a binary vector for the current value
                    mapping = [0] * len(values)
                    mapping[index] = 1
                    # Calculate numerical value of binary mapping
                    mapping_value = int(''.join(map(str, mapping)), 2)
                    # Append the header, value, and its binary mapping to the list
                    hot_mappings.append((header, value, mapping, mapping_value))
                    csv_writer_hm.writerow([header, value, mapping, mapping_value])  # Write data rows
                idx += 1 # DEBUG
    return hot_mappings

# Logic to record what header-value pairs are present for a given log (session)
def get_header_data(log_file_path, hot_mappings, unique_headers):
    # Mapping dict contains the hot mappings for all header-value pairs
    mapping_dict = {(header, value): mapping_value for header, value, _, mapping_value in hot_mappings}
    # Variable to keep track of what header-value pairs have been seen in this log
    session_header_data = {header: 0 for header, _, _, _ in hot_mappings}
    try:
        with open(log_file_path, 'r', encoding='utf-8', errors='replace') as f:
            log_data = json.load(f)
            for entry in log_data.get('log', {}).get('entries', []):
                for header in entry.get('request', {}).get('headers', []):
                    name, value = header.get('name'), header.get('value')
                    if (name, value) in mapping_dict:
                        if name not in session_header_data:
                            session_header_data[name] = 0
                        session_header_data[name] |= mapping_dict[(name, value)]
                for header in entry.get('response', {}).get('headers', []):
                    name, value = header.get('name'), header.get('value')
                    if (name, value) in mapping_dict:
                        if name not in session_header_data:
                            session_header_data[name] = 0
                        session_header_data[name] |= mapping_dict[(name, value)]
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error reading {log_file_path}: {e}")
    oredered_data = [session_header_data[header] for header in unique_headers] # Return ordered (so format matches with CSV)
    return oredered_data

# Logic to record what headers are present for a given log (session)
def get_present_headers(log_file_path, hot_mappings):
    # Mapping dicts contain the hot mappings for all headers
    all_headers_mapping, request_headers_mapping, response_headers_mapping = hot_mappings
    all_headers_mapping_dict = {header: mapping_value for header, _, mapping_value in all_headers_mapping}
    request_headers_mapping_dict = {header: mapping_value for header, _, mapping_value in request_headers_mapping}
    response_headers_mapping_dict = {header: mapping_value for header, _, mapping_value in response_headers_mapping}
    # Variables to keep track of what headers have been seen in this log
    all_headers_present = 0
    request_headers_present = 0
    response_headers_present = 0
    try:
        with open(log_file_path, 'r', encoding='utf-8', errors='replace') as f:
            log_data = json.load(f)
            for entry in log_data.get('log', {}).get('entries', []):
                for header in entry.get('request', {}).get('headers', []):
                    name = header.get('name')
                    if name in all_headers_mapping:
                        all_headers_present |= all_headers_mapping_dict[name]
                    if name in request_headers_mapping:
                        request_headers_present |= request_headers_mapping_dict[name]
                for header in entry.get('response', {}).get('headers', []):
                    name = header.get('name')
                    if name in all_headers_mapping:
                        all_headers_present |= all_headers_mapping_dict[name]
                    if name in response_headers_mapping:
                        response_headers_present |= response_headers_mapping_dict[name]
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error reading {log_file_path}: {e}")
    return all_headers_present, request_headers_present, response_headers_present

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
    sys.set_int_max_str_digits(0) # Allow for larger integer conversion
    
    print("DEBUG: getting unique header-value pairs...")
    unique_header_data = get_unique_header_data(data_folders, threshold=0.9)
    print("DEBUG: DONE.")
    print("DEBUG: creating hot mappings...")
    header_data_mappings = create_header_data_hot_mappings(unique_header_data, '90percent_header_data_mappings.csv')
    print("DEBUG: DONE.")
    print("DEBUG: creating header hot mappings...")
    header_mappings = create_header_hot_mappings(data_folders)
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
            'all_headers',
            'request_headers',
            'response_headers',
        ]
        http_headers = [header_name for header_name, _ in unique_header_data]
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
                all_headers, request_headers, response_headers = get_present_headers(network_logs_path, header_mappings)
                session_data.append(all_headers)
                session_data.append(request_headers)
                session_data.append(response_headers)
                header_data = get_header_data(network_logs_path, header_data_mappings, http_headers)
                for header_value in header_data:
                    session_data.append(header_value)
                
                # Parse page_sources.json
                #   - page_source (optional)
            
                # After all processsing, append data to CSV
                # print("Adding data:", session_data)
                csv_writer.writerow(session_data)



if __name__ == "__main__":
    main()