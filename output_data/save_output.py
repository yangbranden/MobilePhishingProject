import requests
import os
import json
import yaml

session_id = "cca5193cbb09406fd9be95ddcf362d394db85477"

urls_visited = []
phishing_urls = []

with open("./urls/latest.yml", "r") as f:
    y = yaml.safe_load(f)
    phishing_urls = y["urls"]

# print(phishing_urls)

s = requests.Session()
s.auth = (os.environ.get("BROWSERSTACK_USERNAME"), os.environ.get("BROWSERSTACK_ACCESS_KEY"))

r = s.get(f"https://api.browserstack.com/automate/sessions/{session_id}/logs")
lines = r.text.splitlines()
# print(lines)

with open("./output_data/tmp/tmp.json", "w") as f:
    for line in lines:
        f.write(line + "\n")

output = dict()
current_entry = dict()
for line in lines:
    if "REQUEST" not in line:
        continue
    segments = line.split(' ')
    json_str = ''.join(segments[7:])
    
    # Attempt to parse as JSON
    try:
        json_data = json.loads(json_str)
        if "/url" in line:
            current_entry["url"] = json_data["url"]
        elif "/execute/sync" in line:
            result = json.loads(json_data["script"].split("browserstack_executor:")[-1])
            current_entry["script"] = result["arguments"]
            output[current_entry["url"]] = current_entry["script"]
            current_entry = dict() # reset current entry, just to be safe
    except json.JSONDecodeError:
        print(f"Last segment is not valid JSON: {json_str}")

if not os.path.exists(f"./output_data/outcomes/{session_id}"):
    os.makedirs(f"./output_data/outcomes/{session_id}")

with open(f"./output_data/outcomes/{session_id}/output.json", "w") as f:
    json.dump(output, f, indent=4)

print(output)
print("\nCheck output_data/outcomes/{session_id}/output.json for cleaner view of output.")