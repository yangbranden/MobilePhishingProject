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
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from browserstack_sdk import BrowserStackSdk


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
urls_file = './urls/latest.yml' if len(sys.argv) < 1 else sys.argv[0]

# Read our specified set of phishing URLs
with open(urls_file, 'r', encoding='latin-1') as f:
    data = yaml.safe_load(f)
    phishing_urls = data["urls"]

print("PHISHING URLs:", phishing_urls)

# The webdriver management will be handled by the browserstack-sdk
# so this will be overridden and tests will run browserstack -
# without any changes to the test files!
options = ChromeOptions()
driver = webdriver.Chrome(options=options)

# Detect what browser we are using and add the safe browsing flags accordingly
# platform_caps = BrowserStackSdk.get_current_platform()
browser = driver.capabilities.get("browserName", "").lower()

print("DID IT WORK:", browser)

if browser == "firefox":
    options = webdriver.FirefoxOptions()
    options.set_preference("browser.safebrowsing.malware.enabled", True)
    options.set_preference("browser.safebrowsing.phishing.enabled", True)
    options.set_preference("browser.safebrowsing.downloads.enabled", True)
    driver = webdriver.Chrome(options=options)
elif browser == "chrome":
    options = webdriver.ChromeOptions()
    chrome_prefs = {
        "safebrowsing.enabled": True,
        "safebrowsing.malware.enabled": True,
        "safebrowsing.downloads.enabled": True,
    }
    options.add_experimental_option("prefs", chrome_prefs)
    driver = webdriver.Firefox(options=options)


for count, url in enumerate(phishing_urls):
    print(f"Testing {url}...")
    try:
        # Navigate to the URL
        driver.get(url)
        
        # Save page source
        page_source = driver.page_source
        
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
