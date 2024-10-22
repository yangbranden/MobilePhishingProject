import ruamel.yaml
import time
import os
import requests
import json
from datetime import datetime
from user_agents import parse
yaml = ruamel.yaml.YAML() # using this version of yaml to preserve comments

from dataclasses import dataclass
from omegaconf import DictConfig, ListConfig

from src.platforms import Platforms
from src.util import write_file_source_header
from src.util import generate_unique_str
from src.util import remove_empty_lines

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
            response = json.loads(r.text)

            sleep_counter = 0
            while response["parallel_sessions_running"] != 0:
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
            if not SINGLE_FILE:
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


    # Gather all relevant session ids based on a unique identifier in the title of the associated build(s)
    def scrape_session_ids(self, unique_id):
        s = requests.Session()
        s.auth = (os.environ.get("BROWSERSTACK_USERNAME"), os.environ.get("BROWSERSTACK_ACCESS_KEY"))

        r = s.get(f"https://api.browserstack.com/automate/builds.json?limit=100")
        builds = json.loads(r.text)

        # Save all build IDs with the specified unique_id
        build_ids = []
        for build in builds:
            # print("build:", build)
            if unique_id in build['automation_build']['name']:
                build_ids.append(build['automation_build']['hashed_id'])
        # print(build_ids)

        # Save all relevant session IDs
        session_ids = []
        for build_id in build_ids:
            r = s.get(f"https://api.browserstack.com/automate/builds/{build_id}/sessions.json")
            sessions = json.loads(r.text)
            for session in sessions:
                # print("session:", session)
                session_ids.append(session['automation_session']['hashed_id'])
        # print(session_ids)

        return session_ids


    # Parse the relevant User-Agent header to detect the browser version
    def detect_mobile_browser_version(self, session_id):
        s = requests.Session()
        s.auth = (os.environ.get("BROWSERSTACK_USERNAME"), os.environ.get("BROWSERSTACK_ACCESS_KEY"))

        try:
            r = s.get(f"https://api.browserstack.com/automate/sessions/{session_id}/networklogs")
            response = json.loads(r.text)

            logs = response["log"]["entries"]
            user_agent = None
            for log in logs:
                found = False
                log_headers = log["request"]["headers"]
                for header in log_headers:
                    # printing host for visibility
                    # if header["name"] == "Host":
                    #     print(header)
                    if header["name"] == "User-Agent":
                        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/User-Agent
                        # "Mozilla/5.0 is the general token that says that the browser is Mozilla-compatible. 
                        # For historical reasons, almost every browser today sends it"
                        if "Mozilla/5.0" not in header["value"]:
                            # print("skipping", header["value"])
                            continue
                        else:
                            user_agent = header["value"]
                            found = True
                            break
                if found:
                    break
            browser_family = parse(user_agent).browser.family
            browser_version_str = parse(user_agent).browser.version_string
            browser_version = browser_family + " " + browser_version_str
            return browser_version
        except Exception as e:
            print(f"Exception (detect_mobile_browser_version): {e}")
        return None


    # Get the output directory for the build
    def get_build_dir(self, session_id):
        base_dir = self.config.browserstack_runner.output_analyzer.output_directory

        s = requests.Session()
        s.auth = (os.environ.get("BROWSERSTACK_USERNAME"), os.environ.get("BROWSERSTACK_ACCESS_KEY"))
        
        try:
            r = s.get(f"https://api.browserstack.com/automate/sessions/{session_id}.json")
            response = json.loads(r.text)

            build_name = response['automation_session']['build_name'].split(' ')[0]
        except Exception as e:
            print(f"Exception (get_build_dir); {e}")

        return f"{base_dir}/{build_name}"
    

    # Write an error to a log file
    def save_error(self, session_id, error_msg):
        base_dir = self.config.browserstack_runner.output_analyzer.output_directory
        errors_dir = f"{base_dir}/errors"

        if not os.path.exists(errors_dir):
            os.makedirs(errors_dir)

        with open(f"{errors_dir}/{session_id}.txt", "a") as f:
            f.write(f"{datetime.now()} ERROR: {error_msg}\n")


    # Save information about a session
    def save_session_info(self, session_id):
        s = requests.Session()
        s.auth = (os.environ.get("BROWSERSTACK_USERNAME"), os.environ.get("BROWSERSTACK_ACCESS_KEY"))

        try:
            r = s.get(f"https://api.browserstack.com/automate/sessions/{session_id}.json")
            response = json.loads(r.text)
        except Exception as e:
            print(f"Bad response (save_session_info): {e}")
        
        automation_session = response['automation_session']

        output = dict()
        output['build_name'] = automation_session['build_name']
        output['public_url'] = automation_session['public_url']
        output['created_at'] = automation_session['created_at']
        output['duration'] = automation_session['duration']

        # contains information about the device
        device_info = dict()
        device_info["device"] = automation_session["device"]
        device_info["os"] = automation_session["os"]
        device_info["os_version"] = automation_session["os_version"]
        device_info["browser"] = automation_session["browser"]
        device_info["browser_version"] = automation_session["browser_version"]
        if device_info["browser_version"] is None:
            device_info["browser_version"] = self.detect_mobile_browser_version(session_id)
        output["device_info"] = device_info

        build_dir = self.get_build_dir(session_id)
        output_dir = f"{build_dir}/{session_id}"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(f"{output_dir}/session.json", "w") as f:
            json.dump(output, f, indent=4)
    

    # Save the outcome of our tests based on a session-id
    def save_outcome_session_id(self, session_id):
        print(f'Gathering information about session_id "{session_id}"...')
        build_dir = self.get_build_dir(session_id)

        s = requests.Session()
        s.auth = (os.environ.get("BROWSERSTACK_USERNAME"), os.environ.get("BROWSERSTACK_ACCESS_KEY"))

        # Check if session ID is valid
        r = s.get(f"https://api.browserstack.com/automate/sessions/{session_id}/logs")
        response_lines = r.text.splitlines()

        # Add basic session info if we haven't already
        session_info_dir = f"{build_dir}/{session_id}/session.json"
        if not os.path.exists(session_info_dir):
            self.save_session_info(session_id)

        # We are detecting the following fields from the logs:
        # REQUEST for /url
        # RESPONSE from the /execute/sync REQUEST
        output = dict() # Contains output for all URLs
        current_entry = dict() # used to record the current url
        execute_sync_req_detected = False

        for line in response_lines:
            if "REQUEST" in line:
                # Detect the REQUEST for /url
                if "/url" in line: 
                    segments = line.split(' ')
                    json_str = ' '.join(segments[7:])
                    try:
                        json_data = json.loads(json_str)
                        current_entry["url"] = json_data["url"]
                    except Exception as e:
                        print(f"Exception in REQUEST (save_outcome_session_id): {e}")
                        continue
                # Detect the REQUEST for /execute/sync (the outcome we are sending to BrowserStack)
                elif "/execute/sync" in line:
                    execute_sync_req_detected = True # indicates that the next RESPONSE should be interpreted as important (containing the outcome)
            
            elif "RESPONSE" in line:
                # Detect the RESPONSE after the /execute/sync request
                if execute_sync_req_detected:
                    segments = line.split(' ')
                    json_str = ' '.join(segments[3:])
                    try:
                        json_data = json.loads(json_str)
                        automation_session = json.loads(json_data['value'].split('"automation_session":')[-1][:-1])
                        # print(automation_session)
                        current_entry["outcome"] = {
                            "status": automation_session["status"],
                            "reason": automation_session["reason"]
                        }
                        output[current_entry["url"]] = current_entry["outcome"]
                    except Exception as e:
                        print(f"Exception in RESPONSE (save_outcome_session_id): {e}")
                        continue
                    execute_sync_req_detected = False

        # Create directories if they do not exist
        output_dir = f"{build_dir}/{session_id}"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(f"{output_dir}/outcomes.json", "w") as f:
            json.dump(output, f, indent=4)

        # print(output)
        print(f"Check {output_dir}/outcomes.json for the output.\n")

    
    # Save the outcome of our tests based on a unique string ID in the title of the relevant builds
    def save_outcome_unique_id(self, unique_id):
        print(f'Gathering information about builds with unique identifier "{unique_id}"...')

        print("Scraping all relevant BrowserStack session ids...")
        session_ids = self.scrape_session_ids(unique_id)
        print(f"Total of {len(session_ids)} session ids found.")

        for count, session_id in enumerate(session_ids):
            print(f"({count+1}/{len(session_ids)}) ", end='')
            self.save_outcome_session_id(session_id)
    
    
    # Save all logs based on session id
    def save_logs_session_id(self, session_id):
        build_dir = self.get_build_dir(session_id)

        # Add basic session info if we haven't already
        session_info_dir = f"{build_dir}/{session_id}/session.json"
        if not os.path.exists(session_info_dir):
            self.save_session_info(session_id)

        # Create the directory for the session
        output_dir = f"{build_dir}/{session_id}"
        if not os.path.exists(f"{output_dir}"):
            os.makedirs(f"{output_dir}")

        s = requests.Session()
        s.auth = (os.environ.get("BROWSERSTACK_USERNAME"), os.environ.get("BROWSERSTACK_ACCESS_KEY"))

        text_logs_url = f"https://api.browserstack.com/automate/sessions/{session_id}/logs"
        network_logs_url = f"https://api.browserstack.com/automate/sessions/{session_id}/networklogs"
        console_logs_url = f"https://api.browserstack.com/automate/sessions/{session_id}/consolelogs"
        r = s.get(text_logs_url)
        # Text logs will occasionally return a 502 error; make sure the request succeeds
        err_count = 0
        while r.status_code != 200:
            print("RETURN CODE (text logs):", r.status_code, session_id)
            r = s.get(text_logs_url)
            if r.status_code == 429:
                print("TOO MANY REQUESTS (waiting a bit...)")
                time.sleep(5)
                continue
            if err_count > 5:
                self.save_error(session_id, f"Unable to get text logs for session {session_id}")
                break
            err_count += 1
        # Save text logs
        with open(f"{output_dir}/text_logs.txt", "w", encoding='utf-8') as f:
            content = remove_empty_lines(r.text)
            f.write(content)

        r = s.get(network_logs_url)
        # Ensure request succeeds
        err_count = 0
        while r.status_code != 200:
            print("RETURN CODE (network logs):", r.status_code, session_id)
            r = s.get(network_logs_url)
            if r.status_code == 429:
                print("TOO MANY REQUESTS (waiting a bit...)")
                time.sleep(5)
                continue
            if err_count > 5:
                self.save_error(session_id, f"Unable to get network logs for session {session_id}")
                break
            err_count += 1
        # Save network logs
        with open(f"{output_dir}/network_logs.txt", "w", encoding='utf-8') as f:
            content = remove_empty_lines(r.text)
            f.write(content)

        r = s.get(console_logs_url)
        # Ensure request succeeds
        err_count = 0
        while r.status_code != 200:
            print("RETURN CODE (console logs):", r.status_code, session_id)
            r = s.get(console_logs_url)
            if r.status_code == 429:
                print("TOO MANY REQUESTS (waiting a bit...)")
                time.sleep(5)
                continue
            if err_count > 5:
                self.save_error(session_id, f"Unable to get console logs for session {session_id}")
                break
            err_count += 1
        # Save console logs
        with open(f"{output_dir}/console_logs.txt", "w", encoding='utf-8') as f:
            content = remove_empty_lines(r.text)
            f.write(content)
        
        print(f"Check {output_dir}/ for saved output.")


    # Save all logs based on unique id
    def save_logs_unique_id(self, unique_id):
        print(f'Gathering information about builds with unique identifier "{unique_id}"...')

        print("Scraping all relevant BrowserStack session ids...")
        session_ids = self.scrape_session_ids(unique_id)
        print(f"Total of {len(session_ids)} session ids found.")

        for count, session_id in enumerate(session_ids):
            print(f"({count+1}/{len(session_ids)}) ", end='')
            self.save_logs_session_id(session_id)