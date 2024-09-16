from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

output_file = "ALL.yml"

# Setup webdriver browser options
options = ChromeOptions()
# options.add_argument('--headless')  # Run headless mode (no GUI)

# Initialize WebDriver
driver = webdriver.Chrome(options=options)

try:
    # Navigate to the webpage
    driver.get('https://www.browserstack.com/list-of-browsers-and-platforms/automate')

    # Print the contents of the webpage
    # page_source = driver.page_source
    # print(page_source)

    # ANDROID
    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, 'device-list-doc')))
    android_devices = []
    device_lists = driver.find_elements(By.CLASS_NAME, 'device-list-doc')
    vendors_elements = driver.find_elements(By.CLASS_NAME, 'device-name-doc')
    vendors = []
    for vendor in vendors_elements:
        vendors.append(vendor.text)
    vendors.remove("Others")
    print("VENDORS:", vendors)
    vendor_index = 0
    for device_list in device_lists:
        print("found device-list-doc:", device_list)
        device_entries = device_list.find_elements(By.TAG_NAME, 'li')
        for device_entry in device_entries:
            device = device_entry.text
            device = device.split("\n")[0]
            if device == vendors[vendor_index]:
                continue
            device = vendors[vendor_index] + " " + device
            android_devices.append(device)
        vendor_index += 1
    print(android_devices)
    # with open(output_file, "w") as f:
    #     f.write("ANDROID DEVICES\n")

    # SLEEP
    # for i in range(20, 0, -1):
    #     print(f"Sleeping ({i})...")
    #     time.sleep(1)
except Exception as e:
    print(e)
finally:
    # Clean up and close the browser
    driver.quit()
