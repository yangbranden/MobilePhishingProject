import argparse
import sys
from omegaconf import OmegaConf

from src.fetch_phishtank import PhishtankFetcher
from src.target_generator import TargetGenerator
from src.browserstack.browserstack_runner import BrowserstackRunner

CONFIG_FILE = "config.yml"

def browserstack_runner():
    config = OmegaConf.load(CONFIG_FILE)
    x = BrowserstackRunner(config=config)
    x.run_browserstack()

def target_generator(args):
    config = OmegaConf.load(CONFIG_FILE)
    x = TargetGenerator(config=config)
    x.generate_targets(args.platform)

def phishtank_fetcher(args):
    config = OmegaConf.load(CONFIG_FILE)
    x = PhishtankFetcher(config=config)
    x.fetch_phishtank(args.num_urls)


def main():
    parser = argparse.ArgumentParser(description="Command-line tool to run different modules.")
    subparsers = parser.add_subparsers(dest="module", required=True, help="Module to run")

    # Subparser for browserstack_runner
    browserstack_runner_parser = subparsers.add_parser("browserstack", help="Use browserstack_runner submodule")
    # options for this module should be specified in config.yml
    browserstack_runner_parser.set_defaults(func=browserstack_runner)
    
    # Subparser for target_generator
    target_generator_parser = subparsers.add_parser("target_generator", help="Use target_generator submodule")
    target_generator_parser.add_argument("-p", "--platform", choices=['all', 'android', 'ios', 'windows', 'macosx'], default='all', required=True, help="Value must be among [all, android, ios, windows, macosx]")
    target_generator_parser.set_defaults(func=target_generator)

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