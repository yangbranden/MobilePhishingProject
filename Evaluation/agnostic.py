import os
import json
import csv
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pandasgui import show

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
    
    # Safari does not loads up any page when site is blocked.
    # driver.page_source remains at the previously visited page. So this method does not work for Safari.
    # need to figure out how to fix this. maybe checking previously_visited_url == driver.current_url ??
    
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

def parse_data(data_dirs: list, csv_path: str):
    # Open CSV file for appending
    with open(csv_path, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = None  # Writer object to be initialized after getting fieldnames
        
        for data_dir in data_dirs:
            print(f"Parsing directory '{data_dir}'...")
            # Walk through all files and subdirectories in the base directory
            for dirpath, dirnames, _ in os.walk(data_dir):
                for dir in dirnames:
                    # Loop through each session folder
                    session_path = os.path.join(dirpath, dir)
                    session_data = dict()  # Keep track of data for current session
                    visit_data = list()  # List of dicts for each page visit
                    for file in os.listdir(session_path):
                        file_path = os.path.join(session_path, file)

                        # Parse text logs
                        if file == "text_logs.txt":
                            with open(file_path, 'r', encoding='utf-8') as f:
                                get_url_req_detected = False  # Prevent multiple entries for consecutive REQUESTs to /source
                                get_source_req_detected = False
                                url = None

                                text_logs = f.read().splitlines()
                                for line in text_logs:
                                    result = None
                                    if "REQUEST" in line:
                                        # Detect the REQUEST for /url
                                        if "/url" in line:
                                            segments = line.split(' ')
                                            json_str = ' '.join(segments[7:])
                                            try:
                                                json_data = json.loads(json_str)
                                                url = json_data["url"].replace("http", "hxxp")
                                            except Exception as e:
                                                print(f"Exception getting /url: {e}")
                                                continue
                                            get_url_req_detected = True
                                        # Detect the REQUEST for /source
                                        elif "/source" in line and get_url_req_detected:
                                            get_source_req_detected = True  # Indicates that the next RESPONSE should be interpreted as page source
                                            get_url_req_detected = False  # Previous REQUEST is no longer for /url
                                    elif "RESPONSE" in line:
                                        # Detect the RESPONSE after the /source request
                                        if get_source_req_detected:
                                            try:
                                                # First get timestamp
                                                segments = line.split(' ')
                                                timestamp = ' '.join(segments[:2])

                                                # Then get json response data
                                                segments = line.split('{')
                                                json_str = '{' + '{'.join(segments[1:])
                                                json_data = json.loads(json_str)
                                                page_source = json_data["value"] # page source is given in "value" field from RESPONSE log
                                                result = 0

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

                                                if result == 0:
                                                    reasoning = "Page allowed; not blocked"

                                                current_entry = dict()
                                                current_entry["url"] = url
                                                current_entry["page_source"] = None  # commenting out because otherwise file becomes unreadable (too big)
                                                current_entry["result"] = result  # 0 = allowed through; 1 = blocked by browser; -1 = other reason (blocked by 3rd party/taken down)
                                                current_entry["reasoning"] = reasoning
                                                current_entry["timestamp"] = timestamp
                                                visit_data.append(current_entry)
                                            except Exception as e:
                                                print(f"Exception getting page source: {e}")
                                                continue
                                            get_source_req_detected = False

                        # Parse session.json
                        elif file == "session.json":
                            try:
                                with open(file_path, 'r') as f:
                                    json_data = json.load(f)

                                    session_data["device"] = json_data["device_info"].get("device", "Unknown")
                                    session_data["os"] = json_data["device_info"]["os"]
                                    session_data["os_version"] = json_data["device_info"]["os_version"]
                                    session_data["browser"] = json_data["device_info"]["browser"]
                                    session_data["browser_version"] = json_data["device_info"]["browser_version"]
                                    session_data["public_url"] = json_data["public_url"]

                            except json.JSONDecodeError:
                                print(f"Error decoding JSON in {file_path}")

                    # Go through all visit data and create entries to write into CSV
                    for visit in visit_data:
                        # Initialize each entry to session_data
                        entry = dict()
                        entry["device"] = session_data.get("device", "Unknown")
                        entry["os"] = session_data["os"]
                        entry["os_version"] = session_data["os_version"]
                        entry["browser"] = session_data["browser"]
                        entry["browser_version"] = session_data["browser_version"]
                        entry["url"] = visit["url"]
                        entry["result"] = visit["result"]
                        entry["reasoning"] = visit["reasoning"]
                        entry["public_url"] = session_data["public_url"]
                        entry["page_source"] = visit["page_source"]
                        entry["timestamp"] = visit["timestamp"]

                        # Initialize CSV writer once fieldnames are available
                        if writer is None:
                            writer = csv.DictWriter(csv_file, fieldnames=entry.keys())
                            writer.writeheader()
                        # Write the entry to the CSV file
                        writer.writerow(entry)


def agnostic_criteria(csv_file_path):
    try:
        df = pd.read_csv(csv_file_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S:%f') # convert timestamp to datetime object
        df = df[df['result'] != -1]  # Remove rows where result is -1

        # Plot 1: device horizontal bar chart for average result (recall: 0 = allowed through; 1 = blocked by browser; -1 = other reason (blocked by 3rd party/taken down))
        df = df[df['device'].notna()] # remove null values for device
        df['result'].groupby(df['device']).mean().sort_values().plot(kind='barh', figsize=(10, 8), color='skyblue')
        plt.title('Average Result by Device')
        plt.xlabel('Average Result')
        plt.ylabel('Device')
        plt.show()
        
        # Observation: due to groupings, I think maybe a big factor is the time of testing (more so than the factors of device/os/browser)
        # df.set_index('timestamp', inplace=True)
        # resampled_times = df.groupby('device').resample('h').size().reset_index(name='test_count')
        # tested_times = resampled_times[resampled_times['test_count'] > 0]
        # show(tested_times[['device', 'timestamp']])
        # # This is just without resampling (to confirm individual timestamps) 
        # device_times = df.groupby('device').size().reset_index(name='test_count')
        # df_reset = df.reset_index()
        # tested_times = df_reset[df_reset['device'].isin(device_times[device_times['test_count'] > 0]['device'])]
        # show(tested_times[['device', 'timestamp']])
        
        # Plot 2: OS horizontal bar charts
        # for os in df['os'].unique():
        #     # Filter the data for the current OS
        #     os_data = df[df['os'] == os]
        #     # Calculate the average result (success rate) for each os_version
        #     avg_results = os_data.groupby('os_version')['result'].mean()
        #     # Create a horizontal bar plot for the average success rate (no sorting)
        #     plt.figure(figsize=(12, 6))
        #     avg_results.plot(kind='barh', color='skyblue')
        #     # Set x-axis limits from -1 to 1
        #     plt.xlim(-1, 1)
        #     plt.title(f'Average Success Rate by OS Version for {os}')
        #     plt.xlabel('Average Success Rate')
        #     plt.ylabel('OS Version')
        #     plt.tight_layout()
        #     plt.show()
        
        # Plot 3: browser horizontal bar charts
        # for browser in df['browser'].unique():
        #     # Filter the data for the current browser
        #     browser_data = df[df['browser'] == browser]
        #     # Calculate the average result (success rate) for each browser_version
        #     avg_results = browser_data.groupby('browser_version')['result'].mean()
        #     # Create a horizontal bar plot for the average success rate (no sorting)
        #     plt.figure(figsize=(12, 6))
        #     avg_results.plot(kind='barh', color='skyblue')
        #     # Set x-axis limits from -1 to 1
        #     plt.xlim(-1, 1)
        #     plt.title(f'Average Success Rate by Browser Version for {browser}')
        #     plt.xlabel('Average Success Rate')
        #     plt.ylabel('Browser Version')
        #     plt.tight_layout()
        #     plt.show()
        
        
        
        
        
        ### IGNORE (was using for testing data cleaning stuff) ###
        # with open(csv_file_path, mode='r', newline='', encoding='utf-8') as file:
        #     reader = csv.DictReader(file)
            
        #     # Check if required fields exist
        #     if 'public_url' not in reader.fieldnames or 'result' not in reader.fieldnames:
        #         raise ValueError("CSV file must contain 'public_url' and 'result' columns.")
            
        #     print("Public URLs with result = 0:")
        #     for row in reader:
        #         try:
        #             temp_skip = [
        #                 "hxxps://keepo.io/goodgood/",
        #                 "hxxps://bafkreic73cwiszlzfyym5yow4ndbxgkzk5dwtt3aye5u4t63hgoimvf7nu.ipfs.dweb.link/",
        #             ]
        #             if int(row['result']) == 0 and row['url'] not in temp_skip and "hxxps://docs.google.com/presentation/d/" not in row['url']:
        #                 print(row)
        #         except ValueError:
        #             print(f"Skipping invalid result value: {row['result']}")
    except FileNotFoundError:
        print(f"File not found: {csv_file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Replace with directory to analyze
    data_directories = [
        # './output_data/HGWhwxQ6_All_Targets',
        # './output_data/JwIZY1fx_All_Targets',
        # './output_data/6rVphbHX_All_Targets',
        # './output_data/pOKUgP2N_All_Targets',
        # './output_data/xhYQi9NJ_All_Targets',
        # './output_data/rJJdSLUJ_All_Targets',
        # './output_data/iHRIMXqv_All_Targets',
        # './output_data/8BIwchFv_All_Targets',
        # './output_data/O2M8irR0_All_Targets', # i think the data collection before this is kinda bad :(
        './output_data/YWkkHPgU_All_Targets',
        './output_data/1uAdSmiL_All_Targets',
        './output_data/Lx1iBz0s_All_Targets',
        './output_data/lQqblPgs_All_Targets',
        './output_data/HtWS2rps_All_Targets',
        './output_data/ItjDdasT_All_Targets',
        './output_data/WVGMx5Y2_All_Targets',
        './output_data/UB70Lvvd_All_Targets',
        ]
    csv_file = './Evaluation/agnostic_test.csv'
    parse_data(data_directories, csv_file)
    
    # This is the actual data analysis
    # agnostic_criteria(csv_file)