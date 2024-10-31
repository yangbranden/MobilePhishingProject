# Used to sort data on server; uploaded at /tank
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
        if not os.path.isdir(source_dir):
            print(f"Skipping {source_dir} as it is not a directory.")
            continue

        for session_id in os.listdir(source_dir):
            session_path = os.path.join(source_dir, session_id)
            if not os.path.isdir(session_path):
                continue

            session_json_path = os.path.join(session_path, 'session.json')
            platform, browser = get_info_from_json(session_json_path)

            # Determine the destination based on the sort_by argument
            if sort_by == "os" and platform:
                new_session_path = os.path.join("sorted", "os", platform, session_id)
            elif sort_by == "browser" and browser:
                # idk if we really want to do this
                # if browser == "ipad" or browser == "iphone":
                #     browser = "safari"
                new_session_path = os.path.join("sorted", "browser", browser, session_id)
            else:
                with open("errors.log", "a") as error_log:
                    error_log.write(f"Skipping {session_id}: Invalid or missing {sort_by}\n")
                continue

            # Copy the session directory to the new path if it doesn't already exist
            copy_files(session_path, new_session_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reorganize session logs by OS/platform or browser for multiple source directories.")
    parser.add_argument("source_dirs", nargs='+', type=str, help="List of source directories containing the build_id folders.")
    parser.add_argument("-s", "--sort-by", choices=["os", "browser"], required=True, help="Specify whether to sort by OS/platform or browser.")
    args = parser.parse_args()
    
    reorganize_logs(args.source_dirs, args.sort_by)
