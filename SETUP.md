# Instructions for Data Collection
See the BrowserStack automated testing tutorial: https://automate.browserstack.com/dashboard/v2/quick-start/get-started

# Getting BrowserStack (free with GitHub Student Developer Pack)
https://www.browserstack.com/github-students

## Prerequisite
Make sure you have python3 installed:
```
python3 --version
```
or
```
python --version
```

## Setup
Clone this repository
```
git clone -b main https://github.com/yangbranden/MobilePhishingProject.git
``` 
Set up a python virtual environment (venv):
```
python3 -m venv env
./env/Scripts/activate
```
If using VSCode, make sure your virtual environment interpreter is selected;
```
[Ctrl]+[Shift]+P
Search for "Python: Select Interpreter"
Select the one in your virtual environment folder (./env/Scripts/python.exe)
```
Install the required packages through requirements.txt
```
pip3 install -r requirements.txt
```

## Set BrowserStack Credentials
Add your BrowserStack username and access key in the `browserstack.yml` config file (if you do this, make sure you don't upload them to git).
* You can also export them as environment variables, `BROWSERSTACK_USERNAME` and `BROWSERSTACK_ACCESS_KEY`:

  #### For Linux/MacOS
    ```
    export BROWSERSTACK_USERNAME=<browserstack-username>
    export BROWSERSTACK_ACCESS_KEY=<browserstack-access-key>
    ```
  #### For Windows
    ```
    setx BROWSERSTACK_USERNAME "<browserstack-username>"
    setx BROWSERSTACK_ACCESS_KEY "<browserstack-access-key>"
    ```
    or
    ```
    set BROWSERSTACK_USERNAME=<browserstack-username>
    set BROWSERSTACK_ACCESS_KEY=<browserstack-access-key>
    ```

## Using the framework
For more detailed information on using the framework, see [FRAMEWORK.md](./FRAMEWORK.md). 
