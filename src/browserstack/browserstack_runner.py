import ruamel.yaml
import time
import os
import requests
import json
from datetime import datetime
yaml = ruamel.yaml.YAML() # using this version of yaml to preserve comments

from dataclasses import dataclass
from omegaconf import DictConfig, ListConfig

from src.platforms import Platforms
from src.util import write_file_source_header
from src.util import generate_unique_str

# BrowserstackRunner class:
# - run_browserstack (actually runs browserstack)
# - generate_targets (interacts with browserstack API to get list of targets)
# - scope_browser_versions (interacts with browserstack API to get list of browser versions for our scope)

@dataclass
class BrowserstackRunner:
    config: DictConfig | ListConfig # return type of OmegaConf.load()

    def run_browserstack(self):
        test_script = self.config.browserstack_runner.test_script
        urls_file = self.config.browserstack_runner.urls_file
        targets_src = self.config.browserstack_runner.targets_src
        # build_name = f"{datetime.now().strftime("%m_%d")}_{self.config.browserstack_runner.build_name}"
        build_name = f"{generate_unique_str()}_{self.config.browserstack_runner.build_name}"

        # Save the original config to restore later
        with open("browserstack.yml", "r") as f:
            original_config = yaml.load(f)

        found = False
        current_config = None
        files = os.listdir(targets_src)
        sorted_files = sorted(files, key=lambda x: int(x.split('.')[0]))
        
        # Iterate through each file in the target directory
        for file in sorted_files:
            if self.config.browserstack_runner.interrupted:
                if found is False and file != self.config.browserstack_runner.continue_point:
                    print("skipping...")
                    continue 
                
                print("Continuing from", file)
                found = True
            
            # Get the current config
            with open("browserstack.yml", "r") as f:
                current_config = yaml.load(f)

            # Open the file that contains the platforms we want to test on
            with open(os.path.join(targets_src, file), "r") as target_set:
                platforms = yaml.load(target_set)
            
            # edit the config to have the target set we want
            current_config["buildName"] = build_name
            current_config["platforms"] = platforms

            # overwrite the current config
            with open("browserstack.yml", "w") as f:
                yaml.dump(current_config, f)

            # if parallel_sessions_running == 0 then we can continue testing
            # https://api.browserstack.com/automate/plan.json
            s = requests.Session()
            s.auth = (os.environ.get("BROWSERSTACK_USERNAME"), os.environ.get("BROWSERSTACK_ACCESS_KEY"))
            r = s.get("https://api.browserstack.com/automate/plan.json")
            output = json.loads(r.text)
            sleep_counter = 0
            while output["parallel_sessions_running"] != 0:
                print(f"Waiting for parallel session to finish ({sleep_counter})...")
                time.sleep(1)
                sleep_counter += 1

            # run the test
            os.system(f"browserstack-sdk {test_script} {urls_file}")

        # Reset back to the original config
        with open("browserstack.yml", "w") as f:
            yaml.dump(original_config, f)
    
    def generate_targets(self, output_mode):
        if output_mode == "all":
            output_mode = Platforms.ALL
        if output_mode == "android":
            output_mode = Platforms.ANDROID
        if output_mode == "ios":
            output_mode = Platforms.IOS
        if output_mode == "windows":
            output_mode = Platforms.WINDOWS
        if output_mode == "macosx":
            output_mode = Platforms.MACOSX

        assert output_mode in Platforms, "Error: OUTPUT_MODE must be among [ALL, ANDROID, IOS, WINDOWS, MACOSX]; NOTE: this function should not be being called directly.\n"

        # Setup output location
        base_dir = self.config.browserstack_runner.target_generator.targets_directory
        if output_mode == Platforms.ALL:
            output_location = f"{base_dir}/all_targets"
        elif output_mode == Platforms.ANDROID:
            output_location = f"{base_dir}/android"
        elif output_mode == Platforms.IOS:
            output_location = f"{base_dir}/ios"
        elif output_mode == Platforms.WINDOWS:
            output_location = f"{base_dir}/windows"
        elif output_mode == Platforms.MACOSX:
            output_location = f"{base_dir}/macosx"
        if self.config.browserstack_runner.target_generator.custom_outfile is not None:
            output_location = self.config.browserstack_runner.target_generator.custom_outfile

        # Setup for if we are scoping browser versions
        SCOPE_BROWSER_VERSIONS = False
        if self.config.browserstack_runner.target_generator.browser_versions_file is not None:
            SCOPE_BROWSER_VERSIONS = True

        if SCOPE_BROWSER_VERSIONS:
            try:
                with open(f"{self.config.browserstack_runner.target_generator.browser_versions_file}", "r") as f:
                    browser_versions = yaml.load(f)
                    firefox_versions_range = browser_versions["firefox_versions"]
                    chrome_versions_range = browser_versions["chrome_versions"]
                    edge_versions_range = browser_versions["edge_versions"]
                    safari_versions_range = browser_versions["safari_versions"]
                    opera_versions_range = browser_versions["opera_versions"]
            except Exception as e:
                print(f"Unable to open {self.config.browserstack_runner.target_generator.browser_versions_file}; file may not exist. Defaulting to all browser versions. (Error: {e})")

        # Use API to get all possible combinations of browser versions
        s = requests.Session()
        s.auth = (os.environ.get("BROWSERSTACK_USERNAME"), os.environ.get("BROWSERSTACK_ACCESS_KEY"))

        # Make request to API to gather all possible platform combinations
        r = s.get("https://api.browserstack.com/automate/browsers.json")
        output = json.loads(r.text)

        # Remove null values to avoid issues when running browserstack-sdk
        for item in output:
            null_fields = [field for field in item if item[field] is None]
            for n in null_fields:
                item.pop(n)

        # Filter by OS depending on output mode
        selective_output = []
        if output_mode == Platforms.ANDROID:
            for item in output:
                if item["os"] == "android":
                    selective_output.append(item)
            output = selective_output
        elif output_mode == Platforms.IOS:
            for item in output:
                if item["os"] == "ios":
                    selective_output.append(item)
            output = selective_output
        elif output_mode == Platforms.WINDOWS:
            for item in output:
                if item["os"] == "Windows":
                    selective_output.append(item)
            output = selective_output
        elif output_mode == Platforms.MACOSX:
            for item in output:
                if item["os"] == "OS X":
                    selective_output.append(item)
            output = selective_output
        
        # Filter by browser versions (if specified)
        if SCOPE_BROWSER_VERSIONS:
            selective_output = []
            for item in output:
                # just add the mobile devices; we are unable to specify browser versions
                if item["os"] == "android" or item["os"] == "ios":
                    selective_output.append(item)
                    continue
                try:
                    detected_version = float(item["browser_version"])
                    if item["browser"] == "firefox":
                        if detected_version in firefox_versions_range:
                            selective_output.append(item)
                    elif item["browser"] == "chrome":
                        if detected_version in chrome_versions_range:
                            selective_output.append(item)
                    elif item["browser"] == "edge":
                        if detected_version in edge_versions_range:
                            selective_output.append(item)
                    elif item["browser"] == "safari":
                        if detected_version in safari_versions_range:
                            selective_output.append(item)
                    elif item["browser"] == "opera":
                        if detected_version in opera_versions_range:
                            selective_output.append(item)
                except Exception as e:
                    # print(e)
                    continue
            output = selective_output

            # Detect if we are outputting as a single file or directory
            SINGLE_FILE = self.config.browserstack_runner.target_generator.output_as_file

            # Create the output directory; if it already exists, remove existing output
            targets_dir = os.path.dirname(output_location)
            if not os.path.exists(targets_dir):
                os.makedirs(targets_dir)
            if SINGLE_FILE:
                if os.path.exists(output_location):
                    for root, dirs, files in os.walk(output_location, topdown=False):
                        for file in files:
                            os.remove(os.path.join(root, file))
                        for dir in dirs:
                            os.rmdir(os.path.join(root, dir))
                    os.rmdir(output_location)
                os.makedirs(output_location)

            if SINGLE_FILE:
                with open(f"{output_location}.yml", "w") as f:
                    write_file_source_header("generate_targets (browserstack_runner.py)", f)
                    yaml.dump(output, f)
            else:
                # Separate output into files each containing only n entries
                for i in range(0, len(output), self.config.browserstack_runner.target_generator.entries_per_file):
                    batch = output[i:i+self.config.browserstack_runner.target_generator.entries_per_file]
                    file_index = i // self.config.browserstack_runner.target_generator.entries_per_file
                    with open(f"{output_location}/{file_index}.yml", "w") as f:
                        write_file_source_header("generate_targets (browserstack_runner.py)", f)
                        yaml.dump(batch, f)

    # TODO: This currently does not perform any sort of useful analysis; 
    # plan was to use this to programmatically go through the browser changelogs and make a list of versions
    # that have significant security updates
    def scope_browser_versions(self):
        # Use API to get all possible combinations of browser versions
        s = requests.Session()
        s.auth = (os.environ.get("BROWSERSTACK_USERNAME"), os.environ.get("BROWSERSTACK_ACCESS_KEY"))

        r = s.get("https://api.browserstack.com/automate/browsers.json")
        output = json.loads(r.text)

        # Find the latest version
        latest_versions = {
            'firefox': 0.0,
            'chrome': 0.0,
            'edge': 0.0,
            'safari': 0.0,
            'opera': 0.0
        }
        for item in output:
            if item["browser"] == "firefox":
                try:
                    detected_version = float(item["browser_version"])
                    if detected_version > latest_versions["firefox"]:
                        latest_versions["firefox"] = detected_version
                except Exception:
                    continue
            elif item["browser"] == "chrome":
                try:
                    detected_version = float(item["browser_version"])
                    if detected_version > latest_versions["chrome"]:
                        latest_versions["chrome"] = detected_version
                except Exception:
                    continue
            elif item["browser"] == "edge":
                try:
                    detected_version = float(item["browser_version"])
                    if detected_version > latest_versions["edge"]:
                        latest_versions["edge"] = detected_version
                except Exception:
                    continue
            elif item["browser"] == "safari":
                try:
                    detected_version = float(item["browser_version"])
                    if detected_version > latest_versions["safari"]:
                        latest_versions["safari"] = detected_version
                except Exception:
                    continue
            elif item["browser"] == "opera":
                try:
                    detected_version = float(item["browser_version"])
                    if detected_version > latest_versions["opera"]:
                        latest_versions["opera"] = detected_version
                except Exception:
                    continue
        print("Latest versions:\n", latest_versions)

        data = {
            'firefox_versions': [latest_versions["firefox"] - i for i in range(10)],
            'chrome_versions': [latest_versions["chrome"] - i for i in range(10)],
            'edge_versions': [latest_versions["edge"] - i for i in range(10)],
            'safari_versions': [latest_versions["safari"] - i for i in range(10)],
            'opera_versions': [12.16, 12.15]
        }

        with open("./targets/browser_versions.yml", "w+") as f:
            write_file_source_header("scope_browser_versions (browserstack_runner.py)", f)
            yaml.dump(data, f)

    def save_output(self, session_id):
        print(session_id)
        base_output_dir = self.config.browserstack_runner.output_analyzer.output_directory

        s = requests.Session()
        s.auth = (os.environ.get("BROWSERSTACK_USERNAME"), os.environ.get("BROWSERSTACK_ACCESS_KEY"))

        # Check if session ID is valid
        try:
            r = s.get(f"https://api.browserstack.com/automate/sessions/{session_id}/logs")
            response_lines = r.text.splitlines()
        except Exception as e:
            print(f"Invalid session id; Error: {e}")
            return

        # Save full output to tmp.json for debugging purposes
        with open(f"{base_output_dir}/tmp/tmp.json", "w") as f:
            for line in response_lines:
                f.write(line + "\n")

        # Log format:
        # REQUEST for /url
        # REQUEST for whatever the script asks for (e.g. we ask for /source in phish-test.py)
        # REQUEST for the outcome we send using driver.execute_script (in phish-test.py)
        output = dict() # Contains output for all URLs
        current_entry = dict() # used to record the current url
        for line in response_lines:
            if "REQUEST" not in line:
                continue
            segments = line.split(' ')
            json_str = ''.join(segments[7:])
            
            # Attempt to parse as JSON
            try:
                json_data = json.loads(json_str)
                if "/url" in line: # Parses the URL we are requesting
                    current_entry["url"] = json_data["url"]
                elif "/execute/sync" in line: # Parses the response we are sending
                    result = json.loads(json_data["script"].split("browserstack_executor:")[-1])
                    current_entry["script"] = result["arguments"]
                    output[current_entry["url"]] = current_entry["script"]
            except json.JSONDecodeError:
                print(f"Last segment is not valid JSON: {json_str}")

        if not os.path.exists(f"./output_data/outcomes/{session_id}"):
            os.makedirs(f"{base_output_dir}/outcomes/{session_id}")

        with open(f"{base_output_dir}/outcomes/{session_id}/output.json", "w") as f:
            json.dump(output, f, indent=4)

        print(output)
        print(f"\nCheck {base_output_dir}/outcomes/{session_id}/output.json for cleaner view of the output.")

        # Future TODO: Implement system for unique string as test title so that we can search by unique ID instead of platform-specific (in this case, browserstack) session ID
