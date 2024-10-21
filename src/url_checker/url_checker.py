import requests
import json
import os
import csv
import ssl
import socket
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.x509.ocsp import OCSPRequestBuilder

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
    

    # Returns certificate for URL
    def get_certificate(self, hostname, port=443):
        conn = ssl.create_default_context().wrap_socket(
            socket.socket(socket.AF_INET), server_hostname=hostname
        )
        conn.connect((hostname, port))
        cert = conn.getpeercert(binary_form=True)
        conn.close()
        return x509.load_der_x509_certificate(cert, default_backend())


    # OCSP; Returns True if certificate is valid, False if certificate is invalid or unknown
    def check_ocsp(self, url):
        cert = self.get_certificate(url)

        # Get the OCSP responder URL
        ocsp_url = None
        for ext in cert.extensions:
            if isinstance(ext.value, x509.AuthorityInformationAccess):
                for access_desc in ext.value:
                    if access_desc.access_method == x509.AuthorityInformationAccessOID.OCSP:
                        ocsp_url = access_desc.access_location.value
        if not ocsp_url:
            print("No OCSP URL found.")
            return False

        # Create the OCSP request
        builder = OCSPRequestBuilder()
        builder = builder.add_certificate(cert, cert, hashes.SHA1()) # TODO: FIGURE OUT HOW TO GET THE ISSUER CERT
        ocsp_req = builder.build()

        # Send the OCSP request
        headers = {'Content-Type': 'application/ocsp-request'}
        response = requests.post(ocsp_url, data=ocsp_req.public_bytes("PEM"), headers=headers) # TODO: ENCODING NEEDS TO BE SPECIFIED

        # Parse the OCSP response
        ocsp_response = x509.ocsp.load_der_ocsp_response(response.content)
        status = ocsp_response.certificate_status
        if status == x509.ocsp.OCSPCertStatus.GOOD:
            print("Certificate status (OCSP): GOOD")
            return True
        elif status == x509.ocsp.OCSPCertStatus.REVOKED:
            print("Certificate status (OCSP): REVOKED")
            return False
        else:
            print("Certificate status (OCSP): UNKNOWN")
            return False


    # CRL; Returns True if CRL status is good, False if CRL status is revoked or unknown
    def check_crl(self, url):
        cert = self.get_certificate(url)

        crl_urls = []
        for ext in cert.extensions:
            if isinstance(ext.value, x509.CRLDistributionPoints):
                for dist_point in ext.value:
                    if dist_point.full_name:
                        for name in dist_point.full_name:
                            crl_urls.append(name.value)
        if not crl_urls:
            print("No CRL URLs found.")
            return False

        # For this example, we'll just check the first CRL URL
        crl_url = crl_urls[0]
        print(f"Fetching CRL from {crl_url}...")

        # Download the CRL
        response = requests.get(crl_url)
        if response.status_code != 200:
            print(f"Failed to download CRL: {response.status_code}")
            return False

        crl = x509.load_der_x509_crl(response.content, default_backend())

        # Check if the certificate is revoked
        for revoked_cert in crl:
            if revoked_cert.serial_number == cert.serial_number:
                print("Certificate status (CRL): REVOKED")
                return False

        print("Certificate status (CRL): GOOD")
        return True
    

    def check_all(self, url):
        print("Checking all sources...")
        print("----------------------------------------")
        print("Google SafeBrowsing...")
        self.check_google_safebrowsing(url)
        print("----------------------------------------")
        print("PhishTank...")
        self.check_phishtank(url)
        print("----------------------------------------")
        print("OCSP...")
        self.check_ocsp(url)
        print("----------------------------------------")
        print("CRL...")
        self.check_crl(url)
        print("----------------------------------------")