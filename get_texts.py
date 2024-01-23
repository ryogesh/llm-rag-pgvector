#!/usr/bin/python
# -*- coding: utf-8 -*-

""" Script to extract text from html, pdf, text, doc, xls, csv files """
from pathlib import Path
from zipfile import BadZipfile

import spacy
from openpyxl.utils.exceptions import InvalidFileException

from coreconfigs import _DOCTYPES, _INDIR, _TEXTDIR, _DOCSREADDIR, _SPACYMDL, _NUMDOTSPACE
from txtfrmfl import ExtractTextFromFile

prsr = spacy.load(_SPACYMDL)
txtext = ExtractTextFromFile()


def loopdir(fldr, parent='.'):
    """
    Iterate all the directories under _INDIR
    Extract text from the file.
    Perform basic pre-processing on the texts and save in _TEXTDIR
    Move the processed file to _DOCSREADDIR
    """
    for rfl in fldr.iterdir():
        if rfl.is_file():
            print(f"Processing file: {rfl}")
            ftype = rfl.name.split('.')[-1]
            if ftype == rfl.name:
                print(f"Check file type for: {rfl.name}")
                try:
                    ftype = txtext.guess_filetype(rfl)
                except Exception as err:
                    print(f"Could not identify file type: {err}")
                    print("Ignoring file...")
                    continue
            ftype = ftype[:3].lower() # Convert docx, xlsx, html : doc, xls, htm
            if ftype not in _DOCTYPES:
                print(f"Invalid or unsupported file with extension: {ftype}")
                print("Ignoring file processing...")
                continue
            try:
                fnc = f"get_texts_frm{ftype}"
                alltxt = getattr(txtext, fnc)(rfl)
            except (IOError, OSError, ValueError, BadZipfile, InvalidFileException) as err:
                print(f"Error processing file: {rfl.name}: {err}")
                print("Ignoring file processing...")
                continue
            ptxt = prsr(alltxt)
            fl_w = f"{'_'.join(rfl.name.split('.'))}.txt"
            with open(Path(_TEXTDIR, parent, fl_w), 'w', encoding='utf-8') as wfl:
                for snt in ptxt.sents:
                    txt = str(snt).strip()
                    if not _NUMDOTSPACE.match(txt):
                        wfl.write(f"{txt}\n")
            try:
                _ = rfl.replace(Path(_DOCSREADDIR, parent, rfl.name))
            except (PermissionError, FileExistsError, FileNotFoundError) as err:
                print(f"File not moved: {err}")
                print("Ignoring error...")

        if rfl.is_dir():
            print(f"Creating output, processed directories: {rfl.name}")
            Path(_TEXTDIR, rfl.name).mkdir(parents=True, exist_ok=True)
            Path(_DOCSREADDIR, rfl.name).mkdir(parents=True, exist_ok=True)
            loopdir(rfl, rfl.name)
            # Delete the documents input directory, ignore error if any file exists
            try:
                rfl.rmdir()
            except (OSError, FileNotFoundError) as err:
                print(f"Directory not deleted: {err}")
                print("Ignoring error...")

loopdir(Path(_INDIR))
