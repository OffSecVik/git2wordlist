from abc import abstractmethod, ABC

from bs4 import BeautifulSoup
import requests
import argparse
from datetime import datetime
from urllib.parse import quote

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
    def __init__(self, url, outfile, verbose, auto_encode):
        self.repo_items = []
        self.session = requests.session()
        self.url = url
        self.outfile = outfile
        self.verbose = verbose
        self.auto_encode = auto_encode

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
    def __init__(self, url, outfile, verbose, auto_encode):
        super().__init__(url, outfile, verbose, auto_encode)

    def getBranchName(self, repoUrl):
        response = self.session.get(repoUrl)
        soup = BeautifulSoup(response.text, 'lxml')
        ### GET BRANCH NAME
        button = soup.find("button", attrs={"id": "branch-picker-repos-header-ref-selector"})
        button_div = button.find("div", attrs={"class": "ref-selector-button-text-container"})
        branch_name = str(button_div.span.text).strip()
        self.log_verbose(f"[+] Found branch: {branch_name}")
        return branch_name

    def appendTreeAndBranchName(self, url, branch_name):
        ### MAKE NEW URL WITH COMPLETE BRANCH NAME
        new_url = url.rstrip("/") + "/tree/" + branch_name
        self.log_verbose(f"[+] Now crawling: {new_url}")
        return new_url

    def needsBranchName(self, url):
        return not "/tree" in url

    def parseRepo(self, url, parent_directory):
        response = self.session.get(url)
        if response.status_code == 404:
            self.log_verbose(f"[-] Invalid status code for {url}: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'lxml')
        table = soup.find("table", attrs={"aria-labelledby": "folders-and-files"})
        if not table:
            self.log_verbose(f"[-] Failed to find repository table on url: {url}")
            return

        tbody = table.find("tbody")
        if not tbody:
            return

        trows = tbody.find_all("tr")
        for tr in trows:
            if a := tr.find("a", attrs={"aria-label": True}):
                item_info = a.attrs['aria-label'].split(',')
                if len(item_info) < 2:
                    continue

                href = a.attrs['href']
                item_name = item_info[0]
                item_type = item_info[1].strip()
                if item_type == "(Directory)":
                    item_name += "/"
                item = RepoItem(item_name, item_type, href, parent_directory)
                self.repo_items.append(item)

                self.log_verbose(f"[+] Found repository item: {item.parent + item.name}")
                self.write_result(item.parent + item.name)

                ### INITIATE RECURSION FOR DIRECTORIES
                if item.type == "(Directory)":
                    new_url = url.rstrip("/") + "/" + item.name
                    new_parent = parent_directory + item.name
                    self.parseRepo(new_url, new_parent)

    def print_repo_items(self):
        for item in self.repo_items:
            if item is not None:
                print(item.parent + item.name)

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

    def parse_repo(self):
        if not self.site_parsable():
            return
        log(f"[+] Parsing site: {self.url}")
        url = self.url
        if self.needsBranchName(url):
            branch_name = self.getBranchName(url)
            url = self.appendTreeAndBranchName(url, branch_name)
        self.parseRepo(url, "")
        # self.print_repo_items()

def determineParser(args):
    url = args.url
    verbose = args.verbose
    outfile = args.outfile
    auto_encode = args.auto_url_encode
    if url.startswith("https://github.com"):
        repo_parser = GithubParser(url, outfile, verbose, auto_encode)
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

        args = repo_parser.parse_args()

        if args.outfile is None:
            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
            args.outfile = f"g2w_{timestamp}.txt"

        if repo_parser := determineParser(args):
            repo_parser.parse_repo()
            log(f"[+] Created wordlist at {args.outfile}")
            repo_parser.log_verbose(f"[+] Job finished. Exiting...")
        else:
            log("[-] Failed to determine version control system")
    except KeyboardInterrupt:
        log("[+] Received keyboard interrupt, exiting...")

if __name__ == "__main__":
    main()

