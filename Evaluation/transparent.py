import os
import json
import csv
from readability import Readability

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
    "Page Not Found": "Not Found"
}

def parse_data(base_dir):
    data = list() # Data to be returned (CSV file contents)
    # Walk through all files and subdirectories in the base directory
    for dirpath, dirnames, _ in os.walk(base_dir):
        for dir in dirnames:
            # Loop through each session folder
            session_path = os.path.join(dirpath, dir)
            session_data = dict() # Keep track of data for current session
            visit_data = list() # List of dicts for each page visit
            # print(session_path)
            for file in os.listdir(session_path):
                file_path = os.path.join(session_path, file)
                
                # Parse text logs
                if file == "text_logs.txt":
                    with open(file_path, 'r', encoding='utf-8') as f:
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
                                # Detect the REQUEST for /source
                                elif "/source" in line:
                                    get_source_req_detected = True # indicates that the next RESPONSE should be interpreted as page source
                            elif "RESPONSE" in line:
                                # Detect the RESPONSE after the /source request
                                if get_source_req_detected:
                                    try:
                                        segments = line.split('{"value":')
                                        page_source = '{"value":'.join(segments[1:])[:-1] # get the page source by parsing it out of the "value" json response (remove last '}')
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
                                        current_entry["page_source"] = page_source
                                        current_entry["result"] = result
                                        current_entry["reasoning"] = reasoning
                                        visit_data.append(current_entry)
                                    except Exception:
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
            
            # Go through all visit data and create entries to put into data
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
                data.append(entry)
    return data

def SMOG_algorithm(text):
    try:
        readability = Readability(text)
        result = readability.smog(all_sentences=True)
        return result
    except Exception as e:
        return e # SMOG requires 30 sentences.


def parse_blocked_data(data):
    blocked_data = []  # List to store all blocked entries

    for entry in data:  # Loop through each entry in the data list
        if entry['result'] == 1:  # Check if the result indicates the page is blocked
            
            # Calculate SMOG and add to entry
            readability = SMOG_algorithm(entry['page_source'])
            entry['smog'] = readability
            print(readability)
            # Add the entire entry to the blocked_data list     
            blocked_data.append(entry)

    return blocked_data


def create_csv(file_path, data):
    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        # Extract headers from the first dictionary
        fieldnames = data[0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        # Write the header row
        writer.writeheader()
        # Write each dictionary as a row
        writer.writerows(data)
        
def transparent_criteria():
    # Replace with directory to analyze
    base_directory = '../output_data/UB70Lvvd_All_Targets'
    csv_output = './transparent.csv'
    csv_blocked_output = './blocked_page/blocked.csv'
    data = parse_data(base_directory)
    create_csv(csv_output, data)
    
    blocked_data = parse_blocked_data(data)
    create_csv(csv_blocked_output, blocked_data)
    
    # SMOG_algorithm()
    
    
transparent_criteria()

