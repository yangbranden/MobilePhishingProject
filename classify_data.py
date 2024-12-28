import os
import json
import shutil
import argparse

def get_info_from_json(json_path):
    """Read the platform (OS) and browser from the session.json file."""
    try:
        with open(json_path, 'r') as file:
            data = json.load(file)
            platform = data.get('device_info', {}).get('os')
            browser = data.get('device_info', {}).get('browser')
            return platform, browser
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error reading {json_path}: {e}")
        return None, None

def copy_files(source, dest):
    """Copy files from source to destination, skipping if destination already exists."""
    if not os.path.exists(dest):
        os.makedirs(dest)
        shutil.copytree(source, dest, dirs_exist_ok=True)
        print(f"Copied {source} to {dest}")
    else:
        print(f"Skipped {source} (already exists at {dest})")

def reorganize_logs(source_dirs, sort_by):
    for source_dir in source_dirs:
        parent_dir = os.path.join("sorted", os.path.basename(source_dir))
        
        # Copy over info.json file
        info_file_path = os.path.join(source_dir, "info.json")
        new_info_file_path = os.path.join(parent_dir, "info.json")
        if os.path.exists(info_file_path):
            os.makedirs(os.path.dirname(new_info_file_path), exist_ok=True)
            shutil.copy(info_file_path, new_info_file_path)
        
        if not os.path.isdir(source_dir):
            print(f"Skipping {source_dir} as it is not a directory.")
            continue

        for session_dir in os.listdir(source_dir):
            session_path = os.path.join(source_dir, session_dir)
            if not os.path.isdir(session_path):
                continue

            session_json_path = os.path.join(session_path, 'session.json')
            platform, browser = get_info_from_json(session_json_path)

            # Determine the destination based on the sort_by argument
            if sort_by == "os" and platform:
                new_session_path = os.path.join(parent_dir, "os", platform, session_dir)
            elif sort_by == "browser" and browser:
                new_session_path = os.path.join(parent_dir, "browser", browser, session_dir)
            else:
                with open("errors.log", "a") as error_log:
                    error_log.write(f"Skipping {session_dir}: Invalid or missing {sort_by}\n")
                continue

            # Copy the session directory to the new path if it doesn't already exist
            copy_files(session_path, new_session_path)

def rename_session_directories(base_path):
    # Loop through all directories in the base_path
    for folder in os.listdir(base_path):
        # Check if already renamed
        if "_" in folder:
            continue
        
        folder_path = os.path.join(base_path, folder)
        
        # Ensure it's a directory
        if not os.path.isdir(folder_path):
            continue
        
        session_file = os.path.join(folder_path, "session.json")
        
        # Check if session.json exists
        if not os.path.isfile(session_file):
            print(f"Skipping {folder}: 'session.json' not found.")
            continue
        
        # Read the JSON file
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            build_name = session_data.get("build_name")
            if not build_name:
                print(f"Skipping {folder}: 'build_name' not found in 'session.json'.")
                continue
            
            # Extract the number by splitting the build_name field
            parts = build_name.split()
            if len(parts) < 2:
                print(f"Skipping {folder}: Unexpected 'build_name' format.")
                continue
            
            number = f"{int(parts[1]):02d}"
            new_folder_name = f"{number}_{folder}"
            new_folder_path = os.path.join(base_path, new_folder_name)
            
            # Rename the directory
            os.rename(folder_path, new_folder_path)
            print(f"Renamed '{folder}' to '{new_folder_name}'")
        
        except Exception as e:
            print(f"Error processing {folder}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reorganize session logs by OS/platform or browser within each source directory.")
    parser.add_argument("source_dirs", nargs='+', type=str, help="List of source directories containing the build_id folders.")
    args = parser.parse_args()

    # Run rename_session_directories for all passed source directories
    for base_path in args.source_dirs:
        rename_session_directories(base_path)

    # Run reorganize_logs for both os and browser
    reorganize_logs(args.source_dirs, "os")
    reorganize_logs(args.source_dirs, "browser")
