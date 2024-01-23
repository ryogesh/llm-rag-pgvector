#!/usr/bin/python
# -*- coding: utf-8 -*-

""" coreutils module: Provides common utilities for other modules """
from pathlib import Path
from time import sleep
import subprocess
import sys
from datetime import datetime, timezone
import json

import numpy as np
import psycopg
from humanize import precisedelta

import torch
import transformers
from sentence_transformers import SentenceTransformer

from coreconfigs import _LLM_NAME, _LLM_MSG_TMPLT, _EMBED_MDL, _TXTSREADDIR, \
                        _DB_EMBED_DIM, _MAX_SIM_TXTS, _MAX_TKNLEN, \
                        _PGHOST, _PGPORT, _PGUSER, _PGDB, _PGPWD


class DbOps():
    """ For database operations """
    def __init__(self):
        self.stmt = ''
        self.values = ''
        self._tmr = 0
        self._conn = ''
        self._dbconn_retry()

    def _dbconn_retry(self):
        try:
            self._conn = psycopg.connect(dbname=_PGDB,
                                        user=_PGUSER,
                                        password=_PGPWD,
                                        host=_PGHOST,
                                        port=_PGPORT,
                                        sslmode="prefer",
                                        connect_timeout=2)
        except psycopg.OperationalError:
            if self._tmr < 6:
                self._tmr += 3
                ### Server connection issue, try in few secs
                print(f"Unable to connect to database, trying in {self._tmr} secs...")
                sleep(self._tmr)
                self._dbconn_retry()
            else:
                self._tmr = 0
                raise

    def execstmt(self):
        """ Execute the DB statements """
        cur = self._conn.execute(self.stmt, self.values)
        res = ''
        if cur.description:  #no return rows
            res = cur.fetchall()
        return res

    def commit(self):
        """ Commits the transaction"""
        self._conn.commit()

    def rollback(self):
        """ Rollback the transaction"""
        self._conn.rollback()


class Embeds():
    """
    Provides helper functions to
    1. Iterate all the directories under _TEXTDIR
       Read text, chunk and save in pgvector DB
    2. Generate embedding and search for similar texts in pgvector DB
    """

    def __init__(self, dbconn=True):
        self.emb_mdl = SentenceTransformer(_EMBED_MDL)
        ## Verify embedding dimension size before processing
        embeddings = self.emb_mdl.encode("Hello World")
        if _DB_EMBED_DIM < embeddings.size:
            print(f"DB field length={_DB_EMBED_DIM}. Embedding dimension={embeddings.size}")
            print("Choose a different model or change embedding dimension on DB.")
            print("Exiting...")
            sys.exit(1)
        else:
            print("Embedding model ok.")
        if dbconn:
            self.dbo = DbOps()
            print("DB connection established.")
        # similarity: <=> cosine, <-> L2, <#> inner product
        # We normalize embeddings so use <#>
        # Ensure t_document_chunks index is using vector_ip_ops
        self.dbo_stmts = {"upd_doc":"update t_documents set created_at=%s where id=%s",
                     "ins_doc":"insert into t_documents (doc_name) values(%s) RETURNING id",
                     "sel_doc":"select id from t_documents where doc_name = %s",
                     "del_txts":"delete from t_document_chunks where doc_id = %s",
                     "ins_txt":"insert into t_document_chunks (doc_id, chunk, embedding) \
                                 values(%s, %s, %s)",
                     "sim_txts":f"SELECT id, chunk FROM t_document_chunks \
                                ORDER BY embedding <#> %s LIMIT {_MAX_SIM_TXTS}"
                    }

    def np_to_str(self, val):
        """Convert np.float32 to np.float64. json.dumps supports it."""
        return np.float64(val)

    def dbexec(self, stmt, values, msg):
        """
        Generic function for executing database statements
        If results=False, returns ''
        If results=True returns all rows
        """
        self.dbo.stmt = stmt
        self.dbo.values = values
        retval = ''
        try:
            retval = self.dbo.execstmt()
        except Exception:
            print(f"{msg}  failed....")
            print("Rolling back transaction")
            print(f"Statement: {self.dbo.stmt}")
            print(f"Values: {self.dbo.values}")
            self.dbo.rollback()
            raise
        self.dbo.stmt = ''
        self.dbo.values = ''
        return retval

    def save_embeddings_to_db(self, fldr, parent='.'):
        """
        Iterate all the directories under _TEXTDIR (fldr)
        Read text file, chunk texts and save chunk+embeddings in pgvector DB
        """
        for rfl in fldr.iterdir():
            if rfl.is_file():
                print(f"Processing text file: {rfl.name}")
                # If the file has been processed already, delete the document chunks and reprocess
                docid = self.dbexec(self.dbo_stmts['sel_doc'], (rfl.name, ),
                                    "Check for Document")
                if docid:
                    _ = self.dbexec(self.dbo_stmts['del_txts'], (docid[0][0], ),
                                    "Deleting document chunks")
                    _ = self.dbexec(self.dbo_stmts['upd_doc'],
                                    (datetime.now(tz=timezone.utc), docid[0][0]),
                                    "Updating document timestamp")
                else:
                    docid = self.dbexec(self.dbo_stmts['ins_doc'], (rfl.name, ),
                                        "Insert Document")
                with open(rfl, encoding="utf-8", errors="replace") as txt_fl:
                    filetexts = txt_fl.readlines()
                txtchunk = ''
                txtlst = []
                for txt in filetexts:
                    txt = txt.strip()
                    txtchunk = f"{txtchunk} {txt}"
                    txtlst.append(txt)
                    if len(txtchunk.split()) >= _MAX_TKNLEN:
                        embeddings = self.emb_mdl.encode(txtchunk)
                        # Normalizing the embeddings, just in case
                        # default is Frobenius norm
                        # https://numpy.org/doc/stable/reference/generated/numpy.linalg.norm.html
                        fnorm = np.linalg.norm(embeddings)
                        lst = list(embeddings/fnorm)
                        # json supports only np.float64. Convert np.float32
                        embed_str = json.dumps(lst, default=np.float64)
                        _ = self.dbexec(self.dbo_stmts['ins_txt'],
                                        (docid[0][0], json.dumps(txtlst), embed_str),
                                        "Insert chunk into Document")
                        txtchunk = ''
                self.dbo.commit()
                print(f"Embeddings commited for file: {rfl}")
                try:
                    _ = rfl.replace(Path(_TXTSREADDIR, parent, rfl.name))
                except (PermissionError, FileExistsError, FileNotFoundError) as err:
                    print(f"File not moved: {err}")
                    print("Ignoring error...")

            if rfl.is_dir():
                print(f"Creating text processed directory: {rfl.name}")
                Path(_TXTSREADDIR, rfl.name).mkdir(parents=True, exist_ok=True)
                self.save_embeddings_to_db(rfl, rfl.name)
                # Delete the processed text directory, ignore error if any file exists
                try:
                    rfl.rmdir()
                except (OSError, FileNotFoundError) as err:
                    print(f"Directory not deleted: {err}")
                    print("Ignoring error...")

    def get_similar_texts(self, text):
        """
        1. Generate text embedding.
        2. Compare similarity against vectorDB and get texts similar to the input text.
        """
        embeddings = self.emb_mdl.encode(text)
        # Normalize before querying the DB
        fnorm = np.linalg.norm(embeddings)
        lst = list(embeddings/fnorm)
        # json supports only np.float64. Convert np.float32
        embed_str = json.dumps(lst, default=np.float64)
        sim_txts = self.dbexec(self.dbo_stmts['sim_txts'], (embed_str,), "Get similar texts")
        #print(f"Similar text ids: {[itm[0] for itm in sim_txts]}")
        all_txts = []
        contxt = ''
        # Avoid duplicate sentences, less noise in context is better for LLM response
        for itm in sim_txts:
            for txt in itm[1]:
                if txt not in all_txts:
                    all_txts.append(txt)
                    contxt = f"{contxt} {txt}"
                    # Do not exceed the tokens limit
                    if len(contxt.split()) >= _MAX_TKNLEN*_MAX_SIM_TXTS:
                        break
        return contxt

class LLMOps():
    """For LLM operations """
    def __init__(self):
        self.pipeline = transformers.pipeline("text-generation",
                                              model=_LLM_NAME,
                                              torch_dtype=torch.bfloat16,
                                              device_map="auto",
                                             )
        self.gconfigdct = self.pipeline.model.generation_config.to_dict()
        self.gconfigdct["max_new_tokens"] =256
        self.gconfigdct["do_sample"] = True
        self.gconfigdct["top_k"] = 50
        self.gconfigdct["top_p"] = 0.95
        self.gconfigdct["pad_token_id"] = self.pipeline.model.config.eos_token_id
        self.emb = ''

    def mdl_ui_response(self, qry, temp=7, qrycontext="ANSWER"):
        """ Function returns ui friendly answer from the LLM """
        ans = self.mdl_response(qry, temp, qrycontext)
        return (f"{ans[0][0]}\n\n{ans[0][1]}",
                f"{ans[1][0]}\n\n{ans[1][1]}")

    def mdl_response(self, qry, temp=7, qrycontext="BOTH"):
        """ Function returns the answer from the LLM
        If qrycontext="ANSWER", then LLM answer only
        If qrycontext="CONTEXT", then LLM answer with context (RAG)
        If qrycontext="BOTH", then both
        Returns a tuple ("Query ANSWER", "With context ANSWER")
        """
        if temp < 1 or temp > 9:
            temp = 7
        def _get_ans(msg):
            _LLM_MSG_TMPLT[1]['content'] = msg
            btime = datetime.now()
            prompt = self.pipeline.tokenizer.apply_chat_template(_LLM_MSG_TMPLT, tokenize=False,
                                                                 add_generation_prompt=True)
            self.gconfigdct["temperature"] = temp/10
            gconfig = transformers.GenerationConfig(**self.gconfigdct)
            outputs = self.pipeline(prompt, generation_config=gconfig)
            res = outputs[0]["generated_text"].split("<|assistant|>\n")[1]
            return (res, precisedelta(datetime.now() - btime))

        if qrycontext == "ANSWER":
            fnl_res = (_get_ans(qry), '')
        elif qrycontext == "CONTEXT":
            if not self.emb:
                self.emb = Embeds()
            fnl_res = ('', _get_ans(self.emb.get_similar_texts(qry)) )
        elif qrycontext == "BOTH":
            msg1 = _get_ans(qry)
            if not self.emb:
                self.emb = Embeds()
            msg2 = _get_ans(self.emb.get_similar_texts(qry))
            fnl_res = (msg1, msg2)
        if len(qry.split()) < 2:
            fnl_res = (("Ask a good question", ''), '')
        return fnl_res


def run_spider(spiderfl):
    """ In case the program is called as a python program instead of 
    scrapy runspider cdp-spider.py
    """
    print(f"Running spider {spiderfl}")
    command = [
      "scrapy",
      "runspider",
      spiderfl,
    ]

    # Run the command
    with subprocess.Popen(command, stdout=subprocess.PIPE) as process:
        _, error = process.communicate()

    # Print output
    if process.returncode == 0:
        print("Spider completed successfully")
    else:
        print(f"Spider failed with: {error}")
