# created just for a test purpose
# feel free to delete this file, and inegrate this into cve_seraecher.py, if everything seems okay

import requests
import yaml

def get_cve_version(CVE):
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
    
def test():
    with open(f"D:\\All\\Project\\SEFCOM\\MobilePhishingProject\\src\\cve_searcher\\cves\\browser_cves.yml", "r") as f:
        cve_results = yaml.safe_load(f)

    # Sort through each of the CVEs and their summaries; get the versions from them (using sets so no duplicates)
    versions = {
        "firefox": set(),
        "chrome": set(),
        "edge": set(),
        "safari": set()
    }
    
    for entry in cve_results.get("edge", []):
            cve_id = entry["cve_id"] 
            print(f"Getting version for {cve_id}")
            version = get_cve_version(cve_id)
            print(version)
    for entry in cve_results.get("safari", []):
            cve_id = entry["cve_id"] 
            print(f"Getting version for {cve_id}")
            version = get_cve_version(cve_id)
            print(version)
            
            
test()