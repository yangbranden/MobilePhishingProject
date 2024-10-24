import requests
import json
import os
import csv
import shutil
from pki_tools import Certificate, Chain, is_revoked, RevokeMode
from get_certificate_chain.download import SSLCertificateChainDownloader

from dataclasses import dataclass
from omegaconf import DictConfig, ListConfig

from src.fetch_phishtank import PhishtankFetcher

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
        # print(response.content)

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
    

    # Returns True if URL is found in PhishTank; just does a Python 'str in str' check
    def check_phishtank(self, url):
        x = PhishtankFetcher(config=self.config)
        x.download_phishtank_db()

        # Open the PhishTank source csv file and check if our url is in it
        with open(self.config.phishtank_fetcher.source_csv, mode='r', encoding='latin-1', newline='') as file:
            csv_reader = csv.reader(file)
            
            # Skip header row
            header = next(csv_reader)
            for row in csv_reader:
                if url in row[1]:
                    print("URL found in PhishTank list;")
                    print(row)
                    return True

        return False


    # Returns the certificate chain given a hostname
    def get_cert_chain(self, hostname):
        certs_dir = f"./tmp/{hostname}"

        # Try to download the certificates
        try:
            downloader = SSLCertificateChainDownloader(certs_dir)
            downloader.run({'host': hostname})
        except Exception as e:
            print(e)

        cert_files = []
        for root, dirs, files in os.walk(certs_dir):
            for file in files:
                cert_files.append(os.path.join(root, file))

        certs = []
        for cert_file in cert_files:
            certs.append(Certificate.from_file(cert_file))
        
        return Chain(certificates=certs)

    
    # Returns True if certificate is valid, False if certificate is invalid or unknown
    def check_certificate(self, hostname, revoke_mode: RevokeMode):
        valid = False

        # Fetch the certificate chain dynamically from the server
        chain = self.get_cert_chain(hostname)

        # Fetch the server's certificate
        server_cert = Certificate.from_server(f"https://{hostname}")

        # Perform revocation checks
        if not is_revoked(server_cert, chain, revoke_mode=revoke_mode):
            print("Certificate is not revoked")
            valid = True
        else:
            print("Certificate is revoked")
            valid = False

        # Remove the certificate files afterwards
        if os.path.exists(f"./tmp/{hostname}") and os.path.isdir(f"./tmp/{hostname}"):
            shutil.rmtree(f"./tmp/{hostname}")

        return valid


    # Online Certificate Status Protocol
    def check_ocsp(self, hostname):
        self.check_certificate(hostname, RevokeMode.OCSP_ONLY)


    # Certificate Revocation List
    def check_crl(self, hostname):        
        self.check_certificate(hostname, RevokeMode.CRL_ONLY)