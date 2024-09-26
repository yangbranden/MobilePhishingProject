import ruamel.yaml
import time
import os
import requests
import json
yaml = ruamel.yaml.YAML() # using this version of yaml to preserve comments

# This is if for some reason the test is interrupted and we need to continue from a specific point
INTERRUPTED = False # Set to True if need to continue from the below CONTINUE_POINT file
CONTINUE_POINT = "0.yml"

test_script = "./tests/phish-test.py"
test_dirs = {
    # 'All Targets': './targets/all_targets', 
    # 'Android Targets': './targets/android',
    'iOS Targets': './targets/ios',
    # 'Windows Targets': './targets/windows',
    # 'OS X Targets': './targets/macosx'
}

# save the original config
with open("browserstack.yml", "r") as f:
    original_config = yaml.load(f)

found = False
current_config = None
for test_dir in test_dirs:
    files = os.listdir(test_dirs[test_dir])
    sorted_files = sorted(files, key=lambda x: int(x.split('.')[0]))
    
    for file in sorted_files:
        if INTERRUPTED:
            if found is False and file != CONTINUE_POINT:
                print("skipping...")
                continue 
            
            print("Continuing from", file)
            found = True
        
        # get the current config
        with open("browserstack.yml", "r") as f:
            current_config = yaml.load(f)

        # open the file with the set of targets
        with open(os.path.join(test_dirs[test_dir], file), "r") as target_set:
            platforms = yaml.load(target_set)
        
        # edit the config to have the target set we want
        current_config["buildName"] = test_dir
        current_config["platforms"] = platforms

        # overwrite the current config
        with open("browserstack.yml", "w") as f:
            yaml.dump(current_config, f)

        # run the test
        os.system(f"browserstack-sdk {test_script}")
        
        # if parallel_sessions_running == 0 then we can continue testing
        # https://api.browserstack.com/automate/plan.json
        s = requests.Session()
        s.auth = (os.environ.get("BROWSERSTACK_USERNAME"), os.environ.get("BROWSERSTACK_ACCESS_KEY"))
        r = s.get("https://api.browserstack.com/automate/plan.json")
        output = json.loads(r.text)  
        sleep_counter = 0
        while output["parallel_sessions_running"] != 0:
            print(f"Waiting for parallel session to finish ({sleep_counter})...")
            time.sleep(1)
            sleep_counter += 1

# Reset back to the original config
with open("browserstack.yml", "w") as f:
    yaml.dump(original_config, f)