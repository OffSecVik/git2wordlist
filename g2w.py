from bs4 import BeautifulSoup
import requests
import argparse

repo_items = []

session = requests.session()

class RepoItem:
    def __init__(self, name, type_, href_, parent):
        self.name = name
        self.type = type_
        self.href = href_
        self.parent = parent

def getBranchName(repoUrl):
    response = session.get(repoUrl)
    soup = BeautifulSoup(response.text, 'lxml')
    ### GET BRANCH NAME
    button = soup.find("button", attrs={"id": "branch-picker-repos-header-ref-selector"})
    button_div = button.find("div", attrs={"class": "ref-selector-button-text-container"})
    branch_name = str(button_div.span.text).strip()
    return branch_name

def appendTreeAndBranchName(url, branch_name):
    ### MAKE NEW URL WITH COMPLETE BRANCH NAME
    return url + "/tree/" + branch_name

def needsBranchName(url):
    return not "/tree" in url

def parseRepo(url, parent_directory):
    response = session.get(url)
    if response.status_code == 404:
        return

    soup = BeautifulSoup(response.text, 'lxml')
    table = soup.find("table", attrs={"aria-labelledby": "folders-and-files"})
    if not table:
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
            item = RepoItem(item_name, item_type, href, parent_directory)

            repo_items.append(item)
            if item.type == "(Directory)":
                new_url = url.rstrip("/") + "/" + item.name
                new_parent = parent_directory + item.name + "/"
                parseRepo(new_url, new_parent)

def print_repo_items():
    for item in repo_items:
        if item is None:
            print("NONE ITEM")
        else:
            print(item.parent + item.name)


def main():
    url = "https://github.com/cmsmadesimple/cmsmadesimple"
    if needsBranchName(url):
        branch_name = getBranchName(url)
        url = appendTreeAndBranchName(url, branch_name)
    parseRepo(url, "")
    print_repo_items()

if __name__ == "__main__":
    main()
    ### TODO: Flag: Autourlencode (Should be default behavior)
    ### TODO: Flag: Verbose (logs finds on the fly, errors too)

