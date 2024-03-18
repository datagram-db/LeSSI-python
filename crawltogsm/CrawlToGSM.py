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

from crawltogsm.generate_gsm_cypher_db import item_generator, convert_to_cypher_json


class CrawlToGSM:
    def __init__(self, full_cfg):
        stanza.download('en')
        self.nlp = stanza.Pipeline('en')
        final_db = 'final_db.json'
        if ("generate_final_db") in full_cfg:
            if ("db_ph2") in full_cfg["generate_final_db"]:
                final_db = full_cfg["generate_final_db"]["db_ph2"]
        with open(final_db) as user_file:  # always take "final_db.json" as input
            self.parsed_json = json.load(user_file)
        self.cfg = full_cfg

    def __call__(self, *args, **kwargs):
        if "final_gsm_stanza_db" in self.cfg and self.cfg["final_gsm_stanza_db"]:
            self.final_gsm_stanza_db()
        ## TODO: calling C++ Code

    def final_gsm_stanza_db(self):
        db = []
        count = 0
        for i in item_generator(self.parsed_json, "maintext"):  # 'maintext' is the body of text from a given article
            text = str(i).replace('\n', '.')  # Replace newline with . to make split easier
            sentence = text.split('.')[0]  # Get first sentence from 'maintext'
            results = self.nlp(sentence)
            # TODO: merge strings based on type
            # for result in results.ents:
            #     if result.type == "ORG":
            #         result.text.replace(" ", "")
            print(results.ents)

            # Get entire output string from 'standfrom_nlp_dg_server'
            command = 'curl -X POST -F "p=' + sentence + '" ' + str(self.cfg['stanford_nlp_host']) + ':' + str(cfg[
                                                                                                              'stanford_nlp_port']) + '/stanfordnlp'  # Giacomo: change to the configuration, so to ensure this is always a string (better practices require that ports are numbers)
            try:
                output = subprocess.check_output(command, shell=True, text=True)

                # Output from "stanford_nlp_dg_server" gives the dependency relations§gsm output so split here with §
                cypher = convert_to_cypher_json(output.split("§")[0])
                gsm = output.split("§")[1]

                ans = {"first_sentence": sentence, "cypher": cypher, "gsm": gsm}
                db.append(ans)
            except subprocess.CalledProcessError:
                print("Make sure 'stanford_nlp_dg_server' is running")
                break

            count += 1
            total = int(self.cfg['iterations'])
            if total is not None:
                if count >= total:
                    break
            else:
                print("Please enter valid number of iterations as an argument, --it [number]")
                break

        # print(db)
        if 'crawl_to_gsm' in self.cfg:
            if 'stanza_db' in self.cfg["crawl_to_gsm"]:
                json.dump(db, open(self.cfg["crawl_to_gsm"]['stanza_db'], "w"), indent=4, sort_keys=True)