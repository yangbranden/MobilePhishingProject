import requests
import os

# WORK IN PROGRESS
build_id = "aaa"

s = requests.Session()
s.auth = (os.environ.get("BROWSERSTACK_USERNAME"), os.environ.get("BROWSERSTACK_ACCESS_KEY"))

r = s.get(f"https://api.browserstack.com/automate/builds/{build_id}/sessions.json")