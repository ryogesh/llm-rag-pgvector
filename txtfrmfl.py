#!/usr/bin/python3
# -*- coding: utf-8 -*-

""" 
Module to extract texts from file
Supports word, excel, txt, csv and pdf files
"""

import csv
import re
from zipfile import ZipFile
from io import BytesIO, StringIO
import codecs

from lxml.etree import iterparse
from pdfminer.high_level import extract_text
from openpyxl import load_workbook
from bs4 import BeautifulSoup as bs
from ftfy import fix_text
from pygments.lexers import guess_lexer

from coreconfigs import _IGNORE_SENTS, _LGLTXT, _TOC, _NUMDOTSPACE


class ExtractTextFromFile():
    """ Extracts text from file like object"""
    def default_filters(self, txt):
        """ Default filters to replace text strings"""
        # Key: String to replace, Value: (item1, item2)
        # item1(from the key replace what):everything r'.*' or specific e.g. r" 's"
        oth_fltrs = {
            r"\[\d+\]":(r'.*', ''), #replace digits between [] with ""
            r"\$ \d+(?:\.\d+)?":(' ', ""), # replace "$ " with just $
            r"\d{1,2} : \d{2}[ap]m":(' ', ""), # remove _ in time, " 12 : 13pm "
            r"\w+ 's":(r" 's", "'s"), # replace " 's"... with "'s"... and the likes below
            r"\w+ 're":(r" 're", "'re"), r"\w+ 'm":(r" 'm", "'m"), r"L '\w+":(r"L '", "L'"),
            r"\w+ 'll":(r" 'll", "'ll"), r"\w+ 'd":(r" 'd", "'d"), r"\w+ 't":(r" 't", "'t"),
            r"\w+ ,":(r" ,", ","), r"\w- \w":(r" ", ""),
            #replace space before the end of sentence punctuation
            r" \.$":(r".*", "."), r" \?$":(r".*", "?"), r" \!$":(r".*", "!"), r" ;$":(r".*", ";"),
            r"\w +\. +":(r" +\. +", ". "), r"\w +\! +":(r" +\! +", "! "),
            r"\w +\; +":(r" +\; +", "; "), r"\w +\? +":(r" +\? +", "? "),
            }
        # Replace any windows special characters, mojibake ...
        txt = fix_text(txt)
        for dkey, dval in oth_fltrs.items():
            txt = re.sub(dkey, lambda match: re.sub(dval[0], dval[1], match.group()), txt)
        txt = re.sub(_LGLTXT, r'', txt)
        txt = re.sub(_TOC, r'', txt)
        return txt

    def get_parsed_lines(self, lines):
        """ Utility function to apply ignore_texts
        and ignore lines with just line numbers, space, ."""
        alltxts = ''
        for txt in lines:
            if txt:
                txt = str(txt).strip()  # Just in case, we get a numeric
                if not _NUMDOTSPACE.match(txt) and txt not in _IGNORE_SENTS:
                    alltxts = f"{alltxts} {txt}"
        return alltxts

    def get_texts_frmhtm(self, fname):
        """Function to extract texts from html file"""
        with open(fname, 'rt', encoding='utf-8', errors='replace') as html_fl:
            html = bs(html_fl, "html.parser")
        _IGNORE_SENTS[-1] = html.title.text.strip()
        alltxts = self.get_parsed_lines(html.text.splitlines())
        _IGNORE_SENTS[-1] = ""
        return self.default_filters(alltxts)

    def get_texts_frmtxt(self, fname):
        """Function to extract texts from text file"""
        with open(fname, 'rt', encoding='utf-8', errors='replace') as tfl:
            alltxts = tfl.readlines()
        alltxts = self.get_parsed_lines(alltxts)
        return self.default_filters(alltxts)

    def get_texts_frmpdf(self, fname):
        """Function to extract texts from pdf file"""
        txt = extract_text(fname)
        pfl = StringIO(txt)
        alltxts = self.get_parsed_lines(pfl.readlines())
        return self.default_filters(alltxts)


    def get_texts_frmcsv(self, fname):
        """Function to extract texts from csv file. 
           If a row has many columns, columns are concatenated with ' '
           Returns concatenated text of all rows
        """
        alltxts = ''
        with open(fname, 'r', encoding='utf-8', errors='replace') as csvfl:
            csvdata = csv.reader(csvfl)
            for row in csvdata:
                rdata = self.get_parsed_lines(row)
                alltxts = f"{alltxts} {rdata}"
        return self.default_filters(alltxts)

    def get_texts_frmxls(self, fname):
        """Function to extract texts from xlsx file, only the first worksheet
        If a row has many columns, columns are concatenated with ' '
        Returns  concatenated text of all rows
        """
        xl_wbk = load_workbook(fname)
        xl_s = xl_wbk.worksheets[0]
        alltxts = ''
        for row in xl_s.values:
            rdata = self.get_parsed_lines(row)
            alltxts = f"{alltxts} {rdata}"
        return self.default_filters(alltxts)

    def get_texts_frmdoc(self, fname):
        """Function to extract texts from doc file
        Returns: Extracted texts as string
        """
        with open(fname, 'rb') as dfl:
            with ZipFile(dfl) as zfl:
                xmlfl = zfl.read('word/document.xml')

        tag_ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
        txttag = tag_ns + 't'  #text tag in word
        sstag = './/' + tag_ns + 'vertAlign'  # ignore superscripts
        alltxts = ''

        # Instead of parsing and building the entire xml tree into memory, use iterparse
        # Refer http://lxml.de/FAQ.html#how-do-i-use-lxml-safely-as-a-web-service-endpoint
        for action, elem in iterparse(BytesIO(xmlfl), events=('start', 'end'),
                                      resolve_entities=False, recover=False,
                                      remove_comments=True, remove_pis=True):
            ##print(action, elem.tag, elem.get(tag_ns + 'rsidR'))
            if action == 'end':  #***end is important***
                if elem.findtext(txttag) is not None and elem.find(sstag) is None:
                    alltxts = f"{alltxts}{elem.findtext(txttag)}"
                #Adding a space after a paragraph to classify new sentences accurately
                elif elem.tag == tag_ns + 'p':
                    #print('**Found p**:%s', elem.tag)
                    alltxts = f"{alltxts} "
        return self.default_filters(alltxts)

    def guess_filetype(self, rfl):
        """
        Try and make some guess on the filetype, not foolproof
        File signatures (aka "magic numbers"): https://www.garykessler.net/library/file_sigs.html
        Read 20 chars of the file to check if the file is doc, xl or pdf
        If not check if it's a html or text file
        """
        ftype = 'bin'
        with open(rfl, 'rb') as fl20:
            chars20 = fl20.read(20)
        if codecs.encode(chars20[:8], "hex") == b'504b030414000600': # docx, xlsx
            try:
                # Check if docx
                with open(rfl, 'rb') as dfl:
                    with ZipFile(dfl) as zfl:
                        _ = zfl.read("word/document.xml")
                ftype = "doc"
            except KeyError:
                with open(rfl, 'rb') as dfl:
                    with ZipFile(dfl) as zfl:
                        _ = zfl.read("xl/workbook.xml")
                ftype = "xls"
            except Exception as err:
                print(f"Could open the zipfile as docx or xlsx: {err}")
                raise
        elif codecs.encode(chars20[:4], "hex") == b'25504446': #pdf
            ftype = 'pdf'
        else:
            #try opening the file as text
            try:
                with open(rfl, 'rt') as fl20:
                    chars20 = fl20.read(20)
            except UnicodeDecodeError:
                print("Looks like a binary file")
            else:
                try:
                    mtypes = guess_lexer(chars20).mimetypes
                    if mtypes and 'text/html' in mtypes:
                        ftype = 'htm'
                    else:
                        ftype = 'txt'
                except Exception as err:
                    print(f"Lexer couldn't parse the file: {err}")
                    raise
        return ftype
