import os
import requests
import sys
import shutil
import string
from bs4 import BeautifulSoup
from contextlib import closing
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZIP_DEFLATED


class PoolDownloader(object):

    def __init__(self, pool_id):
        self.pool_id = pool_id
        self.pool_name = None
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.base_url = "https://danbooru.donmai.us"
        self.page_count = 1
        self.image_count = 1
        self.temp_dir = None
        self.end_of_pool = False

    def download(self, image_url):
        try:
            data = requests.get(image_url, headers=self.headers, stream=True)
        except requests.exceptions.RequestException as e:
            print(e)
            sys.exit(1)
        with open(os.path.join(self.temp_dir, "") + "%d" % self.image_count + ".jpg", 'wb') as file:
            shutil.copyfileobj(data.raw, file)

    def getimages(self, page_tree):
        for article in page_tree.find_all("article"):
            self.download(article.get("data-file-url"))
            print("\r%d images downloaded..." % self.image_count, end="")
            sys.stdout.flush()
            self.image_count += 1

    def getpage(self):
        page_url = self.base_url + "/pools/%s" % self.pool_id + "?page=%d" % self.page_count
        try:
            page_content = requests.get(page_url, headers=self.headers)
        except requests.exceptions.RequestException as e:
            print(e)
            sys.exit(1)
        parsed_page = BeautifulSoup(page_content.text, "html.parser")
        self.getimages(parsed_page)
        if parsed_page.find("li", class_="current-page").find_next_sibling("li", class_="numbered-page") is None:
            self.end_of_pool = True
            self.pool_name = parsed_page.find("a", {"class": "pool-category-series"}).get_text()
        else:
            self.page_count += 1

    def makezip(self):
        translator = str.maketrans("", "", string.punctuation)
        with closing(ZipFile(self.pool_name.translate(translator) + ".zip", "w", ZIP_DEFLATED)) as archive:
            for file in os.listdir(self.temp_dir):
                archive.write(os.path.join(self.temp_dir, file), file)
            print("\nCreated archive '%s'" % archive.filename)

    def getpool(self):
        with TemporaryDirectory() as self.temp_dir:
            while not self.end_of_pool:
                self.getpage()
            self.makezip()


def userinput():
    if len(sys.argv) > 1:
        return sys.argv[1]
    else:
        return input("Pool ID: ")


def main():
    PoolDownloader(userinput()).getpool()


if __name__ == "__main__":
    main()

