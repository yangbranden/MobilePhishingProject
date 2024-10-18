import requests
import json
import os

from dataclasses import dataclass
from omegaconf import DictConfig, ListConfig

@dataclass
class URLChecker:
    config: DictConfig | ListConfig # return type of OmegaConf.load()

    # Returns True if match found in Google SafeBrowsing API
    def check_google_safebrowsing(self, url):
        API_KEY = os.environ.get('GOOGLE_SAFEBROWSING_API_KEY')
        api_endpoint = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={API_KEY}"

        # Payload format for Google SafeBrowsing API
        payload = {
            "client": {
                "clientId": "yourcompanyname",
                "clientVersion": "1.0"
            },
            "threatInfo": {
                "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [
                    {"url": url}
                ]
            }
        }

        # Send the request to Google Safe Browsing API
        response = requests.post(api_endpoint, json=payload)

        # Check the response status code
        if response.status_code == 200:
            result = response.json()
            # Check if any threats were found
            if "matches" in result:
                print(f"Match found for {url}; not safe.")
                print(f"Threat info: {json.dumps(result, indent=2)}")
                return True
            else:
                print(f"The URL {url} is safe.")
                return False
        else:
            print(f"Error: Unable to check the URL. Status code: {response.status_code}")
            return False
    
    #  
    def check_phishtank(self):
        return
    
    # OCSP
    def check_certificate(self):
        return