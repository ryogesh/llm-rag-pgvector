#!/usr/bin/python
# -*- coding: utf-8 -*-

""" 
Download HTML files using sitemap information

Logic:
1. If a topic, _DOWNLOAD_TOPIC, is not specified, and _RAND_DIRS_COUNT is specified, 
  -> All html files of N random sites are downloaded
2. If a topic is specified and _RAND_DIRS_COUNT is not specified, 
  -> All htmls related to the topic (url should contain the topic word)
3. If both _DOWNLOAD_TOPIC and _RAND_DIRS_COUNT is specified,
  ->Only html files of N random sites containing the topic word are downloaded
4. If both _DOWNLOAD_TOPIC and _RAND_DIRS_COUNT is not specified,
  -> All html files are downloaded from the site. <-- use with caution
5. If _MAX_FILES_CNT is set. Restricts the html files downloaded from a site
"""

import random
from pathlib import Path

import scrapy

from bs4 import BeautifulSoup as bs
from lxml import etree

from coreconfigs import _SITEMAPDIR, _MAX_FILES_CNT, _DOWNLOAD_TOPIC, _RAND_DIRS_COUNT, _HTMLDIR
from coreutils import run_spider


class CdpdocsSpider(scrapy.Spider):
    """
    Download html files based on the constraints specified in the config file
    Prettify and save in the HTMLs folder.
    """
    name = "cdpdocs"
    custom_settings = {
        "DOWNLOAD_DELAY": 2,
    }

    def start_requests(self):
        # Another way of reading xml file
        # tag_ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        # for evnt, elem in etree.iterparse("sitemap-719.xml", tag = f"{tag_ns}loc",
                                            #resolve_entities=False, recover=False,
                                            # remove_comments=True, remove_pis=True):

        sites = Path(_SITEMAPDIR)
        fl_lst = []
        for rfl in sites.iterdir():
            if rfl.is_file():
                fl_lst.append(rfl)

        if _RAND_DIRS_COUNT and _RAND_DIRS_COUNT > 0:
            fl_lst = random.sample(fl_lst, min(_RAND_DIRS_COUNT, len(fl_lst)))
        for rfl in fl_lst:
            print(f"Processing sitemap file: {rfl}")
            tree = etree.parse(rfl)
            flcntr = 1
            for elem in tree.iter("*"):
                if elem.tag.endswith("loc"):
                    url=elem.text
                    if _DOWNLOAD_TOPIC and _DOWNLOAD_TOPIC.lower() in url.lower():
                        yield scrapy.Request(url=url, callback=self.parse)
                        # Extract N docs only
                        flcntr +=1
                        if _MAX_FILES_CNT and flcntr > _MAX_FILES_CNT:
                            break

    def parse(self, response):
        page = response.url.split("/")[-1]
        doc, ver = response.url.split("/")[3:5]
        Path(_HTMLDIR, doc).mkdir(parents=True, exist_ok=True)
        filename = f"{ver}-{page}"
        phtml = bs(response.text, 'html.parser').prettify()
        Path(_HTMLDIR, doc, filename).write_text(phtml)
        self.log(f"Saved file {filename}")


if __name__ == '__main__':
    run_spider(Path(__file__).name)
