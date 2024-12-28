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

from src.util import write_file_source_header

@dataclass
class CVESearcher:
    config: DictConfig | ListConfig # return type of OmegaConf.load()

    # WORK IN PROGRESS
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
                        url = cve_element.find_element(By.TAG_NAME, "a").get_attribute("href")
                        # Check if any keyword is present in the description
                        if any(keyword.lower() in summary.lower() for keyword in phishing_keywords):
                            print("entry found:", {"cve_id": cve_id, "summary": summary, "url": url})
                            cve_results[browser].append({"cve_id": cve_id, "summary": summary, "url": url})
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
                        url = cve_element.find_element(By.TAG_NAME, "a").get_attribute("href")
                        # Check if any keyword is present in the description
                        if any(keyword.lower() in summary.lower() for keyword in phishing_keywords):
                            print("entry found:", {"cve_id": cve_id, "summary": summary, "url": url})
                            cve_results[browser].append({"cve_id": cve_id, "summary": summary, "url": url})

        driver.quit()

        # Save the list of CVEs
        base_dir = self.config.cve_searcher.cves_directory
        os.makedirs(base_dir)
        with open(f"{base_dir}/browser_cves.yml", "w+") as f:
            yaml.dump(cve_results, f)


    # WORK IN PROGRESS
    def scrape_os_cves(self, url_source):
        # Use API to get all possible combinations of OS versions
        s = requests.Session()
        s.auth = (os.environ.get("BROWSERSTACK_USERNAME"), os.environ.get("BROWSERSTACK_ACCESS_KEY"))

        r = s.get("https://api.browserstack.com/automate/browsers.json")
        output = json.loads(r.text)

        # Find the latest versions of each OS
        latest_versions = {
            "Windows": 0.0,
            "OS X": 0.0,
            "ios": 0.0,
            "android": 0.0
        }
        for item in output:
            os = item["os"]
            if os in latest_versions:
                try:
                    detected_version = float(item["os_version"])
                    if detected_version > latest_versions[os]:
                        latest_versions[os] = detected_version
                except ValueError:
                    continue
        print("Latest versions:\n", latest_versions)

        # These do not really work; too many categorizations
        cvedetails_urls = {
            "Windows": "https://www.cvedetails.com/vulnerability-list/vendor_id-26/product_id-102217/Microsoft-Windows-11.html",
            "OS X": "https://www.cvedetails.com/vulnerability-list/vendor_id-49/product_id-156/Apple-Mac-Os-X.html",
            "ios": "https://www.cvedetails.com/version-list/49/15556/1/Apple-Iphone-Os.html",
            "android": "https://www.cvedetails.com/version-list/1224/19997/1/Google-Android.html"
        }

        # MITRE search URLs
        mitre_urls = {
            "Windows": "https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword=windows",
            "OS X": "https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword=OS%20X",
            "ios": "https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword=ios",
            "android": "https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword=android"
        }

        cve_results = {
            "Windows": [],
            "OS X": [],
            "ios": [],
            "android": []
        }

        # Keywords to search by on CVEs:
        phishing_keywords = ["spoof", "spoofing", "fake", "phishing"]

        # Use selenium to search CVEDetails website and record a list of CVEs that have the keywords in them 
        driver = webdriver.Chrome(options=ChromeOptions())

        ##########
        ### TODO
        ##########

        base_dir = self.config.cve_searcher.cves_directory
        with open(f"{base_dir}/os_cves.yml", "w+") as f:
            yaml.dump(cve_results, f)
        return
    
    def get_version_from_cve(self, CVE):
        # https://cveawg.mitre.org/api/cve/CVE-2024-40866
        url = f"https://cveawg.mitre.org/api/cve/{CVE}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            
            affected = data["containers"]["cna"]["affected"]
            for item in affected:
                versions = item["versions"]
                for version in versions:
                    if version.get("lessThan"):
                        return version["lessThan"]
        else:
            return None
    
    
    # Based on the recorded CVEs, save a list of the relevant browser versions
    def parse_browser_versions(self):
        # Load list of CVEs
        base_dir = self.config.browserstack_runner.target_generator.targets_directory
        with open(f"{base_dir}/browser_cves.yml", "r") as f:
            cve_results = yaml.safe_load(f)

        # Sort through each of the CVEs and their summaries; get the versions from them (using sets so no duplicates)
        versions = {
            "firefox": set(),
            "chrome": set(),
            "edge": set(),
            "safari": set()
        }

        # Parse versions for Firefox;
        for entry in cve_results.get("firefox", []):
            cve_id = entry["cve_id"] 
            version = self.get_version_from_cve(cve_id)
            version_str = version.split('.')[0]  # Get the major version only
            # Add the version to the Firefox set
            if version_str.isdigit():
                versions["firefox"].add(int(version_str))
        versions["firefox"] = sorted(versions["firefox"], reverse=True)
        print("Extracted Firefox Versions:", versions["firefox"])


        # Parse versions for Google Chrome;
        for entry in cve_results.get("chrome", []):
            cve_id = entry["cve_id"] 
            version = self.get_version_from_cve(cve_id)
            version_str = version.split('.')[0]  # Get the major version only
            # Add the version to the Chrome set
            if version_str.isdigit():
                versions["chrome"].add(int(version_str))
        versions["chrome"] = sorted(versions["chrome"], reverse=True)
        print("Extracted Chrome Versions:", versions["chrome"])
        
        # Parse versions for Microsoft Edge;
        for entry in cve_results.get("edge", []):
            cve_id = entry["cve_id"] 
            version = self.get_version_from_cve(cve_id)
            version_str = version.split('.')[0]  # Get the major version only
            # Add the version to the Edge set
            if version_str.isdigit():
                versions["edge"].add(int(version_str))
        versions["edge"] = sorted(versions["edge"], reverse=True)
        print("Extracted Edge Versions:", versions["edge"])

        # Parse versions for Safari;
        for entry in cve_results.get("safari", []):
            cve_id = entry["cve_id"] 
            version = self.get_version_from_cve(cve_id)
            version_str = version.split('.')[0]  # Get the major version only
            # Add the version to the safari set
            if version_str.isdigit():
                versions["safari"].add(int(version_str))
        versions["safari"] = sorted(versions["safari"], reverse=True)
        print("Extracted Safari Versions:", versions["safari"])  

        data = {
            'firefox_versions': versions["firefox"],
            'chrome_versions': versions["chrome"],
            'edge_versions': versions["edge"],
            'safari_versions': versions["safari"],
            'opera_versions': [12.16, 12.15] # There are only 2 versions of opera available on BrowserStack lol
        }

        print(data)

        # Output the versions to a file
        browser_versions_file = self.config.browserstack_runner.target_generator.browser_versions_file
        with open(browser_versions_file, "w+") as f:
            write_file_source_header("save_browser_versions (cve_searcher.py)", f)
            yaml.dump(data, f)