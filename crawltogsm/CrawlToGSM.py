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
import subprocess
import numpy as np
import stanza
from scipy.sparse import csr_matrix
import markov_clustering as mc
from crawltogsm.generate_gsm_cypher_db import generate_final_db
from gsmtosimilarity.graph_similarity import load_file_for_similarity, SimilarityScore

class CrawlToGSM:
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

    def ideas24Similarity(self):
        if 'should_run_datagram_db' in self.cfg and self.cfg['should_run_datagram_db']:
            with open(self.cfg['gsm_sentences']) as sentences:
                db = sentences.read()
            command = (f"{self.cfg['gsm_gsql_file_path']}/cmake-build-release/gsm2_server "
                       f"data/test/einstein/einstein_query.txt -j '{db}' -iortv -z \"pos\nSizeTAtt\"")
            try:
                # This will create the outputs for the given sentences in the C++ GSM
                output = subprocess.check_output(command, shell=True, text=True, cwd=self.cfg['gsm_gsql_file_path'])
                # print(output)
            except subprocess.CalledProcessError as e:
                raise Exception(e.output)
        directory = os.path.join(self.cfg['gsm_gsql_file_path'], "viz", "data")

        graphs = []
        for x in os.walk(directory):
            graphs = [None for _ in range(len(x[1]))]
            for result_folder in x[1]:
                resultFile = os.path.join(x[0], result_folder, "result.json")
                graphs[int(result_folder)] = load_file_for_similarity(resultFile)
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

    def getSentencesFromFile(self):
        sentences = []
        with open(self.cfg['hand_dataset'], "r") as file:
            sentences = file.read().splitlines()
        return sentences

    def getSimilarityMatrix(self):
        if self.cfg['similarity'] == 'IDEAS24':
            return self.ideas24Similarity()
        elif self.cfg['similarity'] == 'SentenceTransformer':
            return self.bertSimilarity()

    def bertSimilarity(self):
        L = self.getSentencesFromFile()
        M = []
        for x in L:
            ls = []
            for y in L:
                ls.append(self.sc.string_similarity(x, y))
            M.append(ls)
        return np.array(M)

    def __call__(self, *args, **kwargs):
        # Should we regenerate the stanza db or not
        if "should_generate_final_stanza_db" in self.cfg and self.cfg["should_generate_final_stanza_db"]:
            stanza.download('en')
            self.nlp = stanza.Pipeline('en')
            generate_final_db(self)
        M = self.getSimilarityMatrix()
        # perform clustering using different inflation values from 1.5 and 2.5
        # for each clustering run, calculate the modularity
        s = self.getSentencesFromFile()
        row = []
        col = []
        data = []
        for i in range(len(M)):
            j, maxVal = max(filter(lambda idx: idx[0]!=i, enumerate(M[i])), key=lambda x: x[1])
            for i, currVal in enumerate(M[i]):
                if currVal >= maxVal:
                    row.append(i)
                    col.append(j)
                    data.append(currVal)
        sparseMatrix = csr_matrix((np.array(data), (np.array(row), np.array(col))),
                                  shape=(len(M), len(M))).toarray()
        # perform clustering using different inflation values from 1.5 and 2.5
        # for each clustering run, calculate the modularity
        result = mc.run_mcl(sparseMatrix)
        clusters = mc.get_clusters(result)
        print(clusters)
        with open("similarity_"+self.cfg['similarity']+".json", "w") as f:
            json.dump({ "similarity_matrix": M.tolist(), "sentences": s }, f)
        with open("clusters_"+self.cfg['similarity']+".txt", "w") as f:
            f.write(os.linesep.join(map(lambda x: str(x), clusters)))



