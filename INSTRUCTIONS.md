# Instructions for Data Collection

(The first portion of this document is the same as the README.md file; also here: https://automate.browserstack.com/dashboard/v2/quick-start/)

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
* Clone this repository
```
git clone -b sdk https://github.com/browserstack/python-selenium-browserstack.git
``` 
* Set up a python virtual environment (venv):
```
python3 -m venv env
./env/Scripts/activate
```
* If using VSCode, make sure your virtual environment interpreter is selected;
```
[Ctrl]+[Shift]+P
Search for "Python: Select Interpreter"
Select the one in your virtual environment folder (./env/Scripts/python.exe)
```
* Install the required packages through requirements.txt
```
pip3 install -r requirements.txt
```

## Set BrowserStack Credentials
* Add your BrowserStack username and access key in the `browserstack.yml` config file (if you do this, make sure you don't upload them to git).
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

## Running tests
* First, update the platforms/devices to test in the `browserstack.yml` file. The `platforms/` folder in this repo will have lists that we can copy-paste and modify to test on the different categories of devices.
* After updating the `browserstack.yml` file, run our custom test script, `phish-test.py`:
  - Run the following command:
    ```
    browserstack-sdk ./tests/phish-test.py
    ```
  - If there is any specific logic that you are trying to test for, feel free to modify the script, or make a copy and modify the copy (since we are using git, it is OK to change things).

* You can also run the sample tests just to see whether it is a setup issue or an issue with the script:
  - To run the sample test across platforms defined in the `browserstack.yml` file, run:
    ```
    browserstack-sdk ./tests/test.py
    ``` 
  - To run the local test across platforms defined in the `browserstack.yml` file, run:
    ```
    browserstack-sdk ./tests/local-test.py
    ``` 

## Collecting and Recording Data
See our Google Doc for instructions on this part. Short recap here:
