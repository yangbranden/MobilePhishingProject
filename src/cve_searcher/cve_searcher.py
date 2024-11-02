import requests
import os
import json
import yaml
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions

from dataclasses import dataclass
from omegaconf import DictConfig, ListConfig

@dataclass
class CVESearcher:
    config: DictConfig | ListConfig # return type of OmegaConf.load()

    def scrape_browser_cves(self, url_source):
        # Use API to get all possible combinations of browser versions
        s = requests.Session()
        s.auth = (os.environ.get("BROWSERSTACK_USERNAME"), os.environ.get("BROWSERSTACK_ACCESS_KEY"))

        r = s.get("https://api.browserstack.com/automate/browsers.json")
        output = json.loads(r.text)

        # Find the latest versions of each browser
        latest_versions = {
            'firefox': 0.0,
            'chrome': 0.0,
            'edge': 0.0,
            'safari': 0.0,
            'opera': 0.0
        }
        for item in output:
            browser = item["browser"]
            if browser in latest_versions:
                try:
                    detected_version = float(item["browser_version"])
                    if detected_version > latest_versions[browser]:
                        latest_versions[browser] = detected_version
                except ValueError:
                    continue
        print("Latest versions:\n", latest_versions)

        cvedetails_urls = {
            "firefox": "https://www.cvedetails.com/vulnerability-list/vendor_id-452/product_id-3264/Mozilla-Firefox.html",
            "chrome": "https://www.cvedetails.com/vulnerability-list/vendor_id-1224/product_id-15031/Google-Chrome.html",
            "edge": "https://www.cvedetails.com/vulnerability-list/vendor_id-26/product_id-32367/Microsoft-Edge.html",
            "safari": "https://www.cvedetails.com/vulnerability-list/vendor_id-49/product_id-2935/Apple-Safari.html"
        }

        # MITRE search URLs
        mitre_urls = {
            "firefox": "https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword=firefox",
            "chrome": "https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword=chrome",
            "edge": "https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword=microsoft%20edge",
            "safari": "https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword=safari"
        }

        cve_results = {
            "firefox": [],
            "chrome": [],
            "edge": [],
            "safari": []
        }

        # Keywords to search by on CVEs:
        phishing_keywords = ["spoof", "spoofing", "fake", "phishing"]

        # Use selenium to search CVEDetails website and record a list of CVEs that have the keywords in them 
        driver = webdriver.Chrome(options=ChromeOptions())
        
        if url_source == "cvedetails":
            # Search each CVEdetails page
            for browser, url in cvedetails_urls.items():
                # Visit the search page
                driver.get(url)
                wait = WebDriverWait(driver, 30)
                # Keep searching for CVEs until specific year
                target_cve_year = 2022
                cve_year = datetime.now().year
                while cve_year > target_cve_year:
                    # Find all CVE elements on the page
                    cve_elements = driver.find_elements(By.XPATH, "//div[@id='searchresults']/div[@data-tsvfield='cveinfo']")
                    for cve_element in cve_elements:
                        # Parse the cve_element
                        lines = cve_element.text.split("\n")  # Split by new lines
                        cve_id = lines[0].strip()
                        cve_year = int(cve_id.split('-')[1])
                        summary = lines[1].strip()
                        if cve_year <= target_cve_year:
                            break
                        # print((cve_id, summary))
                        # Check if any keyword is present in the description
                        if any(keyword.lower() in summary.lower() for keyword in phishing_keywords):
                            print("entry found:", (cve_id, summary))
                            cve_results[browser].append((cve_id, summary))
                    if cve_year <= target_cve_year:
                        break
                    # Go to the next page
                    next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@title='Next page']")))
                    next_button.click()
        elif url_source == "mitre":
            for browser, url in mitre_urls.items():
                # Visit the search page
                driver.get(url)
                wait = WebDriverWait(driver, 30)
                # Keep searching for CVEs until specific year
                target_cve_year = 2022
                cve_year = datetime.now().year
                while cve_year > target_cve_year:
                    cve_elements = driver.find_elements(By.XPATH, "//div[@id='TableWithRules']/table/tbody/tr")
                    for cve_element in cve_elements:
                        # Parse the cve_element
                        lines = cve_element.text.split(" ")  # Split by spaces
                        cve_id = lines[0].strip()
                        cve_year = int(cve_id.split('-')[1])
                        summary = ' '.join(lines[1:])

                        if cve_year <= target_cve_year:
                            break
                        # print((cve_id, summary))
                        # Check if any keyword is present in the description
                        if any(keyword.lower() in summary.lower() for keyword in phishing_keywords):
                            print("entry found:", (cve_id, summary))
                            cve_results[browser].append((cve_id, summary))

        driver.quit()

        # Save the list of CVEs
        base_dir = self.config.browserstack_runner.target_generator.targets_directory
        with open(f"{base_dir}/relevant_cves.yml", "w+") as f:
            yaml.dump(cve_results, f)

    def scrape_os_cves(self):
        # TODO
        return
    
    def save_browser_versions(self):
        # Load list of CVEs
        base_dir = self.config.browserstack_runner.target_generator.targets_directory
        with open(f"{base_dir}/relevant_cves.yml", "w+") as f:
            cve_results = yaml.safe_load(f)

        # Sort through each of the CVEs and their summaries; get the versions from them (using sets so no duplicates)
        versions = {
            "firefox": set(),
            "chrome": set(),
            "edge": set(),
            "safari": set()
        }

        # Parse versions for Firefox; format is "Firefox < ###.#"
        for cve_id, description in cve_results["firefox"]:
            # Find the starting index of "Firefox < "
            start_index = description.find("Firefox < ")
            # If the format "Firefox < " is found in the description
            if start_index != -1:
                # Extract the version by slicing the string after "Firefox < "
                version_part = description[start_index + len("Firefox < "):]  
                # Find the end of the version number, which is usually the first space or period afterward
                end_index = version_part.find(" ")
                if end_index == -1:  # If no space, take the whole part
                    end_index = len(version_part)
                version_str = version_part[:end_index].rstrip(",.")
                # Add the version to the Firefox set
                if version_str.isdigit():
                    versions["firefox"].add(int(version_str))
        versions["firefox"] = sorted(versions["firefox"], reverse=True)
        print("Extracted Firefox Versions:", versions["firefox"])


        # Parse versions for Google Chrome; format is "Google Chrome prior to ###.#"
        for cve_id, description in cve_results["chrome"]:
            if "Google Chrome prior to" in description:
                # Extract the version substring following "Google Chrome prior to "
                start_index = description.index("Google Chrome prior to") + len("Google Chrome prior to ")
                version_part = description[start_index:].split('.')[0]  # Get the major version before the first period
                # Convert it to an integer
                version_number = int(version_part)
                # Add it to the set of Chrome versions
                versions["chrome"].add(version_number)
        # Convert the set to a sorted list
        versions["chrome"] = sorted(versions["chrome"], reverse=True)
        print("Extracted Chrome Versions:", versions["chrome"])


        # (Versions for Microsoft Edge must be parsed manually; summary texts do not specify, but it does show on CVEdetails website)


        # (Versions for Safari mustbe parsed manually; inconsistent summary text format)


        data = {
            'firefox_versions': versions["firefox"],
            'chrome_versions': versions["chrome"],
            'edge_versions': [],
            'safari_versions': [],
            'opera_versions': [12.16, 12.15] # There are only 2 versions of opera available on BrowserStack lol
        }

        print(data)

        # Output the versions to a file
        # browser_versions_file = self.config.browserstack_runner.target_generator.browser_versions_file
        # with open(browser_versions_file, "w+") as f:
        #     # write_file_source_header("scope_browser_versions (browserstack_runner.py)", f)
        #     yaml.dump(data, f)