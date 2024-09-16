import requests
import os
import json

# WORK IN PROGRESS
build_id = "fd1874b5027a360593f840398eb20cdc77a21802"
session_id = "f9d342106d42c897d712cbab39249f5623e4ed79"

s = requests.Session()
s.auth = (os.environ.get("BROWSERSTACK_USERNAME"), os.environ.get("BROWSERSTACK_ACCESS_KEY"))

r = s.get(f"https://api.browserstack.com/automate/builds/{build_id}/sessions/{session_id}/networklogs")
output = json.loads(r.text)

# List all URLs visited during session
for index, log in enumerate(output["log"]["entries"]):
    print(index, log["request"]["url"])

with open("tmp.json", "w") as f:
    f.write(json.dumps(output["log"]["entries"], indent=2))

# # For example; getting the video URL
# print(output[0]["automation_session"]["selenium_logs_url"])