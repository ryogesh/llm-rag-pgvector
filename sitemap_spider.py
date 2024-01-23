#!/usr/bin/python
# -*- coding: utf-8 -*-

""" Script to extract and save sitemaps from cloudera docs site """

from pathlib import Path

import scrapy

from lxml import etree

from coreconfigs import _SITEMAPDIR
from coreutils import run_spider

class CdpsitemapSpider(scrapy.Spider):
    """
    Download the sitemap xml from Cloudera Docs site.
    Parse and download html files referenced in the sitemap.
    """
    name = "cdpsitemap"
    # All sitemaps: https://docs.cloudera.com/sitemap.xml
    # e.g. CDP 7.1.9: https://docs.cloudera.com/cdp-private-cloud-base/7.1.9/sitemap.xml

    start_urls = [
        "https://docs.cloudera.com/sitemap.xml",
    ]

    def parse(self, response):
        #prod, vers, page = response.url.split("/")[-3:]
        #filename = f"{prod}-{vers}-{page}"
        filename = response.url.split('/')[-1]
        Path(filename).write_bytes(response.body)
        self.log(f"Saved file {filename}")

        # Download all the sitemaps
        Path(_SITEMAPDIR).mkdir(parents=True, exist_ok=True)
        tree = etree.parse(filename)
        for elem in tree.iter("*"):
            if elem.tag.endswith("loc"):
                #print(f"Reading file: {elem.text}")
                yield scrapy.Request(url=elem.text, callback=self.parse_xml)

    def parse_xml(self, site):
        doc, ver = site.url.split("/")[3:5]
        fname = f"{ver}-{doc}.xml"
        #print(f"site filename: {fname}")
        Path(_SITEMAPDIR, fname).write_bytes(site.body)

if __name__ == '__main__':
    run_spider(Path(__file__).name)
