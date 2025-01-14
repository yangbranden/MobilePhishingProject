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
#   - result

import os
import csv
import json
import sys
import subprocess
import yaml
from datetime import datetime

# SETTINGS (these are mostly for debugging but we can also tailor the output CSV)
OUTPUT_FILE = 'data_all_1_14_2024.csv'
DEBUG = True # Show debug prints
INCLUDE_BLOCKED_RESULT = True # Determine whether or not page was blocked
INCLUDE_HEADER_PRESENCE = True # Hot mappings for headers present in request/response/all network logs
INCLUDE_HEADER_VALUES = True # Hot mappings for header-value pairs 

# Specify data location here:
parent_folder = '../output_data'
phishing_data_folders = [
    # 'gLwfQlpM_All_Targets',
    'JaaSewzb_All_Targets',
    'ANhNsXsI_All_Targets',
    '2dM2kv9h_All_Targets',
    'RjZmcQS9_All_Targets',
    'Y1CMnmb5_All_Targets',
    'PP5yNKGg_All_Targets',
    'lec5bU7X_All_Targets',
    'uFzxSpgX_All_Targets',
    '702pzIp8_All_Targets',
    'htwojJit_All_Targets',
]
benign_data_folders = [
    # 'vkeuKXd9_All_Targets',
    'K9hlM3Rf_All_Targets',
    'VQYZtSiN_All_Targets',
    't5tZGTlL_All_Targets',
    'pdht4nq7_All_Targets',
    'EehjidOp_All_Targets',
    'dNdnnX9R_All_Targets',
    'TrDkscAZ_All_Targets',
    'aAFRZWmq_All_Targets',
    '4n6VBfUx_All_Targets',
]
data_folders = phishing_data_folders + benign_data_folders

browser_block_messages = {
    "Microsoft Edge (1)": 'This site has been reported as unsafe',
    "Microsoft Edge (2)": "Microsoft recommends you don\'t continue to this site.",
    "Mozilla Firefox (1)": 'Firefox blocked this page because it may trick you into doing something dangerous like installing software or revealing personal information like passwords or credit cards.', # Deceptive site ahead
    "Mozilla Firefox (2)": 'The page you are trying to view cannot be shown because the authenticity of the received data could not be verified.', # Secure Connection Failed
    "Mozilla Firefox (3)": 'Deceptive site issue', # Android Firefox
    "Google Chrome (1)": 'Attackers might be trying to steal your information from', # Your connection is not private
    "Google Chrome (2)": 'Deceptive site ahead',
    "Google Chrome (3)": 'Attackers on the site you',
    "Google Chrome (4)": 'Dangerous site',
    "Safari (1)": "to steal your personal or financial information.", # This Connection Is Not Private
    "Safari (2)": "Deceptive Website Warning",
    "Samsung Browser": "Attackers might be trying to steal your information from" # Your connection is not private
}

not_found_messages = {
    "Generic Not Found (1)": "Page not found",
    "Generic Not Found (2)": "Not Found</pre></body></html>",
    "Generic Not Found (3)": "The page you are looking for doesn't exist or has been moved.",
    "Wix Not Found (1)": "We Looked Everywhere<br>For This Page!",
    "Wix Not Found (2)": "angular.module('wixErrorPagesApp').constant('errorCode', {code: '404'});",
    "Cisco Umbrella Blocked": "This site is blocked due to a phishing threat.",
    "502 Bad Gateway": "502 Bad Gateway",
    "BrowserStack Unable to Display": "Unable to display the page",
    "Cloudflare SSL Handshake (1)": "SSL handshake failed",
    "Cloudflare SSL Handshake (2)": "Visit <a href=\"https://www.cloudflare.com/5xx-error-landing?utm_source=errorcode_525",
}

# Create hot mappings for headers present in the HTTP requests/responses
def create_header_hot_mappings(data_folders):
    if DEBUG:
        print("DEBUG: Creating hot mappings for headers present...")
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
                    log_data = json.load(f, strict=False)  # Parse the JSON file
                    for entry in log_data.get('log', {}).get('entries', []):
                        # Extract request headers
                        for header in entry.get('request', {}).get('headers', []):
                            request_headers.add(header.get('name'))
                        # Extract response headers
                        for header in entry.get('response', {}).get('headers', []):
                            response_headers.add(header.get('name'))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                if DEBUG:
                    print(f"DEBUG: Error reading {network_logs_path}: {e}")
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
    all_header_mapping_file = 'all_header_presence_mappings.csv'
    if DEBUG:
        print("DEBUG: Creating hot mappings for all headers...")
    if os.path.isfile(all_header_mapping_file):
        try:
            if DEBUG:
                print("Existing mappings found, importing...")
            with open(all_header_mapping_file, mode='r', newline='') as csvfile_hm:
                csv_reader_hm = csv.reader(csvfile_hm)
                next(csv_reader_hm) # Skip header row
                all_headers_mapping = [tuple(row) for row in csv_reader_hm]
        except FileNotFoundError:
            print(f"ERROR: '{all_header_mapping_file}' does not exist.")
    else:
        with open(all_header_mapping_file, mode='w', newline='') as csvfile_hm:
            csv_writer_hm = csv.writer(csvfile_hm)
            csv_writer_hm.writerow(['Header', 'Mapping', 'Mapping Value'])  # Write header row
            for index, header in enumerate(all_headers):
                if DEBUG:
                    print(f"DEBUG: Creating hot mapping for header {header} (Progress: {index}/{len(all_headers)})")
                mapping = [0] * len(all_headers)
                mapping[index] = 1
                mapping_value = int(''.join(map(str, mapping)), 2)
                all_headers_mapping.append((header, mapping, mapping_value))
                csv_writer_hm.writerow([header, mapping, mapping_value])
    # Request headers
    request_headers_mapping_file = 'request_header_presence_mappings.csv'
    if DEBUG:
        print("DEBUG: Creating hot mappings for request headers...")
    if os.path.isfile(request_headers_mapping_file):
        try:
            if DEBUG:
                print("Existing mappings found, importing...")
            with open(request_headers_mapping_file, mode='r', newline='') as csvfile_hm:
                csv_reader_hm = csv.reader(csvfile_hm)
                next(csv_reader_hm) # Skip header row
                request_headers_mapping = [tuple(row) for row in csv_reader_hm]
        except FileNotFoundError:
            print(f"ERROR: '{request_headers_mapping_file}' does not exist.")
    else:
        with open(request_headers_mapping_file, mode='w', newline='') as csvfile_hm:
            csv_writer_hm = csv.writer(csvfile_hm)
            csv_writer_hm.writerow(['Header', 'Mapping', 'Mapping Value'])  # Write header row
            for index, header in enumerate(request_headers):
                if DEBUG:
                    print(f"DEBUG: Creating hot mapping for header {header} (Progress: {index}/{len(request_headers)})")
                mapping = [0] * len(request_headers)
                mapping[index] = 1
                mapping_value = int(''.join(map(str, mapping)), 2)
                request_headers_mapping.append((header, mapping, mapping_value))
                csv_writer_hm.writerow([header, mapping, mapping_value])
    # Response headers
    response_headers_mapping_file = 'response_header_presence_mappings.csv'
    if DEBUG:
        print("DEBUG: Creating hot mappings for response headers...")
    if os.path.isfile(response_headers_mapping_file):
        try:
            if DEBUG:
                print("Existing mappings found, importing...")
            with open(response_headers_mapping_file, mode='r', newline='') as csvfile_hm:
                csv_reader_hm = csv.reader(csvfile_hm)
                next(csv_reader_hm) # Skip header row
                response_headers_mapping = [tuple(row) for row in csv_reader_hm]
        except FileNotFoundError:
            print(f"ERROR: '{response_headers_mapping_file}' does not exist.")
    else:
        with open(response_headers_mapping_file, mode='w', newline='') as csvfile_hm:
            csv_writer_hm = csv.writer(csvfile_hm)
            csv_writer_hm.writerow(['Header', 'Mapping', 'Mapping Value'])  # Write header row
            for index, header in enumerate(response_headers):
                if DEBUG:
                    print(f"DEBUG: Creating hot mapping for header {header} (Progress: {index}/{len(response_headers)})")
                mapping = [0] * len(response_headers)
                mapping[index] = 1
                mapping_value = int(''.join(map(str, mapping)), 2)
                response_headers_mapping.append((header, mapping, mapping_value))
                csv_writer_hm.writerow([header, mapping, mapping_value])
    if DEBUG:
        print("DEBUG: Done creating header hot mappings.")
    return [all_headers_mapping, request_headers_mapping, response_headers_mapping]

# Filter for relevant unique header-value pairs from network_log.txt files
# threshold starts at 0.5, or 50%; if >50% of values are unique for a header, ignore it
def filter_header_data(data_folders, threshold=0.5):
    if DEBUG:
        print("DEBUG: getting unique header-value pairs...")
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
                    if DEBUG:
                        print(f"(filter_header_data) Parsing '{network_logs_path}'...")
                    log_data = json.load(f, strict=False)
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
    if DEBUG:
        print(f"DEBUG: Filtering header data based on threshold of {threshold} (ignore headers where {threshold * 100}% of values are unique)...")
    filtered_header_data = {}
    for name, values in header_data.items():
        unique_values = set(values)
        # Filter based on threshold; i.e. if 50% of values are unique, header likely has no relevance in determining phishing
        # In cases where the header only appears once, we don't care about it anyways (not significant in determining phishing)
        if len(unique_values) > int(len(values) * round(1 - threshold, 1)): # maximum num of unique values allowed is 50% of total num of values 
            continue
        filtered_header_data[name] = unique_values
    # However, this does not take into consideration the actual presence of the headers themselves;
    # we will additionally track for this by creating a hot mapping for the presence of headers themselves (see below)
    if DEBUG:
        print("DEBUG: Done filtering header data.")
    return [(name, sorted(values)) for name, values in filtered_header_data.items()]

# Create a hot mappings for relevant header-value pairs from all network_logs.txt files
def create_header_data_hot_mappings(unique_header_data, load_file):
    if DEBUG:
        print("DEBUG: Creating hot mappings for header data (header-value pairs)...")
    hot_mappings = []
    # First check if hot mappings exist; if it does then no need to re-create (can take a VERY long time)
    if os.path.isfile(load_file):
        try:
            if DEBUG:
                print("Existing mappings found, importing...")
            with open(load_file, mode='r', newline='') as csvfile_hm:
                csv_reader_hm = csv.reader(csvfile_hm)
                next(csv_reader_hm) # Skip header row
                hot_mappings = [tuple(row) for row in csv_reader_hm]
        except FileNotFoundError:
            print(f"ERROR: '{load_file}' does not exist.")
    else:
        with open(load_file, mode='w', newline='') as csvfile_hm:
            csv_writer_hm = csv.writer(csvfile_hm)
            csv_writer_hm.writerow(['Header', 'Header Value', 'Mapping', 'Mapping Value'])  # Write header row
            idx = 0 # DEBUG
            for header, values in unique_header_data:
                for index, value in enumerate(values):
                    if DEBUG:
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
    if DEBUG:
        print("DEBUG: Done creating header data hot mappings.")
    return hot_mappings

# Logic to record what header-value pairs are present for a given log (session)
def get_header_data(log_file_path, hot_mappings, unique_headers):
    if DEBUG:
        print(f"DEBUG: Processing header data (header-value pairs) for {log_file_path}...")
    # Mapping dict contains the hot mappings for all header-value pairs
    mapping_dict = {(header, value): int(mapping_value) for header, value, _, mapping_value in hot_mappings}
    # Variable to keep track of what header-value pairs have been seen in this log
    session_header_data = {header: 0 for header, _, _, _ in hot_mappings}
    try:
        with open(log_file_path, 'r', encoding='utf-8', errors='replace') as f:
            log_data = json.load(f, strict=False)
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
    all_headers_mapping_dict = {header: int(mapping_value) for header, _, mapping_value in all_headers_mapping}
    request_headers_mapping_dict = {header: int(mapping_value) for header, _, mapping_value in request_headers_mapping}
    response_headers_mapping_dict = {header: int(mapping_value) for header, _, mapping_value in response_headers_mapping}
    # Variables to keep track of what headers have been seen in this log
    all_headers_present = 0
    request_headers_present = 0
    response_headers_present = 0
    try:
        with open(log_file_path, 'r', encoding='utf-8', errors='replace') as f:
            log_data = json.load(f, strict=False)
            for entry in log_data.get('log', {}).get('entries', []):
                for header in entry.get('request', {}).get('headers', []):
                    name = header.get('name')
                    if name in all_headers_mapping_dict:
                        all_headers_present |= all_headers_mapping_dict[name]
                    if name in request_headers_mapping_dict:
                        request_headers_present |= request_headers_mapping_dict[name]
                for header in entry.get('response', {}).get('headers', []):
                    name = header.get('name')
                    if name in all_headers_mapping_dict:
                        all_headers_present |= all_headers_mapping_dict[name]
                    if name in response_headers_mapping_dict:
                        response_headers_present |= response_headers_mapping_dict[name]
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error reading {log_file_path}: {e}")
    return [all_headers_present, request_headers_present, response_headers_present]

# Logic to parse 'url' field
def get_url(info_json_path):
    try:
        with open(info_json_path, 'r') as f:
            build_data = json.load(f, strict=False)
        url = build_data.get("urls", [])[0]
        return url
    except Exception as e:
        print(f"Error parsing info.json: {e}")
        return None

# Logic to parse 'phishing' field
def get_phishing(info_json_path):
    try:
        with open(info_json_path, 'r') as f:
            build_data = json.load(f, strict=False)
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
            session_data = json.load(file, strict=False)
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

# Logic to parse BrowserStack session public URL from page_sources.json
def get_public_url(session_json_path):
    try:
        with open(session_json_path, 'r') as file:
            session_data = json.load(file, strict=False)
        public_url = session_data.get("public_url")
        if '?auth_token=' in public_url: # auth_token expires so I will just remove (sorry, I know you guys can't see the browserstack URL)
            public_url = public_url.split('?auth_token=')[0]
        return public_url
    except Exception as e:
        print(f"Error parsing session.json: {e}")
        return None

# Logic to parse result from page_sources.json
def get_result(page_sources_path):
    with open(page_sources_path, 'r') as file:
        data = json.load(file, strict=False)
    page_sources = [entry['text'] for entry in data]
    if len(page_sources) != 1:
        print("ERROR: Incorrect number of page sources; there should only be one for this data collection")
        return -2, "ERROR"
    page_source = page_sources[0]
    # Default is page is allowed through
    result = 0
    reasoning = "Page allowed; not blocked"
    # Check if browser block message in page source:
    for browser, browser_block_message in browser_block_messages.items():
        if browser_block_message in page_source:
            result = 1
            reasoning = browser + ": " + browser_block_message
            break
    # Check for other potential scenarios if result != 1 already
    if result != 1:
        # Check for not found messages
        for not_found, not_found_message in not_found_messages.items():
            if not_found_message in page_source:
                result = -1
                reasoning = not_found + ": " + not_found_message
                break
    return result, reasoning

# Verify that all data folders (session folders) contain valid data:
# - network_logs.txt
# - page_sources.json
# Automatically tries to re-retrieve logs from BrowserStack
# Returns list of sessions to be skipped if they are unable to be read properly 
def verify_data_folders(data_folders):
    if DEBUG:
        print("DEBUG: Verifying data folders...")
    invalid_sessions = []
    if os.path.isfile('invalid_sessions.yml'):
        try:
            if DEBUG:
                print("Existing invalid_sessions found, importing...")
            with open('invalid_sessions.yml', mode='r') as f:
                invalid_sessions = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Existing invalid_sessions not found. Creating new...")
    else:
        for data_folder in data_folders:
            curr_folder = os.path.join(parent_folder, data_folder) # build folders
            for session_folder in os.listdir(curr_folder):
                session_folder_path = os.path.join(curr_folder, session_folder)
                if not os.path.isdir(session_folder_path): # skip info.json
                    continue
                # Check network_logs.txt files
                network_logs_path = os.path.join(session_folder_path, 'network_logs.txt')
                invalid_log = False
                try:
                    with open(network_logs_path, 'r', encoding='utf-8', errors='replace') as f:
                        json.load(f, strict=False)
                except json.JSONDecodeError as e:
                    if "Expecting value" in e.msg:
                        invalid_log = True
                        print(f"\nFound invalid network_logs.txt for build {data_folder} and session {session_folder}")
                        print(f"Running `python -m run browserstack save_logs -s {session_folder}`...")
                        subprocess.run([sys.executable, "-m", "run", "browserstack", "save_logs", "-s", session_folder], cwd="..")
                if invalid_log:
                    print("Attempting to retrieve log again...")
                    try:
                        with open(network_logs_path, 'r', encoding='utf-8', errors='replace') as f:
                            json.load(f, strict=False)
                            print("Log successfully loaded.")
                    except json.JSONDecodeError as e:
                        if "Expecting value" in e.msg:
                            if session_folder not in invalid_sessions:
                                print(f"Log invalid. Adding {session_folder} to list of invalid sessions to be skipped.")
                                invalid_sessions.append(session_folder)
                                continue
                # Check page_sources.json files 
                page_sources_path = os.path.join(session_folder_path, 'page_sources.json')
                invalid_log = False
                try:
                    with open(page_sources_path, 'r', encoding='utf-8', errors='replace') as f:
                        data = json.load(f, strict=False)
                        page_sources = [entry['text'] for entry in data]
                        page_sources[0]
                except (json.JSONDecodeError, UnicodeDecodeError, IndexError) as e:
                    invalid_log = True
                    print(f"\nFound invalid page_sources.json for build {data_folder} and session {session_folder}")
                    print(f"Running `python -m run browserstack save_pagesrc -s {session_folder}`...")
                    subprocess.run([sys.executable, "-m", "run", "browserstack", "save_pagesrc", "-s", session_folder], cwd="..")
                if invalid_log:
                    print("Attempting to retrieve log again...")
                    try:
                        with open(page_sources_path, 'r', encoding='utf-8', errors='replace') as f:
                            data = json.load(f, strict=False)
                            page_sources = [entry['text'] for entry in data]
                            page_sources[0]
                            print("Log successfully loaded.")
                    except (json.JSONDecodeError, UnicodeDecodeError, IndexError) as e:
                        if session_folder not in invalid_sessions:
                            print(f"Log invalid. Adding {session_folder} to list of invalid sessions to be skipped.")
                            invalid_sessions.append(session_folder)
                            continue
        with open('invalid_sessions.yml', 'w') as f:
            yaml.dump(invalid_sessions, f, default_flow_style=False)
    print("DEBUG: Done verifying data folders.")
    return invalid_sessions

def main():
    sys.set_int_max_str_digits(0) # Allow for larger integer conversion
    
    # Initial processing to create hot mappings
    if INCLUDE_HEADER_VALUES:
        unique_header_data = filter_header_data(data_folders, threshold=0.9)
        header_data_mappings = create_header_data_hot_mappings(unique_header_data, '90percent_header_data_mappings.csv')
    if INCLUDE_HEADER_PRESENCE:
        header_mappings = create_header_hot_mappings(data_folders)

    # Create output CSV file first
    with open(OUTPUT_FILE, mode='w', newline='') as csvfile:
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
        if INCLUDE_BLOCKED_RESULT:
            header_row.append('blocked')
            header_row.append('reasoning')
        header_row.append('public_url')
        if INCLUDE_HEADER_PRESENCE:
            header_row.append('all_headers')
            header_row.append('request_headers')
            header_row.append('response_headers')
        if INCLUDE_HEADER_VALUES:
            http_headers = [header_name for header_name, _ in unique_header_data]
            for header in http_headers:
                header_row.append(header)
        csv_writer.writerow(header_row)

        # Verify all data is valid; if invalid, write to file
        invalid_sessions = verify_data_folders(data_folders) # Verify that all data is valid
        
        # Parse all valid data folders
        for data_folder in data_folders:
            curr_folder = os.path.join(parent_folder, data_folder) # build folders
            # We want to create an entry for session; loop through all sessions
            for session_folder in os.listdir(curr_folder):
                if session_folder in invalid_sessions:
                    if DEBUG:
                        print(f"Skipping invalid session '{session_folder}'.")
                    continue
                
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
                session_data.append(parsed_session_json['browser_version'] if parsed_session_json['browser_version'] is not None else "None")
                
                # Parse page_sources.json
                #   - result (0=unblocked, 1=blocked by browser, -1=blocked by other)
                page_sources_path = os.path.join(session_folder_path, 'page_sources.json')
                if INCLUDE_BLOCKED_RESULT:
                    blocked, reasoning = get_result(page_sources_path)
                    session_data.append(blocked)
                    session_data.append(reasoning)
                
                # Parse public_url from session.json
                session_data.append(get_public_url(session_json_path))
                
                # Parse network_logs.txt
                #   - All request headers (bitmap of all values in the network requests associated with a website visit)
                #   - All response headers (bitmap of all values in the network responses associated with a website visit)
                network_logs_path = os.path.join(session_folder_path, 'network_logs.txt')
                if INCLUDE_HEADER_PRESENCE:
                    all_headers, request_headers, response_headers = get_present_headers(network_logs_path, header_mappings)
                    session_data.append(all_headers)
                    session_data.append(request_headers)
                    session_data.append(response_headers)
                if INCLUDE_HEADER_VALUES:
                    header_data = get_header_data(network_logs_path, header_data_mappings, http_headers)
                    for header_value in header_data:
                        session_data.append(header_value)
                
                # After all processsing, append data to CSV
                # print("Adding data:", session_data)
                csv_writer.writerow(session_data)


if __name__ == "__main__":
    main()