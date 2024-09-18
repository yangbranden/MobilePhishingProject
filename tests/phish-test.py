import json
import csv
import os
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions


phishing_urls = [] # can explicitly specify URLs here as well
urls_file = './urls/urls_2024-09-16.txt'

# FOR TXT FILE
with open(urls_file, 'r', encoding='latin-1') as f:
    for url in f:
        phishing_urls.append(url.strip())

# FOR CSV FILE
# with open(urls_file, 'r', encoding='latin-1') as f:
#     for url in f.read().strip().split(','):
#         phishing_urls.append(url)
# FOR JSON FILE
# with open(urls_file, 'r', encoding='latin-1') as f:
#     for url in json.load(f):
#         phishing_urls.append(url)

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
        
        
        # check if page has '/html/body/div[1]/div/div[2]/h1 (Microsoft Edge's: This site has been reported as unsafe)'  
        if len(driver.find_elements(By.XPATH, '/html/body/div[1]/div/div[2]/h1')) > 0:
                print(f"Found Microsoft Edge 'This site has been reported as unsafe' element on {url}")
                driver.execute_script(
                'browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"failed", "reason": "Page blocked by Microsoft Edge."}}')
        else:
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