import csv
import datetime
import os
import yaml
import requests
import gzip
import shutil
import time

from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from dataclasses import dataclass
from omegaconf import DictConfig, ListConfig

from src.util import Platforms
from src.util import write_file_source_header

@dataclass
class PhishScraper:
    config: DictConfig | ListConfig # return type of OmegaConf.load()
    
    # Manually check phishing sites (source = PhishTank)
    def manual_phishtank(self, n=None):
        base_dir = self.config.phish_scraper.urls_directory
        num_urls = n if n is not None else self.config.phish_scraper.num_urls
        phishing_urls = []
        
        self.download_phishtank_db()
        
        options = ChromeOptions()
        driver = webdriver.Chrome(options=options)
        
        with open(self.config.phish_scraper.source_csv, mode='r', encoding='latin-1', newline='') as file:
            csv_reader = csv.reader(file)
            
            # Skip header row
            header = next(csv_reader)
            for row in csv_reader:
                if len(phishing_urls) >= num_urls:
                    break
                test_url = row[1]
                
                try:
                    print(f"Testing {test_url}...")
                    driver.get(test_url)
                    
                    choice = input("Add phishing URL? (Y/N) ")
                    if choice == "Y":
                        phishing_urls.append(test_url)
                    elif choice == "N":
                        continue
                except WebDriverException as e:
                    print(f"Network error for url {test_url}; skipping")
        
        with open(f"{base_dir}/manual.yml", "w") as f:
            write_file_source_header("manual_phishtank (phish_scraper.py)", f)
            last_updated = datetime.datetime.today().strftime("%Y_%m_%d_%H_%M_%S")
            data = {
                'last_updated': last_updated,
                'urls': phishing_urls
            }
            yaml.dump(data, f)
    

    # Updates our `latest.yml` file to contain n latest URLs from PhishTank
    def fetch_phishtank(self, n=None):
        base_dir = self.config.phish_scraper.urls_directory
        num_urls = n if n is not None else self.config.phish_scraper.num_urls
        phishing_urls = []

        self.download_phishtank_db()

        # If we already have a 'latest.yml' file containing our URLs, we want to read it and move it (change its name)
        last_updated = None
        if os.path.exists(f"{base_dir}/latest.yml"):
            with open(f"{base_dir}/latest.yml", "r") as f:
                urls_file = yaml.safe_load(f)
                last_updated = urls_file["last_updated"]
            if not os.path.exists(f"{base_dir}/old"):
                os.mkdir(f"{base_dir}/old")
            os.system(f"mv {base_dir}/latest.yml {base_dir}/old/urls_{last_updated}.yml")

        # Read the phishtank URLs file and add the n latest to our output list
        with open(self.config.phish_scraper.source_csv, mode='r', encoding='latin-1', newline='') as file:
            csv_reader = csv.reader(file)
            
            # Skip header row
            header = next(csv_reader)
            for row in csv_reader:
                if len(phishing_urls) >= num_urls:
                    break
                phishing_urls.append(row[1])
                # print(f"Added URL to urls: {row[1]}")

        with open(f"{base_dir}/latest.yml", "w") as f:
            write_file_source_header("fetch_phishtank (phish_scraper.py)", f)
            last_updated = datetime.datetime.today().strftime("%Y_%m_%d_%H_%M_%S")
            data = {
                'last_updated': last_updated,
                'urls': phishing_urls
            }
            yaml.dump(data, f)
            
    
    # Downloads the latest database from PhishTank
    def download_phishtank_db(self):
        base_dir = self.config.phish_scraper.urls_directory
        phishtank_srcs = [
            'https://data.phishtank.com/data/online-valid.csv.gz',
            'https://data.phishtank.com/data/online-valid.json.gz',
            'https://data.phishtank.com/data/online-valid.xml.gz'
        ]

        # Use Python requests and gzip libraries to update sources
        for phishtank_src in phishtank_srcs:
            gzip_name = phishtank_src.split("/")[-1]
            gzip_dir = f"{base_dir}/{gzip_name}"
            outfile = gzip_dir.split(".gz")[0]
            r = requests.get(phishtank_src, stream=True)
            with open(gzip_dir, 'wb') as f:
                f.write(r.content)
            with gzip.open(gzip_dir, 'rb') as f_in:
                with open(outfile, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove the zip file after we've extracted it
            os.remove(gzip_dir)