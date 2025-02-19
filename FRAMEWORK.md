# Framework for Testing Mobile Phishing
This is a Python framework aiming to perform automated testing of phishing websites, with a particular focus on mobile environments.

## Running the Framework
There are currently 4 different modules with which we can run our framework with:
1. `browserstack`
2. `phishtank_fetcher`
3. `url_checker`
4. `cve_searcher`

To use the framework, edit the `config.yml` file with wanted configuration options and then run:
```
python -m run [browserstack/phishtank_fetcher/url_checker] [flags]
```

The basic idea is to first scrape the phishing URLs that we want to test from phishtank using the `phishtank_fetcher` module, then use the `browserstack` module to actually run the tests (currently only supports browserstack, but ideally we would implement support for other IaaS providers that have APIs capable of running Python selenium scripts). 



### Fetching URLs from PhishTank
The `phishtank_fetcher` module is to grab a set of known phishing URLs to run on the target platforms and devices. This allows us to see what devices are or are not protected with current phishing prevention mechanisms.

For just basic fetching of URLs from PhishTank, the options in this module shouldn't need to be changed.

To use `phishtank_fetcher`, just run:
```
python -m run phishtank_fetcher [# of URLs (optional)]
```
Number of URLs can also be specified in the `config.yml` file.



### Running BrowserStack
The `browserstack` module is using the IaaS provider BrowserStack to run automated phishing tests. Options for `browserstack` include:

- `exec`: runs browserstack using the settings specified in the `config.yml` file
    - `build_name`: the title for the build
    - `test_script`: the Selenium script to run with browserstack; this is what will be run with the `browserstack-sdk` command
    - `urls_file`: the YAML file of phishing URLs to test on; should be generated using `phishtank_fetcher` module
    - `targets_src`: The single file or the directory of files containing the list of devices/configurations to test on
    - `interrupted`: boolean value for if the test was interrupted or not; if set to True, it will continue from the file `continue_point`; note this functionality is only for when `targets_src` is a directory, since there is not a way to add sessions (individual tests on a platform) to existing builds; you can only start new builds in browserstack
    - `continue_point`: the name of the YAML file in the `targets_src` directory from which to continue testing

- `generate_targets`: creates list of targets for browserstack tests; there are several options that can be specified in the `config.yml` file, all under the `target_generator` section (located under the `browserstack` section)
    - `targets_directory`: the base directory used during all functionality. The end directory should be called `targets`.
    - `output_as_file`: a boolean value that specifies whether to output the target list as a single YAML file (set to True), or multiple YAML files in groupings of `entries_per_file` located under a separate directory depending on the target OS (set to False).
    - `custom_outfile`: can specify a custom output file or directory (depending on the value of `output_as_file`); leave null to use the default output locations.
    - `browser_versions_file`: should be the YAML file containing the desktop browser versions to limit the test to, if we want to manually specify them.
    - `entries_per_file`: the number of entries to limit each "build" in browserstack to; this is important to specify because otherwise some tests or "sessions" will be lost

- `output_analyzer`: used to view the outcome of a browserstack test; can specify either a single `session_id` or a `unique_id` (randomly generated 8 character string to identify your run)
    - `output_directory`: the base output directory (outcomes will be stored under this directory + `outcomes/`) 



### Checking URLs
The `url_checker` module is meant to act as a way of verifying certain URLs as verified phishing websites amongst other 3rd-party sources. So far, we support checking against:
- Google SafeBrowsing API (v4)
- PhishTank (which is where we scrape the URLs from)
- Online Certificate Status Protocol (OCSP)
- Certificate Revocation List (CRL)



### CVE Searcher
The `cve_searcher` module searches various sources for relevant CVEs, filtering out those that are unrelated to phishing and spoofing attacks. 

It is comprised of 2 simple scripts, which scrape various pieces of information. The `cve_searcher.py` script compiles a list of relevant CVEs, which are decided based on a set of criteria.

Currently, it is hard-coded to filter for CVEs since 2022 that contain the following keywords:
- "spoof", 
- "spoofing", 
- "fake", 
- "phishing"

The `parse_version.py` script determines a list of affected browser versions based upon the compiled list of CVEs.

