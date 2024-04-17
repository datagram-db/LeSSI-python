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
import os.path
import shutil
import subprocess
import numpy as np
import stanza
from scipy.sparse import csr_matrix
import markov_clustering as mc
from crawltogsm.generate_gsm_cypher_db import sentence_preprocessing
from crawltogsm.write_to_log import write_to_log
from gsmtosimilarity.graph_similarity import load_file_for_similarity, SimilarityScore
from gsmtosimilarity.stanza_pipeline import StanzaService


class LegacyPipeline:
    def __init__(self, full_cfg):
        final_db = 'final_db.json'  # By default, this is the file name from "generate_final_db.py"
        if 'generate_final_db' in full_cfg:  # Otherwise get file path from config
            if 'db_ph2' in full_cfg["generate_final_db"]:
                final_db = full_cfg["generate_final_db"]["db_ph2"]
        if os.path.exists(final_db) and os.path.isfile(final_db):
            with open(final_db) as user_file:
                self.parsed_json = json.load(user_file)
        else:
            self.parsed_json = None
        self.cfg = full_cfg
        self.sc = SimilarityScore(self.cfg)
        if "should_generate_final_stanza_db" in self.cfg and self.cfg["should_generate_final_stanza_db"]:
            write_to_log(self.cfg, "Initialising Stanza pipeline...")
            self.nlp = StanzaService().nlp

    def ideas24Similarity(self):
        write_to_log(self.cfg, "Using IDEAS24 similarity matrix...")
        should_run_datagram_db = 'should_run_datagram_db' in self.cfg and self.cfg['should_run_datagram_db']

        directory = self.graph_grammars_with_datagramdb(should_run_datagram_db)
        stanza_json = None
        rejected_edges = []
        non_verbs = []
        if 'crawl_to_gsm' in self.cfg:
            if 'stanza_db' in self.cfg['crawl_to_gsm']:
                with open(self.cfg['crawl_to_gsm']['stanza_db']) as stanza_db_file:
                    stanza_json = json.load(stanza_db_file)
        with open(self.cfg['rejected_edge_types'], 'r') as f:
            rejected_edges = f.read()
        with open(self.cfg['non_verbs'], "r") as f:
            non_verbs = f.readlines()
        doRewriting = False
        simplistic = False
        if 'rewriting_strategy' in self.cfg and self.cfg['rewriting_strategy'] is not None:
            doRewriting = True
            simplistic = self.cfg['rewriting_strategy'] == 'simplistic'

        graphs = []
        for x in os.walk(directory):
            graphs = [None for _ in range(len(x[1]))]
            for result_folder in x[1]:
                resultFile = os.path.join(x[0], result_folder, "result.json")
                graphs[int(result_folder)] = load_file_for_similarity(resultFile, stanza_json, rejected_edges, non_verbs, doRewriting, simplistic)
            break  # // Skipping the remaining subfolder

        M = []
        for x in graphs:
            ls = []
            for y in graphs:
                dist = self.sc.graph_distance(x, y)*1.0
                dist = 1.0 - dist / (1 + dist)
                ls.append(dist)
            M.append(ls)
        return np.array(M)

    def graph_grammars_with_datagramdb(self, should_run_datagram_db=True, gsm_sentences=None):
        if gsm_sentences is None:
            gsm_sentences = self.cfg['gsm_sentences']
        if should_run_datagram_db:
            command = (f"{self.cfg['gsm_gsql_file_path']}cmake-build-release/gsm2_server "
                       f"data/test/einstein/einstein_query.txt '{gsm_sentences}' "
                       f"-iortv -z \"pos\nSizeTAtt\nbegin\nSizeTAtt\nend\nSizeTAtt\"")
            try:
                # This will create the outputs for the given sentences in the C++ GSM
                output = subprocess.check_output(command, shell=True, text=True, cwd=self.cfg['gsm_gsql_file_path'])
                # print(output)
            except subprocess.CalledProcessError as e:
                raise Exception(e.output)
        directory = os.path.join(self.cfg['gsm_gsql_file_path'], "viz", "data")
        # Check if config contains web dir, for visualisation tool
        if 'web_dir' in self.cfg and self.cfg['web_dir'] is not None:
            dataset_folder = f"{self.cfg['web_dir']}/dataset/data"
            if os.path.exists(dataset_folder):
                shutil.rmtree(dataset_folder)
            shutil.copytree(directory, dataset_folder)
        return directory

    def getSentencesFromFile(self):
        if 'sentences' in self.cfg and len(self.cfg['sentences']) > 0:
            sentences = self.cfg['sentences']
        else:
            with open(self.cfg['hand_dataset'], "r") as file:
                sentences = file.read().splitlines()
        write_to_log(self.cfg, f"Chosen sentences: {sentences}")
        return sentences

    def getSimilarityMatrix(self):
        write_to_log(self.cfg, "Getting similarity matrix...")
        if self.cfg['similarity'] == 'IDEAS24':
            return self.ideas24Similarity()
        elif self.cfg['similarity'] == 'SentenceTransformer':
            return self.bertSimilarity()

    def bertSimilarity(self):
        write_to_log(self.cfg, "Using BERT similarity matrix...")
        L = self.getSentencesFromFile()
        M = []
        for x in L:
            ls = []
            for y in L:
                ls.append(self.sc.string_similarity(x, y))
            M.append(ls)
        return np.array(M)

    def do_sentence_preprocessing(self):
        if "should_generate_final_stanza_db" in self.cfg and self.cfg["should_generate_final_stanza_db"]:
            sentence_preprocessing(self)

    def do_sentence_matching_and_evaluation(self):
        # Should we regenerate the stanza db or not
        write_to_log(self.cfg, "Doing sentence matching...")
        M = self.getSimilarityMatrix()
        s = self.getSentencesFromFile()
        if 'web_dir' in self.cfg and self.cfg['web_dir'] is not None:
            with open(self.cfg['web_dir'] + "similarity_" + self.cfg['similarity'] + ".json", "w") as f:
                json.dump({"similarity_matrix": M.tolist(), "sentences": s}, f)
        elif 'should_match_sentences' in self.cfg and self.cfg['should_match_sentences']:
            with open("similarity_"+self.cfg['similarity']+".json", "w") as f:
                json.dump({"similarity_matrix": M.tolist(), "sentences": s}, f)

        sparseMatrix = self.maximal_matching(M)
        self.mcl_clustering_matches(sparseMatrix)

    def mcl_clustering_matches(self, sparseMatrix):
        write_to_log(self.cfg, "Clustering matches...")
        result = mc.run_mcl(sparseMatrix)
        clusters = mc.get_clusters(result)
        if 'web_dir' in self.cfg and self.cfg['web_dir'] is not None:
            with open(self.cfg['web_dir']+"clusters_" + self.cfg['similarity'] + ".txt", "w") as f:
                f.write(os.linesep.join(map(lambda x: str(x), clusters)))
        else:
            with open("clusters_" + self.cfg['similarity'] + ".txt", "w") as f:
                f.write(os.linesep.join(map(lambda x: str(x), clusters)))

    def maximal_matching(self, M):
        write_to_log(self.cfg, "Maximal matching...")
        row = []
        col = []
        data = []
        for i in range(len(M)):
            j, maxVal = max(filter(lambda idx: idx[0] != i, enumerate(M[i])), key=lambda x: x[1])
            for i, currVal in enumerate(M[i]):
                if currVal >= maxVal:
                    row.append(i)
                    col.append(j)
                    data.append(currVal)
        sparseMatrix = csr_matrix((np.array(data), (np.array(row), np.array(col))),
                                  shape=(len(M), len(M))).toarray()
        return sparseMatrix
