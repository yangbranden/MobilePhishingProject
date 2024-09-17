import ruamel.yaml
import time
import os
yaml = ruamel.yaml.YAML() # using this version of yaml to preserve comments

test_script = "./tests/phish-test.py"
tests = {
    'All Targets': './targets/all_targets.yml', 
    'Android Targets': './targets/android.yml',
    'iOS Targets': './targets/ios.yml',
    'Windows Targets': './targets/windows.yml',
    'OS X Targets': './targets/macosx.yml'
}
sleep_time = 300 # Amount of time to wait in between tests

# save the original config
with open("browserstack.yml", "r") as f:
    original_config = yaml.load(f)

current_config = None
for test in tests:
    file = tests[test]

    # get the current config
    with open("browserstack.yml", "r") as f:
        current_config = yaml.load(f)

    # open the file with the set of targets
    with open(file, "r") as target_set:
        platforms = yaml.load(target_set)
    
    # edit the config to have the target set we want
    current_config["buildName"] = test
    current_config["platforms"] = platforms

    # overwrite the current config
    with open("browserstack.yml", "w") as f:
        yaml.dump(current_config, f)

    # run the test
    os.system(f"browserstack-sdk {test_script}")
    for i in range(sleep_time, 0, -1):
        print(f"Sleeping ({i})...")
        time.sleep(1)

# Reset back to the original config
with open("browserstack.yml", "w") as f:
        yaml.dump(original_config, f)