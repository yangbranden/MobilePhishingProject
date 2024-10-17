import requests
import os
import json

# WORK IN PROGRESS
# build_id = "fd1874b5027a360593f840398eb20cdc77a21802"
# session_id = "f9d342106d42c897d712cbab39249f5623e4ed79"
unique_id = "HGWhwxQ6"

s = requests.Session()
s.auth = (os.environ.get("BROWSERSTACK_USERNAME"), os.environ.get("BROWSERSTACK_ACCESS_KEY"))

# Relevant API requests (https://api.browserstack.com/automate):
# /builds.json?limit=100&offset=0
# /sessions/{session_id}/logs
# /sessions/{session_id}/networklogs
# /sessions/{session_id}/consolelogs
# /sessions/{session_id}/seleniumlogs (doesn't work I think)
# /sessions/{session_id}/appiumlogs
# /sessions/{session_id}/telemetrylogs
# r = s.get(f"https://api.browserstack.com/automate/builds/{build_id}/sessions/{session_id}/networklogs")
r = s.get(f"https://api.browserstack.com/automate/builds.json?limit=100")
builds = json.loads(r.text)

# Save all build IDs with the specified unique_id
build_ids = []
for build in builds:
    # print("build:", build)
    if unique_id in build['automation_build']['name']:
        build_ids.append(build['automation_build']['hashed_id'])

# print(build_ids)

# Save all relevant session IDs
session_ids = []
for build_id in build_ids:
    r = s.get(f"https://api.browserstack.com/automate/builds/{build_id}/sessions.json")
    sessions = json.loads(r.text)
    for session in sessions:
        # print("session:", session)
        session_ids.append(session['automation_session']['hashed_id'])

print(session_ids)

# List all URLs visited during session
# for index, log in enumerate(output["log"]["entries"]):
#     print(index, log["request"]["url"])

# with open("tmp.json", "w") as f:
#     f.write(json.dumps(output["log"]["entries"], indent=2))

# # For example; getting the video URL
# print(output[0]["automation_session"]["selenium_logs_url"])