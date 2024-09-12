import json
import csv
import os
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options as ChromeOptions


NUM_URLS = 3 # The most recent number of URLs from phishtank.org
target_urls = ['https://example.com']

# Get updated list of phishing URLs from phishtank.org
print("Retrieving updated list of phishing URLs from phishtank.org...")
os.system("curl -L -s http://data.phishtank.com/data/online-valid.csv.gz -o online-valid.csv.gz")
updated = os.system("gzip -d --force online-valid.csv.gz")
if updated == 0: 
    print("Success.")
    with open('online-valid.csv', mode='r', encoding='latin-1', newline='') as file:
        csv_reader = csv.reader(file)
        # Skip header row
        header = next(csv_reader)

        for index, row in enumerate(csv_reader):
            if index >= NUM_URLS-1:
                break
            target_urls.append(row[1])
            print(f"Added URL to targets: {row[1]}")
elif os.path.exists('online-valid.csv'):
    print("Unable to update data from phishtank.org...")
    os.system("rm online-valid.csv.gz")
    with open('online-valid.csv', mode='r', encoding='latin-1', newline='') as file:
        csv_reader = csv.reader(file)
        # Skip header row
        header = next(csv_reader)
        for index, row in enumerate(csv_reader):
            if index == 0:
                print(f"Using last saved file from {row[3]}")
            if index >= NUM_URLS-1:
                break
            target_urls.append(row[1])
            print(f"Added URL to targets: {row[1]}")
elif len(target_urls) != 0:
    print("No previous file from phishtank.org found, using the manually specified URLs inputted.")
else:
    print("No previous file found. Please manually download the csv file from phishtank.org or manually specify target_urls in the script.")
print("Target URLs specified:", target_urls)


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
