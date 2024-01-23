
# Retrieval-Augmented Generation with pgvector as vector database

## Overview

Tool to interact with a large language module (LLM). 
Supports adding context to the query using Retrieval-Augmented Generation(RAG). Context is built against an internal knowledge base. In this case, [Cloudera Documentation](https://docs.cloudera.com). Context embeddings are stored and retrieved from a vector database.


## Tool Features
- Spider to crawl Cloudera Docs and download html files
- Supports html file download restrictions based on 
	-  Top-level site (Topic or keyword)
	-  Maximum top-level sites 
	-  Maximum files to download under a top-level site
- Extract text from following file formats
	- html
	- pdf
	- text
	- docx
	- xlsx
	- csv
- Store text in a vector database
- Query model with (or without) context or both
- Retrieve context from vector database during model query for accurate results


## Installation
### Prerequisites

- [Python](https://www.python.org/downloads/) 3.10 or greater
- check requirements.txt for required python libraries

### Supported Database

- [PostgreSQL](https://www.postgresql.org/) . Supports Postgres 11+ . Tested on 14.10.

### Vector Database

- [pgvector](https://github.com/pgvector/pgvector) 


### Scripts

- pgdb_setup.sh: Install postgresql14.10 database on Ubuntu.
- pgvector.sql: Configure postgresql database as a vector database
- setup.sh: Install required python packages, configure vector database. Assumes PostgreSQL database on the same host. Review the file before execution.


## Application

- coreconfigs.py: Application configurations. An important file to review and edit.
- sitemap_spider.py: Crawls and downloads all sitemaps from [Cloudera Docs sitemap](https://docs.cloudera.com/sitemap.xml)
- cdphtmldocs_spider.py: Based on the restrictions, crawls the sites under Cloudera Docs and downloads html files
- get_texts.py: Wrapper script to extract texts from the supported file formats.
- store_embeddings.py: Wrapper script to read the text files, generate embeddings and store in pgvector database
- example_query.py: Example to query LLM with context



## Getting Started

### Application config and run
- Download the repo
- Perform the installation steps (see above)
- #### Edit coreconfigs.py to update the postgreSQL DB connection. Optionally feel free to choose any other LLM.
- run get_texts.py to generate texts from the supported file formats
    ```
	python get_texts.py
	Processing file: inputs\runtime\7.2.17-atlas-import-using-connected-type.html
	Processing file: inputs\test.pdf
	Processing file: inputs\Test1.txt
	Processing file: inputs\test.docx
	...
	...
    ```

- run store_embeddings.py to store the embeddings into pgvector DB

    ```
	python store_embeddings.py
	Embedding model ok.
	DB connection established.
	Processing text file: iceberg-overview_pdf.txt
	Embeddings commited for file: texts\iceberg-overview_pdf.txt
	Processing text file: 7_2_17-cdf-datahub-sa-atlas-configuration_html.txt
	Embeddings commited for file: texts\cdf-datahub\7_2_17-cdf-datahub-sa-atlas-configuration_html.txt
	Processing text file: test_docx.txt
	Embeddings commited for file: texts\test_docx.txt
	....
	....
    ```

- run the example_query.py to test

    ```
    python example_query.py
    Loading checkpoint shards: 100%
	....
	....
	Embedding model ok.
	DB connection established.
	Answer: Atlas is a mythological figure in Greek and Roman mythology. In Greek mythology, Atlas...
	Answer with context: In Cloudera Streaming Analytics, you can use Apache Flink with Apache Atlas to track the input...
	...
    ```


## Jupyter notebook with Gradio
A sample jupyter notebook, LLM-RAG, with Gradio interface can also be used to interact with the LLM. 


## GUI example
<div align="center">
	<img src=assets/examples.jpg width=90% />
</div>