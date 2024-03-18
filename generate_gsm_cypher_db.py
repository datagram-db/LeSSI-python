#!/usr/bin/env python3
__author__ = "Oliver R. Fox"
__copyright__ = "Copyright 2024, Oliver R. Fox"
__credits__ = ["Oliver R. Fox"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Oliver R. Fox"
__email__ = "ollie.fox5@gmail.com"
__status__ = "Production"

# This script produces a JSON file with a Cypher and GSM representation of the first sentence from
# "generate_final_db.py" "maintext" paragraph in output JSON file.

import argparse
import json
import subprocess
import stanza
import yaml

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--it', dest='iterations', type=str, help='Number of articles to convert')
    args = parser.parse_args()

    stanza.download('en')
    nlp = stanza.Pipeline('en')

    with open("config.yaml") as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)

    def create_node(id, name):
        node = {
            "type": "node",
            "id": id,
            "properties": {
                "name": name
            }
        }
        return node


    def create_rel(id, name, start, end):
        rel = {
            "type": "relationship",
            "id": id,
            "label": name,
            "start": start,
            "end": end
        }
        return rel


    def convert_to_cypher_json(input):
        lines = input.split("\n")

        i = 0
        nodes = []
        nodeIds = []
        rels = []
        for line in lines:
            split_start = line.split('--')  # Split into [start, rel-->end]
            if split_start != ['']:  # As long as valid relationship exists then
                split_end = split_start[1].split("->")  # Split into [rel, end]

                start_obj = split_start[0].replace('(', '').replace(')', '').split(',')
                startId = start_obj[0]
                start = start_obj[1]

                start_node = create_node(i, start)
                exists = False
                for node in nodeIds:
                    if node[0] == startId:
                        start_node = node[1]
                        exists = True
                        break

                if not exists:
                    nodes.append(start_node)
                    nodeIds.append([startId, start_node])
                i += 1

                end_obj = split_end[1].replace('(', '').replace(')', '').split(',')
                endId = end_obj[0]
                end = end_obj[1]

                end_node = create_node(i, end)
                exists = False
                for node in nodeIds:
                    if node[0] == endId:
                        end_node = node[1]
                        exists = True
                        break

                if not exists:
                    nodes.append(end_node)
                    nodeIds.append([endId, end_node])
                i += 1

                rel = split_end[0].replace('[', '').replace(']', '')  # Remove brackets from rel object
                rel_obj = create_rel(i, rel, start_node, end_node)
                rels.append(rel_obj)
                i += 1

        return {
            "nodes": nodes,
            "rels": rels
        }

    # Function to get JSON key
    def item_generator(json_input, lookup_key):
        if isinstance(json_input, dict):
            for k, v in json_input.items():
                if k == lookup_key:
                    yield v
                else:
                    yield from item_generator(v, lookup_key)
        elif isinstance(json_input, list):
            for item in json_input:
                yield from item_generator(item, lookup_key)


    with open('final_db.json') as user_file:  # always take "final_db.json" as input
        parsed_json = json.load(user_file)

    db = []
    count = 0
    for i in item_generator(parsed_json, "maintext"):  # 'maintext' is the body of text from a given article
        text = str(i).replace('\n', '.')  # Replace newline with . to make split easier
        sentence = text.split('.')[0]  # Get first sentence from 'maintext'
        results = nlp(sentence)
        # TODO: merge strings based on type
        # for result in results.ents:
        #     if result.type == "ORG":
        #         result.text.replace(" ", "")
        print(results.ents)

        # Get entire output string from 'standfrom_nlp_dg_server'
        command = 'curl -X POST -F "p=' + sentence + '" ' + cfg['stanford_nlp_host'] + ':' + cfg['stanford_nlp_port'] + '/stanfordnlp'
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
        total = int(args.iterations)
        if total is not None:
            if count >= total:
                break
        else:
            print("Please enter valid number of iterations as an argument, --it [number]")
            break

    # print(db)
    json.dump(db, open("final_gsm_stanza_db.json", "w"), indent=4, sort_keys=True)
