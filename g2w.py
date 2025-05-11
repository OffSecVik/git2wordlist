from abc import abstractmethod, ABC

import requests
import argparse
from datetime import datetime
from urllib.parse import quote
import json
import os

class RepoItem:
    def __init__(self, name, type_, href_, parent):
        self.name = name
        self.type = type_
        self.href = href_
        self.parent = parent

def log(log_message):
    if "[+]" in log_message:
        print(f"\033[92m{log_message[:3]}\033[0m{log_message[3:]}")
    elif "[-]" in log_message:
        print(f"\033[91m{log_message[:3]}\033[0m{log_message[3:]}")
    else:
        print(log_message)

class RepoParser(ABC):
    def __init__(self, url, outfile, verbose, auto_encode, branch):
        self.repo_items = []
        self.session = requests.session()
        self.url = url
        self.outfile = outfile
        self.verbose = verbose
        self.auto_encode = auto_encode
        self.branch = branch

    @abstractmethod
    def parseRepo(self, url, parent_directory):
        pass

    def log_verbose(self, log_message):
        if self.verbose:
            log(log_message)

    def write_result(self, repository_item):
        if self.auto_encode:
            repository_item = quote(repository_item)
        with open(self.outfile, "a") as file:
            file.write(repository_item + "\n")

class GithubParser(RepoParser):
    def __init__(self, url, outfile, verbose, auto_encode, branch):
        super().__init__(url, outfile, verbose, auto_encode, branch)

    def rate_limited(self, response):
        if response.status_code == 403:
            try:
                data = response.json()
                if "API rate limit exceeded" in data.get("message", ""):
                    log("[-] API rate limit exceeded. Use a GitHub token to authenticate.")
                    return True
            except Exception:
                pass
        return False

    def parse_api(self, api_url, parent):
        response = requests.get(api_url)
        if self.rate_limited(response):
            return
        repo_items = json.loads(response.text)
        for item in repo_items:
            added_slash = "/" if item['type'] == 'dir' else ""
            self.write_result(parent + item['name'] + added_slash)
            if item['type'] == 'dir':
                self.parse_api(item['_links']['self'], f"{parent}{item['name']}/")

    def site_parsable(self):
        self.log_verbose(f"[+] Testing if site is parsable")
        try:
            response = self.session.get(self.url)
        except Exception as e:
            self.log_verbose(f"[-] Encountered {str(e)}")
            return False

        if not ((code := response.status_code) == 200):
            self.log_verbose(f"[-] Error: Site responded with status code {code}. Check your arguments?")
            return False

        self.log_verbose(f"[+] Site is parsable, proceeding...")
        return True

    def get_api_url(self, url, branch):
        repo = url.strip("https://gibhut.com/")
        return f"https://api.github.com/repos/{repo}/contents/{branch}"

    def parse_repo(self):
        if not self.site_parsable():
            return
        branch = self.branch
        api_url = self.get_api_url(self.url, branch)
        log(f"[+] Parsing api: {api_url}")
        self.parse_api(api_url, "")

def determineParser(args):
    url = args.url
    verbose = args.verbose
    outfile = args.outfile
    auto_encode = args.auto_url_encode
    branch = args.branch if args.branch == "" else f"?ref={args.branch}"
    if url.startswith("https://github.com"):
        repo_parser = GithubParser(url, outfile, verbose, auto_encode, branch)
        repo_parser.log_verbose(f"[+] Detected github url: Setting parsing mode to github")
        return repo_parser
    return None

def main():
    try:
        repo_parser = argparse.ArgumentParser(
            prog="g2w",
            description="Parses a git repository and transforms the directory structure into a wordlist.\nCurrently only supports github."
        )
        repo_parser.add_argument('url')
        repo_parser.add_argument('-o', '--outfile')
        repo_parser.add_argument('-v', '--verbose', action='store_true')
        repo_parser.add_argument('-a', '--auto-url-encode', action='store_true')
        repo_parser.add_argument('-b', '--branch', default="")

        args = repo_parser.parse_args()

        if args.outfile is None:
            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
            args.outfile = f"g2w_{timestamp}.txt"

        if repo_parser := determineParser(args):
            repo_parser.parse_repo()
            if os.path.exists(args.outfile) and os.path.getsize(args.outfile) > 0:
                log(f"[+] Created wordlist at {args.outfile}")
            else:
                log("[-] Parsing failed or empty. No wordlist created.")
            repo_parser.log_verbose(f"[+] Job finished. Exiting...")
        else:
            log("[-] Failed to determine version control system")
    except KeyboardInterrupt:
        log("[+] Received keyboard interrupt, exiting...")

if __name__ == "__main__":
    main()

