########################################
# NOTE: This is specifically for the mobile tests, since we don't have the browser version readily available from the API
# For desktop browser tests, we don't need to do this; we can read 'browser_version' from the API (which is not available on mobile tests)
########################################

import requests
import os
import json
import httpagentparser # this doesn't detect samsung browser; look for different parser library

build_ids = []
session_ids = []
build_name_str_identifier = "iOS Targets"
hash_save_file = "./output_data/android_session_hashes.txt"
headers_save_file = "./output_data/android_useragent_headers2.txt"

user_agents = set() # use set so there are no duplicates

hashes_saved = False
if os.path.exists(hash_save_file):
    with open(hash_save_file, "r") as f:
        for hash in f:
            session_ids.append(hash)
    hashes_saved = True
headers_saved = False
if os.path.exists(headers_save_file):
    with open(headers_save_file, "r") as f:
        for hash in f:
            session_ids.append(hash)
    headers_saved = True

s = requests.Session()
s.auth = (os.environ.get("BROWSERSTACK_USERNAME"), os.environ.get("BROWSERSTACK_ACCESS_KEY"))

if not hashes_saved:
    # get all build ids
    # (iterate over the last 1000 builds and find those relevant to the test)
    for i in range(10):
        r = s.get(f"https://api.browserstack.com/automate/builds.json?limit={100}&offset={i*100}")
        output = json.loads(r.text)
        for entry in output:
            build = entry["automation_build"]
            if build_name_str_identifier in build["name"]:
                print(build["name"], build["hashed_id"])
                build_ids.append(build["hashed_id"])
    # print("Total # of build ids:", len(build_ids))

    # get all session ids
    for build_id in build_ids:
        r = s.get(f"https://api.browserstack.com/automate/builds/{build_id}/sessions.json")
        output = json.loads(r.text)
        for entry in output:
            session = entry["automation_session"]
            print(len(session_ids), session["hashed_id"])
            session_ids.append(session["hashed_id"])
    
    # save to file
    with open(hash_save_file, "w") as f:
        for session_id in session_ids:
            f.write(session_id + "\n")
print("Total # of session ids:", len(session_ids))

if not headers_saved:
    # check the network logs and save the User-Agent headers, which we can use to check the browser version
    for session_id in session_ids:
        session_id = session_id.strip()
        r = s.get(f"https://api.browserstack.com/automate/sessions/{session_id}/networklogs")
        try:
            output = json.loads(r.text)
        except Exception as e:
            print(e)
            continue
        logs = output["log"]["entries"]
        user_agent = None
        for log in logs:
            found = False
            log_headers = log["request"]["headers"]
            for header in log_headers:
                # printing host for visibility
                if header["name"] == "Host":
                    print(header)
                if header["name"] == "User-Agent":
                    # set skip condition here
                    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/User-Agent
                    # "Mozilla/5.0 is the general token that says that the browser is Mozilla-compatible. 
                    # For historical reasons, almost every browser today sends it"
                    if "Mozilla/5.0" not in header["value"]:
                        print("skipping", header["value"])
                        continue
                    else:
                        user_agent = header["value"]
                        found = True
                        break
            if found:
                break
        print(len(user_agents), "Adding User-Agent:", header)
        user_agents.add(user_agent)

    with open(headers_save_file, "w") as f:
        for user_agent in user_agents:
            f.write(user_agent + "\n")

# analyze the headers
with open(headers_save_file, "r") as user_agents:
    for user_agent in user_agents:
        # print(user_agent)
        print(httpagentparser.detect(user_agent))