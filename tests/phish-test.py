import json
import csv
import os
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options as ChromeOptions


target_urls = ['https://example.com'] # can explicitly specify URLs here as well
target_file = './targets/targets-9-12.txt'

# FOR TXT FILE
with open(target_file, 'r', encoding='latin-1') as f:
    for url in f:
        target_urls.append(url.strip())

# FOR CSV FILE
# with open(target_file, 'r', encoding='latin-1') as f:
#     for url in f.read().strip().split(','):
#         target_urls.append(url)
# FOR JSON FILE
# with open(target_file, 'r', encoding='latin-1') as f:
#     for url in json.load(f):
#         target_urls.append(url)

print("TARGET URLs:", target_urls)

# The webdriver management will be handled by the browserstack-sdk
# so this will be overridden and tests will run browserstack -
# without any changes to the test files!
options = ChromeOptions()
options.set_capability('sessionName', 'Phishing Project Test')
driver = webdriver.Chrome(options=options) 

try:
    for url in target_urls:
        print(f"Testing {url}...")
        driver.get(url)
        WebDriverWait(driver, 10)
        # TODO: figure out an automated way of determining the results, rather than manually sifting through the output
        # Documentation for Selenium WebDriver here: https://selenium-python.readthedocs.io/api.html
    driver.execute_script(
        'browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"passed", "reason": "Page has been loaded successfully."}}')
except NoSuchElementException as err:
    message = 'Exception: ' + str(err.__class__) + str(err.msg)
    driver.execute_script(
        'browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"failed", "reason": ' + json.dumps(message) + '}}')
except Exception as err:
    message = 'Exception: ' + str(err.__class__) + str(err.msg)
    driver.execute_script(
        'browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"failed", "reason": ' + json.dumps(message) + '}}')
finally:
    # Stop the driver
    driver.quit()