import requests
import os
import json
import yaml

session_id = "b4e4f28a449224a6586f55930e2ba56ebf03f28d"

urls_visited = []
phishing_urls = []

with open("./urls/latest.yml") as f:
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
        f.write(r.text)

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
        # print(json_data)
        if "/url" in line:
            current_entry["url"] = json_data["url"]
        elif "/elements" in line:
            current_entry["using"] = json_data["using"]
        elif "/execute/sync" in line:
            result = json.loads(json_data["script"].split("browserstack_executor:")[-1])
            current_entry["script"] = result["arguments"]
            output[current_entry["url"]] = current_entry["script"]
    except json.JSONDecodeError:
        print(f"Last segment is not valid JSON: {json_str}")


if not os.path.exists(f"./output_data/outcomes/{session_id}"):
    os.makedirs(f"./output_data/outcomes/{session_id}")

with open(f"./output_data/outcomes/{session_id}/output.json", "w") as f:
    json.dump(output, f, indent=4)

print(output)
print("\nCheck output_data/outcomes/{session_id}/output.json for cleaner view of output.")