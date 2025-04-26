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

    def log(self, log_message):
        if self.verbose:
            print(log_message)

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
        self.log(f"[+] Found branch: {branch_name}")
        return branch_name

    def appendTreeAndBranchName(self, url, branch_name):
        ### MAKE NEW URL WITH COMPLETE BRANCH NAME
        new_url = url.rstrip("/") + "/tree/" + branch_name
        self.log(f"[+] Now crawling: {new_url}")
        return new_url

    def needsBranchName(self, url):
        return not "/tree" in url

    def parseRepo(self, url, parent_directory):
        response = self.session.get(url)
        if response.status_code == 404:
            self.log(f"[-] Invalid status code for {url}: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'lxml')
        table = soup.find("table", attrs={"aria-labelledby": "folders-and-files"})
        if not table:
            self.log(f"[-] Failed to find repository table on url: {url}")
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

                self.log(f"[+] Found repository item of type {item_type}: {item_name}")
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

    def parse_repo(self):
        self.log(f"[+] Parsing site: {self.url}")
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
        return GithubParser(url, outfile, verbose, auto_encode)
    return None

def main():
    parser = argparse.ArgumentParser(
        prog="g2w",
        description="Parses a git repository and transforms the directory structure into a wordlist.\nCurrently only supports github."
    )
    parser.add_argument('url')
    parser.add_argument('-o', '--outfile')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-a', '--auto-url-encode', action='store_true')

    args = parser.parse_args()

    if args.outfile is None:
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        args.outfile = f"g2w_{timestamp}.txt"

    if parser := determineParser(args):
        parser.parse_repo()
    else:
        print("Failed to determine version control system")


if __name__ == "__main__":
    main()

