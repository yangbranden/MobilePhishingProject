import os
import json
import csv
import re
from datetime import datetime

def parse_data(base_dir):
    results = []
    
    for dirpath, dirname, _ in os.walk(base_dir):
        for dir in dirname:
            session_path = os.path.join(dirpath, dir)
            session_data = dict()
            
            for file in os.listdir(session_path):
                file_path = os.path.join(session_path, file)
                
                if file == "text_logs.txt":
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text_logs = f.read().splitlines()
                        request_data = {}
                        
                        for line in text_logs:
                            # Extract REQUEST logs
                            if "REQUEST" in line and "/url" in line:
                                try:
                                    segments = line.split(' ')
                                    json_str = ' '.join(segments[7:])
                                    json_data = json.loads(json_str)
                                    url = json_data["url"].replace("http", "hxxp")
                                    
                                    match_request = re.search(
                                        r'(\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}:\d{2}:\d{3})', line
                                    )
                                    if match_request:
                                        request_time = datetime.strptime(
                                            match_request.group(1), "%Y-%m-%d %H:%M:%S:%f"
                                        )
                                        request_data[url] = request_time
                                except Exception as e:
                                    print(f"Exception getting /url: {e}")

                            # Extract RESPONSE logs
                            elif "RESPONSE" in line:
                                match_response = re.search(
                                    r'(\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}:\d{2}:\d{3})', line
                                )
                                if match_response:
                                    response_time = datetime.strptime(
                                        match_response.group(1), "%Y-%m-%d %H:%M:%S:%f"
                                    )
                                    # Match RESPONSE to the last REQUEST URL
                                    for url, req_time in request_data.items():
                                        time_diff = (response_time - req_time).total_seconds() * 1000  # ms
                                        results.append({
                                            "url": url,
                                            "request_time": req_time,
                                            "response_time": response_time,
                                            "time_difference_ms": time_diff
                                        })
                                    request_data = {}  # Reset after processing

                elif file == "session.json":
                    try:
                        with open(file_path, 'r') as f:
                            json_data = json.load(f)
                            session_data['device'] = json_data['device_info'].get('device', 'Unknown')
                            session_data['os'] = json_data['device_info'].get('os')
                            session_data['os_version'] = json_data['device_info'].get('os_version')
                            session_data['browser'] = json_data['device_info'].get('browser')
                            session_data['browser_version'] = json_data['device_info'].get('browser_version')
                    except json.JSONDecodeError:
                        print(f"Error decoding JSON in {file_path}")

            # Update session data for all results
            for result in results:
                result.update(session_data)

    return results

         
def create_csv(file_path, data):
    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        if not data:
            print("No data to write.")
            return
        fieldnames = data[0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def analysis():
    # TODO: can put ML/statistics stuff here
    return

def lightweight_criteria():
    # Replace with directory to analyze
    base_directory = './output_data/target_name'
    csv_output = './Evaluation/lightweight_test.csv'
    
    data = parse_data(base_directory)
    create_csv(csv_output, data)
    
    # analysis()


lightweight_criteria()
