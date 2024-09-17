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
import math
import os
import shutil
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from typing import List

from CurlSimulation import fire_post_request
from crawltogsm.write_to_log import write_to_log
# from crawltogsm.write_to_log import write_to_log
from gsmtosimilarity.geonames.GeoNames import GeoNamesService
from gsmtosimilarity.conceptnet.ConceptNet5 import ConceptNetService
from gsmtosimilarity.levenshtein import lev
from gsmtosimilarity.stanza_pipeline import StanzaService


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
            end_id = end_obj[0]
            end = end_obj[1]

            end_node = create_node(i, end)
            exists = False
            for node in nodeIds:
                if node[0] == end_id:
                    end_node = node[1]
                    exists = True
                    break

            if not exists:
                nodes.append(end_node)
                nodeIds.append([end_id, end_node])
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


def sentence_preprocessing(self):
    db = []
    sentences = []
    if 'sentences' in self.cfg and len(self.cfg['sentences']) > 0:
        sentences = self.cfg['sentences']
    else:
        load_sentences(self, sentences)
    count = 0
    multi_named_entity_recognition(count, db, self, sentences)
    if self.cfg['similarity'] == 'IDEAS24':
        stanford_nlp_to_gsm(self, sentences)


def stanford_nlp_to_gsm(self, sentences:List[str]):
    # output = None
    # all_sentences = " ".join(map(lambda x: f'-F "p={x}"', sentences))
    if self.old_java is None:
        url = f'{str(self.cfg["stanford_nlp_host"])}:{str(self.cfg["stanford_nlp_port"])}/stanfordnlp'
        data = dict(zip(map(str,range(len(sentences))), map(str,sentences)))
        output = fire_post_request(url, data)
        if output is not None:
            with open(self.cfg['gsm_sentences'], 'w') as f:
                f.write(output)
        else:
            print("Make sure 'stanford_nlp_dg_server' is running")
    else:
        output = self.old_java.generateGSMDatabase(sentences)
        with open(self.cfg['gsm_sentences'], 'w') as f:
            f.write(output)
    # # command = f'curl -X POST {all_sentences} {str(self.cfg["stanford_nlp_host"])}:{str(self.cfg["stanford_nlp_port"])}/stanfordnlp'
    # try:
    #     output = subprocess.check_output(command, shell=True, text=True)
    #     with open(self.cfg['gsm_sentences'], 'w') as f:
    #         f.write(output)
    # except subprocess.CalledProcessError:
    #     print("Make sure 'stanford_nlp_dg_server' is running")
    return output, os.path.abspath(self.cfg['gsm_sentences'])


def send_time_parsing(self, sentences):
    # all_sentences = " ".join(map(lambda x: f'-F "p={x}"', sentences))
    output = None
    if self.old_java is None:
        url = f'{str(self.cfg["stanford_nlp_host"])}:{str(self.cfg["stanford_nlp_port"])}/sutime'
        data = dict(zip(map(str,range(len(sentences))), map(str,sentences)))
        output = fire_post_request(url, data)
    else:
        output = self.old_java.getTimeUnits(sentences)
    # command = f'curl -X POST {all_sentences} {str(self.cfg["stanford_nlp_host"])}:{str(self.cfg["stanford_nlp_port"])}/sutime'
    # try:
    #     output = subprocess.check_output(command, shell=True, text=True)
    #     return json.loads(output)
    # except subprocess.CalledProcessError:
    #     print("Make sure 'stanford_nlp_dg_server' is running")
    if output is not None:
        return json.loads(output)
    else:
        print("Make sure 'stanford_nlp_dg_server' is running")
        return None


@dataclass
@dataclass(order=True, frozen=False, eq=True)
class SentenceCoordinates:
    text: str
    sentence_id: int
    start_char: int
    end_char: int
    type: str
    confidence: float


class NamedEntity:
    monad: str
    type: str

    def __init__(self, name=None):
        self.monad = name
        self.type = "None"
        self.fromSentences = defaultdict(list[SentenceCoordinates])

    def reinit(self,name):
        self.monad = name
        return self

    def __getitem__(self, item):
        return self.fromSentences[item]


class MultiEntityUnit:
    def __init__(self):
        self.d = defaultdict(NamedEntity)

    def add_entity(self, sentence_id:int, text:str, type:str, start_char:int, end_char:int, monad:str, confidence:float):
        self.d[monad].reinit(monad)[sentence_id].append(SentenceCoordinates(text, sentence_id, start_char, end_char, type, confidence))

    def add_entity_from_dict(self, sentence_id, d):
        self.add_entity(sentence_id, d["text"], d["type"], d["start_char"], d["end_char"], d["monad"], d["confidence"])
        pass


def multi_named_entity_recognition(count, db, self, sentences):
    if db is None:
        db = list()
    geo_names_service = GeoNamesService()
    concept_net_service = ConceptNetService()
    stanza_service = StanzaService().nlp
    # meu = MultiEntityUnit()
    tp = send_time_parsing(self, sentences)
    sentence_id = -1
    for sentence, withTime in zip(sentences, tp):
        sentence_id += 1
        entities = []
        multi_entity_unit = []

        # Add results from Stanza to MEU
        # results = self.nlp(sentence)
        results = stanza_service(sentence)
        for ent in results.ents:
            # monad = ""
            entity = ent.text
            monad = entity.replace(" ", "")
            if ent.type == "ORG":  # Remove spaces to create one word 'ORG' entities
                entities.append([entity, monad])
            # Possible alternative to keep one single entity:
            # meu.add_entity(sentence_id, ent.text, ent.type, ent.start_char, ent.end_char, monad, 1)
            result = {
                "text": ent.text,
                "type": ent.type,
                "start_char": ent.start_char,
                "end_char": ent.end_char,
                "monad": monad,
                "confidence": lev(monad.lower(), ent.text.lower())
            }
            multi_entity_unit.append(result)

        for time in withTime:
            #Possible alternative to keep one single entity:
            # meu.add_entity_from_dict(sentence_id, time)
            multi_entity_unit.append(time)

        # TODO: add the spatial resolution from GeoNamesService, as per the example provided in the mainof GeoNames,
        #  maybe with a subset of all the GeoGraphical names
        # TODO: similarly we might use the same idea to resolve all the multi-named entity from a dictionary
        #  (e.g., ConceptNet)
        locs = geo_names_service.resolve_u(
            self.cfg['resolve_params']['recall_threshold'],
            self.cfg['resolve_params']['precision_threshold'],
            sentence,
            "GPE"
        )
        for loc in locs:
            #Possible alternative to keep one single entity:
            # meu.add_entity_from_dict(sentence_id, loc)
            multi_entity_unit.append(loc)

        # Get ConceptNet entities
        concept_net = concept_net_service.resolve_u(
            self.cfg['resolve_params']['recall_threshold'],
            self.cfg['resolve_params']['precision_threshold'],
            sentence,
            "ENTITY"
        )
        for net in concept_net:
            #Possible alternative to keep one single entity:
            # meu.add_entity_from_dict(sentence_id, net)
            multi_entity_unit.append(net)

        # Loop through all entities and replace in sentence before passing to NLP server
        for entity in entities:
            sentence = sentence.replace(entity[0], entity[1])

        db.append({'first_sentence': sentence, 'multi_entity_unit': multi_entity_unit})

        write_to_log(None, f"MEU for '{sentence}' finished")

        count += 1
        # Used for news crawler
        # total = int(self.cfg['iterations'])
        # if total is not None:
        #     if count >= total:
        #         break
        # else:
        #     print("Please enter valid number of 'iterations' in config.yaml")
        #     break
    with open(self.cfg['rewritten_dataset'], 'w') as f:
        f.write(os.linesep.join(sentences))
    if 'crawl_to_gsm' in self.cfg:
        if 'stanza_db' in self.cfg['crawl_to_gsm']:
            json.dump(db, open(self.cfg['crawl_to_gsm']['stanza_db'], "w"), indent=4, sort_keys=True)
    return db


def load_sentences(self, sentences):
    has_hand_dataset = 'should_load_handwritten_sentences' in self.cfg and self.cfg['should_load_handwritten_sentences']
    if has_hand_dataset:
        with open(self.cfg['hand_dataset']) as f:
            for line in f:
                sentence = line.split('\n')[0]
                # Skip if sentence already exists
                if sentence in sentences:
                    continue
                else:
                    sentences.append(sentence)
    else:
        ## TODO: connecting eventually to the crawler!
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
        with open(self.cfg['hand_dataset'], 'w') as f:
            f.write(os.linesep.join(sentences))
