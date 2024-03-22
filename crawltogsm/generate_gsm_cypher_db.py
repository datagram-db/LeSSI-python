#!/usr/bin/env python3
__author__ = "Oliver R. Fox"
__copyright__ = "Copyright 2024, Oliver R. Fox"
__credits__ = ["Oliver R. Fox"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Oliver R. Fox"
__email__ = "ollie.fox5@gmail.com"
__status__ = "Production"

# This script produces a JSON file with a (optional: Cypher and) GSM representation of the first sentence from
# "generate_final_db.py" "maintext" paragraph in output JSON file, or from a given set of sentences

import json
import os
import subprocess


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

    # sim_graph = List[Relationship]

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


def generate_final_db(self):
    db = []
    sentences = []
    count = 0
    if 'should_load_handwritten_sentences' in self.cfg and self.cfg['should_load_handwritten_sentences']:
        with open('hand.txt') as f:
            for line in f:
                sentence = line.split('\n')[0]

                # Skip if sentence already exists
                if sentence in sentences:
                    continue
                else:
                    sentences.append(sentence)
    else:
        for i in item_generator(self.parsed_json, "maintext"):  # 'maintext' is the body of text from a given article
            text = str(i).replace('\n', '. ')  # Replace newline with '. ' to make split easier
            sentence = text.split('. ')[0]  # Get first sentence from 'maintext'

            # Skip if sentence already exists
            if sentence in sentences:
                continue
            elif "Published on:" in sentence:  # Omit sentences with this as they are malformed
                continue
            else:
                sentences.append(sentence)
        with open('hand.txt', 'w') as f:
            f.write(os.linesep.join(sentences))

    for sentence in sentences:
        results = self.nlp(sentence)

        entities = []
        multi_entity_unit = []
        for ent in results.ents:
            monad = ""
            if ent.type == "ORG":  # Remove spaces to create one word 'ORG' entities
                entity = ent.text
                monad = entity.replace(" ", "")
                entities.append([entity, monad])

            result = {
                "text": ent.text,
                "type": ent.type,
                "start_char": ent.start_char,
                "end_char": ent.end_char,
                "monad": monad
            }

            multi_entity_unit.append(result)
        print(multi_entity_unit)

        # Loop through all entities and replace in sentence before passing to NLP server
        for entity in entities:
            sentence = sentence.replace(entity[0], entity[1])

        db.append({'first_sentence': sentence, 'multi_entity_unit': multi_entity_unit})

        count += 1
        total = int(self.cfg['iterations'])
        if total is not None:
            if count >= total:
                break
        else:
            print("Please enter valid number of 'iterations' in config.yaml")
            break

    with open('sentences.txt', 'w') as f:
        f.write(os.linesep.join(sentences))

    if 'crawl_to_gsm' in self.cfg:
        if 'stanza_db' in self.cfg['crawl_to_gsm']:
            json.dump(db, open(self.cfg['crawl_to_gsm']['stanza_db'], "w"), indent=4, sort_keys=True)

    if self.cfg['similarity'] == 'IDEAS24':
        all_sentences = " ".join(map(lambda x: f'-F "p={x}"', sentences))
        command = f'curl -X POST {all_sentences} {str(self.cfg["stanford_nlp_host"])}:{str(self.cfg["stanford_nlp_port"])}/stanfordnlp'

        try:
            output = subprocess.check_output(command, shell=True, text=True)
            with open('gsm_sentences.txt', 'w') as f:
                f.write(output)
        except subprocess.CalledProcessError:
            print("Make sure 'stanford_nlp_dg_server' is running")