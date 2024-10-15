import argparse
import sys
from omegaconf import OmegaConf

from src.fetch_phishtank import PhishtankFetcher
from src.browserstack.browserstack_runner import BrowserstackRunner

CONFIG_FILE = "config.yml"

def browserstack_runner(args):
    config = OmegaConf.load(CONFIG_FILE)
    x = BrowserstackRunner(config=config)
    x.run_browserstack()

def target_generator(args):
    config = OmegaConf.load(CONFIG_FILE)
    x = BrowserstackRunner(config=config)
    x.generate_targets(args.platform)

def phishtank_fetcher(args):
    config = OmegaConf.load(CONFIG_FILE)
    x = PhishtankFetcher(config=config)
    x.fetch_phishtank(args.num_urls)


def main():
    parser = argparse.ArgumentParser(description="Mobile Phishing framework")
    subparsers = parser.add_subparsers(dest="module", required=True, help="Module to run")

    # Subparser for browserstack
    browserstack_parser = subparsers.add_parser("browserstack", help="Use browserstack submodule")
    browserstack_subparsers = browserstack_parser.add_subparsers(dest="browserstack_module", required=True, help="Browserstack submodule to run")
    # Subsubparser for generating browserstack targets
    browserstack_generate_targets = browserstack_subparsers.add_parser("generate_targets", help="Generate target list to be used by browserstack")
    browserstack_generate_targets.add_argument("-p", "--platform", choices=['all', 'android', 'ios', 'windows', 'macosx'], default='all', required=True, help="Value must be among [all, android, ios, windows, macosx]")
    browserstack_generate_targets.set_defaults(func=target_generator)
    # Subsubparser for running browserstack
    browserstack_exec = browserstack_subparsers.add_parser("exec", help="Execute browserstack using the configuration in the config.yml file")
    # other options for this module should be specified in config.yml
    browserstack_exec.set_defaults(func=browserstack_runner)

    # Subparser for phishtank_fetcher
    phishtank_fetcher_parser = subparsers.add_parser("phishtank_fetcher", help="Use phishtank_fetcher submodule")
    phishtank_fetcher_parser.add_argument("-n", "--num_urls", type=int, required=False, help="The number of phishing URLs to fetch from PhishTank")
    phishtank_fetcher_parser.set_defaults(func=phishtank_fetcher)

    # Parse the arguments and call the appropriate function
    args = parser.parse_args()

    if args.module == 'browserstack' or args.module == 'target_generator' or args.module == 'phishtank_fetcher':
        args.func(args)
    else:
        print(f"Unknown module: {args.module}")

if __name__ == "__main__":
    main()