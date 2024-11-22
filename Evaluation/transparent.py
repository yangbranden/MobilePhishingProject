import os
import json
import csv

def parse_data(base_dir):
    # Walk through all files and subdirectories in the base directory
    for root, _, files in os.walk(base_dir):
        for file in files:
            file_path = os.path.join(root, file)
            
            # Parse text logs
            if file == "text_logs.txt":
                with open(file_path, 'r') as f:
                    # TODO: parse text logs for relevant info
                    text_logs = f.read()
            
            # Parse session.json
            elif file == "session.json":
                try:
                    with open(file_path, 'r') as f:
                        json_data = json.load(f)
                        
                        # TODO: parse session.json for relevant info
                        device_info = json_data["device_info"]
                        
                except json.JSONDecodeError:
                    print(f"Error decoding JSON in {file_path}")

def create_csv(file_path, data):
    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerows(data)
    
def SMOG_algorithm():
    # TODO: SMOG algorithm implementation
    return -1

def transparent_criteria():
    # Replace with directory to analyze
    base_directory = './output_data/pOKUgP2N_All_Targets'
    csv_output = './Evaluation/transparent_test.csv'
    
    data = parse_data(base_directory)
    create_csv(csv_output, data)
    
    # SMOG_algorithm()