import os
import json
import yaml  # This library allows easy writing of YAML files

# Define the parent folder path
parent_folder = 'output_data'
request_headers_ofile = 'MachineLearning/request_headers.yml'
response_headers_ofile = 'MachineLearning/response_headers.yml'

# Initialize sets to store unique request and response header names
request_headers = set()
response_headers = set()

# Traverse all subfolders and files under the parent folder
for root, dirs, files in os.walk(parent_folder):
    for file in files:
        if file == 'network_logs.txt':  # Look for files named 'network_logs.txt'
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    log_data = json.load(f)  # Parse the JSON file
                    for entry in log_data.get('log', {}).get('entries', []):
                        # Extract request headers
                        for header in entry.get('request', {}).get('headers', []):
                            request_headers.add(header.get('name'))
                        
                        # Extract response headers
                        for header in entry.get('response', {}).get('headers', []):
                            response_headers.add(header.get('name'))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print(f"Error reading {file_path}: {e}")

# Save unique request headers to request_headers.yml
with open(request_headers_ofile, 'w', encoding='utf-8') as f:
    yaml.dump(sorted(request_headers), f, default_flow_style=False)
print(f"Request headers written to {request_headers_ofile}")

# Save unique response headers to response_headers.yml
with open(response_headers_ofile, 'w', encoding='utf-8') as f:
    yaml.dump(sorted(response_headers), f, default_flow_style=False)
print(f"Response headers written to {response_headers_ofile}")
