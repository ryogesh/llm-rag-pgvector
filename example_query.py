#!/usr/bin/python
# -*- coding: utf-8 -*-

""" Example script to query LLM """

from coreutils import LLMOps


llm = LLMOps()

response = llm.mdl_response("what is atlas", )
print(f"Answer: {response[0][0]}\n\n")
print(f"Answer with context: {response[1][0]}")
