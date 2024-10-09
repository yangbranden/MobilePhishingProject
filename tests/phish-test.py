import json
import os
import sys
import time
import requests # to get raw logs and network logs
import yaml # to get username and access key
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions

windows_browsers_xpaths = { # deprecated
    "Microsoft Edge": '//*[@id="Wrapper"]/div/div[2]/h1',
    "Google Chrome": '/html/body/div/div[1]/div[2]/p/a',
    "Mozilla Firefox": '//*[@id="errorPageContainer"]',
    "Opera": '//*[@id="body"]/div/div[3]/h1'    
}

browsers_blocked_message = {
    "Microsoft Edge": 'This site has been reported as unsafe',
    
    "Mozilla Firefox (1)": 'Firefox blocked this page because it may trick you into doing something dangerous like installing software or revealing personal information like passwords or credit cards.', # Deceptive site ahead
    "Mozilla Firefox (2)": 'The page you are trying to view cannot be shown because the authenticity of the received data could not be verified.', # Secure Connection Failed
    "Mozilla Firefox (3)": 'Deceptive site issue', # Android Firefox
    
    "Google Chrome (1)": 'Attackers might be trying to steal your information from', # Your connection is not private
    "Google Chrome (2)": 'Deceptive site ahead',
    
    # Safari does not loads up any page when site is blocked.
    # driver.page_source remains at the previously visited page. So this method does not work for Safari.
    # need to figure out how to fix this. maybe checking previously_visited_url == driver.current_url ??
    
    "Safari (1)": "to steal your personal or financial information.", # This Connection Is Not Private
    "Safari (2)": "Deceptive Website Warning",

    "Samsung Browser": "Attackers might be trying to steal your information from" # Your connection is not private
}

def get_text_logs(username, access_key, build_id, session_id):
    get_text_logs_url = f"https://www.browserstack.com/automate/builds/{build_id}/sessions/{session_id}/logs"
    response = requests.get(get_text_logs_url, auth=(username, access_key))
    
    return response.text
    
    
    
def get_network_logs(username, access_key, build_id, session_id):
    get_network_logs_url = f"https://www.browserstack.com/automate/builds/{build_id}/sessions/{session_id}/networklogs"
    response = requests.get(get_network_logs_url, auth=(username, access_key))
    
    return response.text

# get the username and access key from the browserstack.yml file
with open('./browserstack.yml', 'r') as file:
    config = yaml.safe_load(file)

username = config['userName']
access_key = config['accessKey']

if username == "${BROWSERSTACK_USERNAME}":
    username = os.getenv('BROWSERSTACK_USERNAME')
if access_key == "${BROWSERSTACK_ACCESS_KEY}":
    access_key = os.getenv('BROWSERSTACK_ACCESS_KEY')


phishing_urls = [] # can explicitly specify URLs here as well
urls_file = './urls/latest.yml' if len(sys.argv) < 2 else sys.argv[1]

# Read our specified set of phishing URLs
with open(urls_file, 'r', encoding='latin-1') as f:
    data = yaml.safe_load(f)
    phishing_urls = data["urls"]
    print(phishing_urls)

print("PHISHING URLs:", phishing_urls)

# Output will be list of length phishing_urls
outcomes = {}
for url in phishing_urls:
    outcomes[url] = ['TBD'] # WILL EDIT THIS LATER (once we have identified possible outcomes)

# The webdriver management will be handled by the browserstack-sdk
# so this will be overridden and tests will run browserstack -
# without any changes to the test files!
options = ChromeOptions()
driver = webdriver.Chrome(options=options)

for url in phishing_urls:
    isBlocked = False
    print(f"Testing {url}...")
    try:
        # Navigate to the URL
        driver.get(url) 

        # Pause on the page for a few seconds
        time.sleep(3)
            
        # Currently working on figuring out an automated way of determining the results, rather than manually sifting through the output
        # Documentation for Selenium WebDriver here: https://selenium-python.readthedocs.io/api.html
        # OUTCOME #1: blocked by browser
        # TODO

        # OUTCOME #2: blocked by web server (most likely taken down)
        # TODO

        # OUTCOME #3: allowed
        # TODO

        # ADDITIONAL OUTCOME: redirected URL
        # if url not in driver.current_url:
        #     outcomes[url].append('Redirected URL')
        
        
        # for browser in windows_browsers_xpaths:
        #     if len(driver.find_elements(By.XPATH, windows_browsers_xpaths[browser])) > 0:
        #         print(f"{browser} has blocked element on {url}")
        #         driver.execute_script(
        #         'browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"failed", "reason": "Page blocked by ' + browser + '"}}')
        #         isBlocked = True
        #         break
        # deprecated
        
        page_source = driver.page_source # accessing driver.page_source takes resource each time
            
        for browser in browsers_blocked_message:
            if browsers_blocked_message[browser] in page_source:
                print(f"{browser} has blocked {url}")
                driver.execute_script(
                'browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"failed", "reason": "Page blocked by ' + browser + '"}}')
                isBlocked = True
                break      
            
        if (isBlocked == True):
            continue
        
        driver.execute_script(
                'browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"passed", "reason": "Page loaded successfully."}}')

    except NoSuchElementException as err:
        message = f'Exception: {err.__class__} {err.msg}'
        print(message)
        driver.execute_script(
            'browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"failed", "reason": ' + json.dumps(message) + '}}')
    except WebDriverException as err: # Site Unreachable
        message = f'Exception: {err.__class__} {err.msg}'
        print(message)
        driver.execute_script(
            'browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"failed", "reason": ' + json.dumps(message) + '}}')
    except Exception as err:
        message = f'Exception: {err.__class__} {err.msg}'
        print(message)
        driver.execute_script(
            'browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"failed", "reason": ' + json.dumps(message) + '}}')

# Stop the driver
driver.quit()
