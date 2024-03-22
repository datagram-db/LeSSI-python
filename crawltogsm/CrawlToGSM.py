#!/usr/bin/env python3
__author__ = "Oliver R. Fox, Giacomo Bergami"
__email__ = "ollie.fox5@gmail.com, bergamigiacomo@gmail.com"
__copyright__ = "Copyright 2024, Oliver R. Fox, Giacomo Bergami"
__credits__ = ["Oliver R. Fox", "Giacomo Bergami"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Oliver R. Fox"
__status__ = "Production"

import json
import subprocess

import stanza

from crawltogsm.generate_gsm_cypher_db import generate_final_db


class CrawlToGSM:
    def __init__(self, full_cfg):
        final_db = 'final_db.json'  # By default, this is the file name from "generate_final_db.py"
        if 'generate_final_db' in full_cfg:  # Otherwise get file path from config
            if 'db_ph2' in full_cfg["generate_final_db"]:
                final_db = full_cfg["generate_final_db"]["db_ph2"]
        with open(final_db) as user_file:
            self.parsed_json = json.load(user_file)
        self.cfg = full_cfg

    def __call__(self, *args, **kwargs):
        # Should we regenerate the stanza db or not
        if "should_generate_final_stanza_db" in self.cfg and self.cfg["should_generate_final_stanza_db"]:
            stanza.download('en')
            self.nlp = stanza.Pipeline('en')
            generate_final_db(self)
            with open('gsm_sentences.txt') as sentences:
                db = sentences.read()
        else:
            with open('gsm_sentences.txt') as sentences:
                db = sentences.read()

        command = (f"{self.cfg['gsm_gsql_file_path']}/cmake-build-release/gsm2_server "
                   f"data/test/einstein/einstein_query.txt -j '{db}' -iortv -z \"pos\nSizeTAtt\"")

        try:
            # This will create the outputs for the given sentences in the C++ GSM
            output = subprocess.check_output(command, shell=True, text=True, cwd=self.cfg['gsm_gsql_file_path'])
            print(output)
        except subprocess.CalledProcessError as e:
            raise Exception(e.output)
