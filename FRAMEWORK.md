# Framework for Testing Mobile Phishing
This is a Python framework aiming to perform automated testing of phishing websites in mobile environments.

## Running the Framework
There are currently 3 different modules with which we can run our framework with:
1. `browserstack`
2. `target_generator`
3. `phishtank_fetcher`

To use the framework, edit the `config.yml` file with wanted configuration options and then run:
```
python -m run [browserstack/target_generator/phishtank_fetcher] [flags]
```

The basic idea is to first scrape the phishing URLs that we want to test from phishtank using the `phishtank_fetcher` module, then generate the list of targets/platforms that we want to test on using the `target_generator` module, then use the `browserstack` module to actually run the tests. 


### Fetching URLs from PhishTank
For just basic fetching of URLs from PhishTank, the options in this module shouldn't need to be changed.

To use `phishtank_fetcher`, just run:
```
python -m run phishtank_fetcher [# of URLs (optionally)]
```
Number of URLs can also be specified in the `config.yml` file.


### Generating Target/Platform Lists
When using `target_generator`, there are several options that can be specified in the `config.yml` file, all under the `target_generator` section. Below is a description of each configuration.

- `targets_directory`: the base directory used during all functionality. The end directory should be called `targets`.
- `output_as_file`: a boolean value that specifies whether to output the target list as a single YAML file (set to True), or multiple YAML files in groupings of `entries_per_file` located under a separate directory depending on the target OS (set to False).
- `custom_outfile`: can specify a custom output file or directory (depending on the value of `output_as_file`); leave null to use the default output locations.
- `browser_versions_file`: should be the YAML file containing the desktop browser versions to limit the test to, if we want to manually specify them.
- `entries_per_file`: the number of entries to limit each "build" in browserstack to; this is important to specify because otherwise some tests or "sessions" will be lost


### Running BrowserStack
The options for `browserstack` are:

- `build_name`: the title for the build
- `test_script`: the Selenium script to run with browserstack; this is what will be run with the `browserstack-sdk` command
- `urls_file`: the YAML file of phishing URLs to test on; should be generated using `phishtank_fetcher` module
- `targets_src`: The single file or the directory of files containing the list of devices/configurations to test on
- `interrupted`: boolean value for if the test was interrupted or not; if set to True, it will continue from the file `continue_point`; note this functionality is only for when `targets_src` is a directory, since there is not a way to add sessions (individual tests on a platform) to existing builds; you can only start new builds in browserstack
- `continue_point`: the name of the YAML file in the `targets_src` directory from which to continue testing