# Script for converting the raw data from the brand-targeted data collections (visit single URL only) into a CSV file
# Input:
#   - info.json
#   - session.json
#   - network_logs.txt
#   - text_logs.txt
#
# Output (fields of CSV file):
#   (from info.json):
#   - url (URL of website visited)
#   (from nothing; assumed because this data collection is all phishing)
#   - phishing (whether the website is phishing or benign)
#   (from session.json):
#   - device
#   - os
#   - os_version
#   - browser
#   - browser_version
#   (from network_logs.txt):
#   - All headers presence (bitmap of all values in the network requests/responses associated with a website visit)
#   - All request headers presence (bitmap of all values in the network requests associated with a website visit)
#   - All response headers presence (bitmap of all values in the network responses associated with a website visit)
#   (from text_logs.txt):
#   - result

import os
import csv
import json
import sys
import subprocess
import yaml
from datetime import datetime

# dumb hack to increase csv field size
maxInt = sys.maxsize
while True:
    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt/10)
sys.set_int_max_str_digits(0) # Allow for larger integer conversion

# SETTINGS (these are mostly for debugging but we can also tailor the output CSV)
OUTPUT_FILE = 'batch_data_noheaders_1_15_2025.csv'
APPIUM_IS_BLOCK = True # Edge case for Safari visits to phishing sites; if True, consider page sources with Appium documentation as detected phishing by Safari; otherwise -1
UNIQUE_HEADER_DATA_THRESHOLD = 0.8 # Headers with unique values in more than (this specified percentage) of their total values are ignored (e.g. 0.5 = 50%; if 50% of values are unique, ignore the header)
HEADER_VALUE_MAPPING_FILE = 'mappingfile_batch_data_80percent_header_data.csv' # File to save the mappings for the header-value pair encodings in
ALL_HEADER_MAPPING_FILE = 'mappingfile_batch_data_all_header_presence.csv' # File to save the mappings for all header presence encodings in
REQUEST_HEADER_MAPPING_FILE = 'mappingfile_batch_data_request_header_presence.csv' # File to save the mappings for request header presence encodings in
RESPONSE_HEADER_MAPPING_FILE = 'mappingfile_batch_data_response_header_presence.csv' # File to save the mappings for response header presence encodings in
DEBUG = True # Show debug prints
INCLUDE_BLOCKED_RESULT = True # Determine whether or not page was blocked
INCLUDE_HEADER_PRESENCE = False # Hot mappings for headers present in request/response/all network logs
INCLUDE_HEADER_VALUES = False # Hot mappings for header-value pairs
INVALID_SESSIONS_FILE = 'invalid_sessions_batch_data.yml'

# Specify data location here:
parent_folder = '../output_data'
data_folders = [
    'YWkkHPgU_All_Targets',
    '1uAdSmiL_All_Targets',
    'Lx1iBz0s_All_Targets',
    'lQqblPgs_All_Targets',
    'HtWS2rps_All_Targets',
    'ItjDdasT_All_Targets',
    'WVGMx5Y2_All_Targets',
    'UB70Lvvd_All_Targets',
    '6RXagsDZ_All_Targets',
    'VBlGVVF8_Android',
    'vr3No8Pv_Android',
    'wLBpgJNn_Android',
    'oNXmQznS_Android',
    'zbSbjZVH_iOS',
    'yeH04IHk_iOS',
    'Ahr2slMU_iOS',
    'LVD83eZN_iOS',
]

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
    "Appium.io": "The Appium automation project documentation", # This for some reason occurs mostly on iOS devices; it will just redirect to appium.io documentation, I think has something to do with BrowserStack
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
    "This site can't be reached": "<html><head></head><body></body></html>"
}

# Create hot mappings for headers present in the HTTP requests/responses
def create_header_hot_mappings(data_folders):
    if DEBUG:
        print("DEBUG: Creating hot mappings for headers present...")
    request_headers = set()
    response_headers = set()
    for data_folder in data_folders:
        curr_folder = os.path.join(parent_folder, data_folder) # build folders
        # Get the target URL so we know which requests/responses are relevant
        info_json_path = os.path.join(curr_folder, 'info.json')
        target_urls = get_urls(info_json_path)
        for session_folder in os.listdir(curr_folder):
            session_folder_path = os.path.join(curr_folder, session_folder)
            if not os.path.isdir(session_folder_path):
                continue
            network_logs_path = os.path.join(session_folder_path, 'network_logs.txt')
            for target_url in target_urls:
                target_url = target_url.replace("hxxp", "http")
                try:
                    with open(network_logs_path, 'r', encoding='utf-8', errors='replace') as f:
                        log_data = json.load(f, strict=False)  # Parse the JSON file
                        for entry in log_data.get('log', {}).get('entries', []):
                            # Check if target_url is in the request URL or Referer header
                            request_url = entry.get('request', {}).get('url', "")
                            referer = next((header.get('value') for header in entry.get('request', {}).get('headers', []) if header.get('name') == "Referer"), "")

                            # Skip this entry if the target_url is not in either the request_url or referer
                            if target_url not in request_url and target_url not in referer:
                                continue  # Skip to the next entry (each entry is a request/response pair)

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
    all_header_mapping_file = ALL_HEADER_MAPPING_FILE
    if DEBUG:
        print("DEBUG: Creating hot mappings for all headers...")
    # For some reason this is slower than re-creating the mappings
    # if os.path.isfile(all_header_mapping_file):
    #     try:
    #         if DEBUG:
    #             print("Existing mappings found, importing...")
    #         with open(all_header_mapping_file, mode='r', newline='') as csvfile_hm:
    #             csv_reader_hm = csv.reader(csvfile_hm)
    #             next(csv_reader_hm) # Skip header row
    #             all_headers_mapping = [tuple(row) for row in csv_reader_hm]
    #     except FileNotFoundError:
    #         print(f"ERROR: '{all_header_mapping_file}' does not exist.")
    # else:
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
    request_headers_mapping_file = REQUEST_HEADER_MAPPING_FILE
    if DEBUG:
        print("DEBUG: Creating hot mappings for request headers...")
    # For some reason this is slower than re-creating the mappings
    # if os.path.isfile(request_headers_mapping_file):
    #     try:
    #         if DEBUG:
    #             print("Existing mappings found, importing...")
    #         with open(request_headers_mapping_file, mode='r', newline='') as csvfile_hm:
    #             csv_reader_hm = csv.reader(csvfile_hm)
    #             next(csv_reader_hm) # Skip header row
    #             request_headers_mapping = [tuple(row) for row in csv_reader_hm]
    #     except FileNotFoundError:
    #         print(f"ERROR: '{request_headers_mapping_file}' does not exist.")
    # else:
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
    response_headers_mapping_file = RESPONSE_HEADER_MAPPING_FILE
    if DEBUG:
        print("DEBUG: Creating hot mappings for response headers...")
    # For some reason this is slower than re-creating the mappings
    # if os.path.isfile(response_headers_mapping_file):
    #     try:
    #         if DEBUG:
    #             print("Existing mappings found, importing...")
    #         with open(response_headers_mapping_file, mode='r', newline='') as csvfile_hm:
    #             csv_reader_hm = csv.reader(csvfile_hm)
    #             next(csv_reader_hm) # Skip header row
    #             response_headers_mapping = [tuple(row) for row in csv_reader_hm]
    #     except FileNotFoundError:
    #         print(f"ERROR: '{response_headers_mapping_file}' does not exist.")
    # else:
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
# threshold default at 0.5, or 50%; if >50% of values are unique for a header, ignore it
def filter_header_data(data_folders, threshold=0.5):
    if DEBUG:
        print("DEBUG: getting unique header-value pairs...")
    header_data = {}
    for data_folder in data_folders:
        curr_folder = os.path.join(parent_folder, data_folder)
        # Get the target URL so we know which requests/responses are relevant
        info_json_path = os.path.join(curr_folder, 'info.json')
        target_urls = get_urls(info_json_path)
        for session_folder in os.listdir(curr_folder):
            session_folder_path = os.path.join(curr_folder, session_folder)
            if not os.path.isdir(session_folder_path):
                continue
            network_logs_path = os.path.join(session_folder_path, 'network_logs.txt')
            for target_url in target_urls:
                target_url = target_url.replace("hxxp", "http")
                try:
                    with open(network_logs_path, 'r', encoding='utf-8', errors='replace') as f:
                        if DEBUG:
                            print(f"(filter_header_data) Parsing '{network_logs_path}'...")
                        log_data = json.load(f, strict=False)
                        for entry in log_data.get('log', {}).get('entries', []):
                            # Check if target_url is in the request URL or Referer header
                            request_url = entry.get('request', {}).get('url', "")
                            referer = next((header.get('value') for header in entry.get('request', {}).get('headers', []) if header.get('name') == "Referer"), "")

                            # Skip this entry if the target_url is not in either the request_url or referer
                            if target_url not in request_url and target_url not in referer:
                                # print(request_url, (target_url not in request_url), referer, (target_url not in referer))
                                continue  # Skip to the next entry (each entry is a request/response pair)

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

# Create hot mappings for relevant header-value pairs from all network_logs.txt files
def create_header_data_hot_mappings(unique_header_data, load_file):
    if DEBUG:
        print("DEBUG: Creating hot mappings for header data (header-value pairs)...")
    hot_mappings = []
    # For some reason this is slower than re-creating the mappings
    # First check if hot mappings exist; if it does then no need to re-create (can take a VERY long time)
    # if os.path.isfile(load_file):
    #     try:
    #         if DEBUG:
    #             print("Existing mappings found, importing...")
    #         with open(load_file, mode='r', newline='') as csvfile_hm:
    #             csv_reader_hm = csv.reader(csvfile_hm)
    #             next(csv_reader_hm) # Skip header row
    #             hot_mappings = [tuple(row) for row in csv_reader_hm]
    #     except FileNotFoundError:
    #         print(f"ERROR: '{load_file}' does not exist.")
    # else:
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
def get_header_data(log_file_path, hot_mappings, unique_headers, target_url):
    if DEBUG:
        print(f"DEBUG: Processing header data (header-value pairs) for {log_file_path}...")
    # Mapping dict contains the hot mappings for all header-value pairs
    mapping_dict = {(header, value): int(mapping_value) for header, value, _, mapping_value in hot_mappings}
    # Variable to keep track of what header-value pairs have been seen in this log
    session_header_data = {header: 0 for header, _, _, _ in hot_mappings}
    # For comparison purposes only; will still be hxxp for safety in the actual data CSV file
    target_url = target_url.replace("hxxp", "http")
    try:
        with open(log_file_path, 'r', encoding='utf-8', errors='replace') as f:
            log_data = json.load(f, strict=False)
            for entry in log_data.get('log', {}).get('entries', []):
                # Check if target_url is in the request URL or Referer header
                request_url = entry.get('request', {}).get('url', "")
                referer = next((header.get('value') for header in entry.get('request', {}).get('headers', []) if header.get('name') == "Referer"), "")

                # Skip this entry if the target_url is not in either the request_url or referer
                if target_url not in request_url and target_url not in referer:
                    continue  # Skip to the next entry (each entry is a request/response pair)

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
def get_present_headers(log_file_path, hot_mappings, target_url):
    # Mapping dicts contain the hot mappings for all headers
    all_headers_mapping, request_headers_mapping, response_headers_mapping = hot_mappings
    all_headers_mapping_dict = {header: int(mapping_value) for header, _, mapping_value in all_headers_mapping}
    request_headers_mapping_dict = {header: int(mapping_value) for header, _, mapping_value in request_headers_mapping}
    response_headers_mapping_dict = {header: int(mapping_value) for header, _, mapping_value in response_headers_mapping}
    # Variables to keep track of what headers have been seen in this log
    all_headers_present = 0
    request_headers_present = 0
    response_headers_present = 0
    # For comparison purposes only; will still be hxxp for safety in the actual data CSV file
    target_url = target_url.replace("hxxp", "http")
    try:
        with open(log_file_path, 'r', encoding='utf-8', errors='replace') as f:
            log_data = json.load(f, strict=False)
            for entry in log_data.get('log', {}).get('entries', []):
                # Check if target_url is in the request URL or Referer header
                request_url = entry.get('request', {}).get('url', "")
                referer = next((header.get('value') for header in entry.get('request', {}).get('headers', []) if header.get('name') == "Referer"), "")

                # Skip this entry if the target_url is not in either the request_url or referer
                if target_url not in request_url and target_url not in referer:
                    continue  # Skip to the next entry (each entry is a request/response pair)

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

# Get all urls in the build
def get_urls(info_json_path):
    try:
        with open(info_json_path, 'r') as f:
            build_data = json.load(f, strict=False)
        urls = build_data.get("urls", [])
        return urls
    except Exception as e:
        print(f"Error parsing info.json: {e}")
        return None

# Logic to parse 'phishing' field
def get_phishing():
    # For this data collection, we assume all sites are phishing; for performing operations on benign sites, see data_cleaning_targeted.py 
    return True

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
        # Note that the data expires after 60 days; so this isn't really that useful if the data is old :(
        # if '?auth_token=' in public_url: # auth_token expires so I will just remove (sorry, I know you guys can't see the browserstack URL)
        #     public_url = public_url.split('?auth_token=')[0]
        return public_url
    except Exception as e:
        print(f"Error parsing session.json: {e}")
        return None

# Logic to parse result from text_logs.txt
def get_result(text_logs_path, is_phishing, url):
    with open(text_logs_path, 'r', encoding='utf-8') as f:
        data = f.read().splitlines()
    get_url_req_detected = False  # Prevent multiple entries for consecutive REQUESTs to /source
    get_source_req_detected = False
    url = url.replace("hxxp", "http")
    page_source = None
    for line in data:
        if "REQUEST" in line:
            # Detect the REQUEST for /url
            if "/url" in line and url in line:
                get_url_req_detected = True
            # Detect the REQUEST for /source
            elif "/source" in line and get_url_req_detected:
                get_source_req_detected = True  # Indicates that the next RESPONSE should be interpreted as page source
                get_url_req_detected = False  # Previous REQUEST is no longer for /url
        elif "RESPONSE" in line:
            # Detect the RESPONSE after the /source request
            if get_source_req_detected:
                try:
                    # Parse for page source
                    segments = line.split('{"value":')
                    page_source = '{"value":'.join(segments[1:])[:-1]  # Get the page source by parsing it out of the "value" json response (remove last '}')
                    break
                except Exception as e:
                    print(f"Exception getting page source: {e}")
                    continue
    if page_source is None:
        print(f"ERROR: Page source not found for url {url}")
        print(text_logs_path)
        return -2, "ERROR"

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
                if APPIUM_IS_BLOCK:
                    if not_found == "Appium.io" and is_phishing:
                        result = 1
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
    if os.path.isfile(INVALID_SESSIONS_FILE):
        try:
            if DEBUG:
                print("Existing invalid_sessions found, importing...")
            with open(INVALID_SESSIONS_FILE, mode='r') as f:
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
        with open(INVALID_SESSIONS_FILE, 'w') as f:
            yaml.dump(invalid_sessions, f, default_flow_style=False)
    print("DEBUG: Done verifying data folders.")
    return invalid_sessions

def main():
    # Initial processing to create hot mappings
    if INCLUDE_HEADER_VALUES:
        unique_header_data = filter_header_data(data_folders, threshold=UNIQUE_HEADER_DATA_THRESHOLD)
        header_data_mappings = create_header_data_hot_mappings(unique_header_data, HEADER_VALUE_MAPPING_FILE)
    if INCLUDE_HEADER_PRESENCE:
        header_mappings = create_header_hot_mappings(data_folders)

    # Create output CSV file first
    with open(OUTPUT_FILE, mode='w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        
        # Write the header row
        header_row = [
            'url', 
            'phishing',
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
                session_urls = get_urls(info_json_path)
                for url in session_urls:
                    # Object to hold data for current entry of CSV row
                    session_data = []

                    session_data.append(url)
                    phishing = get_phishing()
                    session_data.append(phishing)
                
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
                    session_data.append(parsed_session_json['device'] if parsed_session_json['device'] is not None else "None")
                    session_data.append(parsed_session_json['os'])
                    session_data.append(parsed_session_json['os_version'])
                    session_data.append(parsed_session_json['browser'])
                    session_data.append(parsed_session_json['browser_version'] if parsed_session_json['browser_version'] is not None else "None")
                
                    # Parse text_logs.txt
                    #   - result (0=unblocked, 1=blocked by browser, -1=blocked by other)
                    text_logs_path = os.path.join(session_folder_path, 'text_logs.txt')
                    if INCLUDE_BLOCKED_RESULT:
                        blocked, reasoning = get_result(text_logs_path, phishing, url)
                        session_data.append(blocked)
                        session_data.append(reasoning)
                
                    # Parse public_url from session.json
                    session_data.append(get_public_url(session_json_path))
                
                    # Parse network_logs.txt
                    #   - All request headers (bitmap of all values in the network requests associated with a website visit)
                    #   - All response headers (bitmap of all values in the network responses associated with a website visit)
                    network_logs_path = os.path.join(session_folder_path, 'network_logs.txt')
                    if INCLUDE_HEADER_PRESENCE:
                        all_headers, request_headers, response_headers = get_present_headers(network_logs_path, header_mappings, url)
                        session_data.append(all_headers)
                        session_data.append(request_headers)
                        session_data.append(response_headers)
                    if INCLUDE_HEADER_VALUES:
                        header_data = get_header_data(network_logs_path, header_data_mappings, http_headers, url)
                        for header_value in header_data:
                            session_data.append(header_value)
                    
                    # After all processsing, append data to CSV
                    # print("Adding data:", session_data)
                    csv_writer.writerow(session_data)


if __name__ == "__main__":
    main()