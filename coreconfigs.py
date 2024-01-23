#!/usr/bin/python
# -*- coding: utf-8 -*-

""" All configuration items
 Important: CHANGE the postgresDB connection information below
 Optional: To ignore during text extraction, Change
            _IGNORE_SENTS: list of sentences (not words)
            _LGLTXT: Legal text start .. end regular expression
            _TOC: Table of Contents start .. end regular expression
"""
import re


# Models used: Embedding model, LLM and Spacy model (for sentence identification)
# Embedding Model with lesser Dimension=384, better for vectorDB performance
# Use MTEB leaderboard: https://huggingface.co/spaces/mteb/leaderboard for model details
# Embedding Model Sequence Length = 512, setting _MAX_TKNLEN to about 25%
# Text chunks shouldn't be too short or too long to be of good context
_EMBED_MDL = "khoa-klaytn/bge-small-en-v1.5-angle"
_DB_EMBED_DIM = 384
_MAX_TKNLEN = 120

# LLM
_LLM_NAME = "HuggingFaceH4/zephyr-7b-beta"
_LLM_MSG_TMPLT = [{ "role": "system", "content": "",}, {"role": "user", "content": ''},]

# LLM model sequence length = 4k, we will provide about 1k tokens, _MAX_TKNLEN*_MAX_SIM_TXTS
# Higher length requires higher GPU processing, memory and can lead to OoM error on smaller GPUs.
# Reducing context tokens, reduces processing costs.
# But short contexts may lead to inaccurate or repetitive answers.
_MAX_SIM_TXTS = 4

# Spacy model for sentence segmentation, small is good enough.
# see comparison https://spacy.io/models/en
_SPACYMDL = "en_core_web_sm"


# Below 4 are applicable to the spider when crawling to download htmls
# Download html files related to a particular Topic
_DOWNLOAD_TOPIC = "atlas"
# Download htmls from any N random sites
_RAND_DIRS_COUNT = 5
# Restrict number of html files to download in a given site
_MAX_FILES_CNT = 5
# Directory to store sitemaps
_SITEMAPDIR = "sitemaps"

# Supported files
_DOCTYPES = ("doc", "pdf", "xls", "csv", "htm", "txt")
# Directory to store downloaded files
_INDIR = "docs_input"
# Directory to store documents once texts are extracted
_DOCSREADDIR = "docs_processed"
# Directory to store extracted texts
_TEXTDIR = "texts_input"
# Directory to store texts once embeddings are stored in vector DB
_TXTSREADDIR = "texts_processed"


# Texts to ignore when extracting text from documents
# Set the last item empty. Used in html processing to ignore the title text
_IGNORE_SENTS = ["Cloudera Docs", "Cloudera Manager", "https://docs.cloudera.com/",
                 ""]
# ignore legal, TOC
_LGLTXT = r"Legal Notice.*Cloudera.*Disclaimer.*OR COVENANT BASED ON COURSE OF DEALING OR USAGE IN TRADE."
_TOC = r"Contents.*\.\.\.\ [0-9]+"
# ignore lines with just digits e.g. page numbers
_NUMDOTSPACE = re.compile(r'^[0-9\.\ ]*$')

#PgVector DB details
_PGHOST = "1.1.1.1"
_PGPORT = 5432
_PGUSER = "ragu"
_PGDB = "ragdb"
_PGPWD = "yourpassword"
