import csv
import datetime
import os
import yaml
import requests
import gzip
import shutil

from dataclasses import dataclass
from omegaconf import DictConfig, ListConfig

from src.platforms import Platforms
from src.util import write_file_source_header

@dataclass
class PhishtankFetcher:
    config: DictConfig | ListConfig # return type of OmegaConf.load()

    def fetch_phishtank(self, n=None):
        base_dir = self.config.phishtank_fetcher.urls_directory
        num_urls = n if n is not None else self.config.phishtank_fetcher.num_urls
        phishing_urls = []

        # Instead of using a shell script, we can use Python requests and gzip libraries to update sources
        r = requests.get(self.config.phishtank_fetcher.phishtank_src, stream=True)
        with open(self.config.phishtank_fetcher.gzip_path, 'wb') as f:
            f.write(r.content)
        with gzip.open(self.config.phishtank_fetcher.gzip_path, 'rb') as f_in:
            with open(self.config.phishtank_fetcher.output_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
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
        with open(self.config.phishtank_fetcher.output_path, mode='r', encoding='latin-1', newline='') as file:
            csv_reader = csv.reader(file)
            
            # Skip header row
            header = next(csv_reader)
            for index, row in enumerate(csv_reader):
                if len(phishing_urls) >= num_urls:
                    break
                phishing_urls.append(row[1])
                # print(f"Added URL to urls: {row[1]}")

        with open(f"{base_dir}/latest.yml", "w") as f:
            write_file_source_header("fetch_phishtank (fetch_phishtank.py)", f)
            last_updated = datetime.datetime.today().strftime("%Y_%m_%d_%H_%M_%S")
            data = {
                'last_updated': last_updated,
                'urls': phishing_urls
            }
            yaml.dump(data, f)