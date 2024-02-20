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

import json
import re
import subprocess

if __name__ == '__main__':
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
        rels = []
        for line in lines:
            split_start = line.split('--')  # [start, rel-->end]
            if split_start != ['']:
                split_end = split_start[1].split("->")

                start = split_start[0]
                start_node = create_node(i, start)
                exists = False
                for node in nodes:
                    if node['properties']['name'] == start:
                        start_node = node
                        exists = True
                        break

                if not exists:
                    nodes.append(start_node)
                i += 1

                end = split_end[1]
                end_node = create_node(i, end)
                exists = False
                for node in nodes:
                    if node['properties']['name'] == end:
                        end_node = node
                        exists = True
                        break

                if not exists:
                    nodes.append(end_node)
                i += 1

                rel = split_end[0].replace('[', '').replace(']', '')
                rel_obj = create_rel(i, rel, start_node, end_node)
                rels.append(rel_obj)
                i += 1

        return {
            "nodes": nodes,
            "rels": rels
        }

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

    with open('final_db.json') as user_file:
        parsed_json = json.load(user_file)

    db = []
    count = 0
    for i in item_generator(parsed_json, "maintext"):
        text = str(i).replace('\n', '.')
        # print(str(i))
        # sentence = re.split('.', str(i))
        # print(sentence)
        sentence = text.split('.')[0]
        # print(sentence)
        command = 'curl -X POST -F "p=' + sentence + '" localhost:9999/stanfordnlp'
        # print(command)
        output = subprocess.check_output(command, shell=True, text=True)

        # cypher = output.split("§")[0]

        cypher = convert_to_cypher_json(output.split("§")[0])
        gsm = output.split("§")[1]

        # print(output)
        ans = {"first_sentence": sentence, "cypher": cypher, "gsm": gsm}
        db.append(ans)

        count += 1
        if count == 99:
            break

    print(db)
    json.dump(db, open("final_gsm_db.json", "w"), indent=4, sort_keys=True)
