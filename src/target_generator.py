import requests
import os
import json
import yaml

from dataclasses import dataclass
from omegaconf import DictConfig, ListConfig

from src.platforms import Platforms
from src.util import write_file_source_header

@dataclass
class TargetGenerator:
    config: DictConfig | ListConfig # return type of OmegaConf.load()

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

        assert output_mode in Platforms, "Error: OUTPUT_MODE must be among [ALL, ANDROID, IOS, WINDOWS, MACOSX]; note this function should not be being called directly."

        # Setup output location
        base_dir = self.config.target_generator.targets_directory
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
        if self.config.target_generator.custom_outfile is not None:
            output_location = self.config.target_generator.custom_outfile

        # Setup for if we are scoping browser versions
        SCOPE_BROWSER_VERSIONS = False
        if self.config.target_generator.browser_versions_file is not None:
            SCOPE_BROWSER_VERSIONS = True

        if SCOPE_BROWSER_VERSIONS:
            with open(f"{self.config.target_generator.browser_versions_file}", "r") as f:
                browser_versions = yaml.safe_load(f)
                firefox_versions_range = browser_versions["firefox_versions"]
                chrome_versions_range = browser_versions["chrome_versions"]
                edge_versions_range = browser_versions["edge_versions"]
                safari_versions_range = browser_versions["safari_versions"]
                opera_versions_range = browser_versions["opera_versions"]

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
            SINGLE_FILE = self.config.target_generator.output_as_file

            # Create the output directory; if it already exists, remove existing output
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
                    write_file_source_header("generate_targets (target_generator.py)", f)
                    yaml.dump(output, f, default_flow_style=False)
            else:
                # Separate output into files each containing only n entries
                for i in range(0, len(output), self.config.target_generator.entries_per_file):
                    batch = output[i:i+self.config.target_generator.entries_per_file]
                    file_index = i // self.config.target_generator.entries_per_file
                    with open(f"{output_location}/{file_index}.yml", "w") as f:
                        write_file_source_header("generate_targets (target_generator.py)", f)
                        yaml.dump(batch, f, default_flow_style=False)

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
            write_file_source_header("scope_browser_versions (target_generator.py)", f)
            yaml.dump(data, f)