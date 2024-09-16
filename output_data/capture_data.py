import requests
import os
import json

# WORK IN PROGRESS
build_id = "072258cb2bc28d2fbfc5b0f7a694864bce89ca67"
# session_id = "49c7ef77ffa758424fc2f54f0b6534b7700c9edc"

s = requests.Session()
s.auth = (os.environ.get("BROWSERSTACK_USERNAME"), os.environ.get("BROWSERSTACK_ACCESS_KEY"))

r = s.get(f"https://api.browserstack.com/automate/builds/{build_id}/sessions.json")
output = json.loads(r.text)

with open("tmp.json", "w") as f:
    f.write(json.dumps(output))

# For example; getting the video URL
print(output[0]["automation_session"]["video_url"])