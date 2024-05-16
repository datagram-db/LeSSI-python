__author__ = "Giacomo Bergami"
__copyright__ = "Copyright 2020, Giacomo Bergami"
__credits__ = ["Giacomo Bergami"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Giacomo Bergami"
__email__ = "bergamigiacomo@gmail.com"
__status__ = "Production"
import json
import os.path
import sys

import numpy as np
import stanza
import yaml

from Parmenides.paremenides import Parmenides
from crawltogsm.LegacyPipeline import LegacyPipeline
from crawltogsm.generate_gsm_cypher_db import load_sentences, stanford_nlp_to_gsm, multi_named_entity_recognition
# from crawltogsm.write_to_log import write_to_log
from gsmtosimilarity.conceptnet.ConceptNet5 import ConceptNetService
from gsmtosimilarity.database.FuzzyStringMatchDatabase import FuzzyStringMatchDatabase
from gsmtosimilarity.geonames.GeoNames import GeoNamesService
from gsmtosimilarity.stanza_pipeline import StanzaService
from logical_repr.sentence_expansion import SentenceExpansion
from newscrawl.NewsCrawl import NewsCrawl

class CleanPipeline:
    _instance = None
    @classmethod
    def instance(cls):
        if cls._instance is None:
            print('Creating new instance')
            cls._instance = cls.__new__(cls)
            # Put any initialization here.
        return cls._instance

    @classmethod
    def write_to_log(cls, text):
        CleanPipeline.instance().writeself_to_log(text)

    def writeself_to_log(self, text):
        if self.cfg is not None and 'web_dir' in self.cfg and self.cfg['web_dir'] is not None:
            with open(f"{self.cfg['web_dir']}/log.txt", 'w') as f:
                f.write(f"{text}")
                f.close()
        else:
            print(text)

    def init(self, conf):
        if ".yaml" in conf:  # Check if this is a file instead of loaded from React
            try:
                with open(conf) as f:
                    self.cfg = yaml.load(f, Loader=yaml.FullLoader)
            except FileNotFoundError:
                raise Exception("Error: missing configuration file")
        else:
            self.cfg = conf
        if 'should_generate_final_stanza_db' not in self.cfg or not self.cfg['should_generate_final_stanza_db']:
            self.cfg['should_generate_final_stanza_db'] = True
        if 'should_run_datagram_db' not in self.cfg or not self.cfg['should_run_datagram_db']:
            self.cfg['should_run_datagram_db'] = self.cfg['similarity'].startswith('IDEAS24')
        if 'rewritten_dataset' not in self.cfg:
            self.cfg['rewritten_dataset'] = 'rewritten_dataset.txt'
        self.write_to_log("Starting the pipeline...")
        # TODO: your current configuration uses this as a server, right?
        #       Then, at initialization phase, we should move the time-consuming
        #       initialization at this point, so to reduce the warm-up time
        self.stanza_service = StanzaService()
        self.crawler = NewsCrawl()
        self.sentences = None

        if self.sentences is None and 'sentences' not in self.cfg:
            if 'hand_dataset' in self.cfg:
                self.cfg['rewritten_dataset'] = self.cfg['hand_dataset'] + '_rewritten.txt'
        else:
            # self.cfg['sentences'] = self.sentences
            self.cfg['rewritten_dataset'] = 'rewritten_user_input.txt'
        if 'gsm_sentences' not in self.cfg:
            self.cfg['gsm_sentences'] = self.cfg['rewritten_dataset'].replace("rewritten", "") + '_gsm_sentences.txt'
        if 'crawl_to_gsm' not in self.cfg:
            self.cfg['crawl_to_gsm'] = {}
        if 'stanza_db' not in self.cfg['crawl_to_gsm']:
            self.cfg['crawl_to_gsm']['stanza_db'] = self.cfg['rewritten_dataset'].replace("rewritten",
                                                                                          "") + '_stanza_db.json'

        ## DB Initialisation
        (FuzzyStringMatchDatabase
         .instance()
         .init(self.cfg["db"]["db"], self.cfg["db"]["uname"], self.cfg["db"]["pw"], self.cfg["db"]["host"], self.cfg["db"]["port"]))
        FuzzyStringMatchDatabase.instance().create("conceptnet", self.cfg["conceptnet"])
        FuzzyStringMatchDatabase.instance().create("geonames", self.cfg["geonames"])
        # global geo_names
        self.geo_names = GeoNamesService()
        # global concept_net
        self.concept_net = ConceptNetService()
        self.legacy_pipeline = LegacyPipeline(self.cfg)
        self.db = []
        self.sentences = []
        self.transitive_verbs = set()
        self.rejected_edges = set()
        self.non_verbs = set()
        if self.cfg['ontology']:
            self.parmenides = Parmenides(self.cfg['ontology'])
            self.transitive_verbs = set(self.parmenides.get_transitive_verbs())
            self.rejected_edges = set(self.parmenides.get_rejected_edges())
            self.non_verbs = set(self.parmenides.get_universal_dependencies())
        # if os.path.isfile(self.cfg['transitive_verbs']):
        #     with open(self.cfg['transitive_verbs'], "r") as f:
        #         self.transitive_verbs = set(map(lambda x: x.strip(), f.readlines()))
        # else:
        #
        # if os.path.isfile(self.cfg['rejected_edge_types']):
        #     with open(self.cfg['rejected_edge_types'], 'r') as f:
        #         self.rejected_edges = set(map(lambda x: x.strip(), f.readlines()))
        # else:
        #
        # if os.path.isfile(self.cfg['non_verbs']):
        #     with open(self.cfg['non_verbs'], "r") as f:
        #         self.non_verbs = set(f.readlines())
        # else:
        self.simplistic = self.cfg['rewriting_strategy'] == 'simplistic'

        # TODO: Add check for if NLTK is downloaded

        return self

    def getSentences(self):
        # if "should_generate_final_stanza_db" in self.cfg and self.cfg["should_generate_final_stanza_db"]:
        if 'sentences' in self.cfg and len(self.cfg['sentences']) > 0:
            self.sentences = self.cfg['sentences']
            with open("automated_dataset.txt", "w") as f:
                f.writelines(self.sentences)
            self.cfg['hand_dataset'] = "automated_dataset.txt"
        else:
            load_sentences(self.legacy_pipeline, self.sentences)
        return self.sentences

    def run(self):
        import json
        self.write_to_log("Starting pipeline...")
        sentences = self.getSentences()
        result = None
        if self.cfg['similarity'].startswith('IDEAS24'):
            result = self.transformation_pipeline(sentences)
        else:
            result = sentences
        f = self.getSimilarityFunction(result)

        M = []
        for x in result:
            ls = []
            for y in result:
                ls.append(f(x, y))
            M.append(ls)
        M = np.array(M)
        return json.dumps({"similarity_matrix": M.tolist(), "sentences": sentences})

    def apply_graph_grammar(self, gsm_sentences):
        gsmout_graphlist_file = self.cfg["hand_dataset"]+"_out_gsm.json"
        import os
        if os.path.isfile(gsmout_graphlist_file) and not self.cfg['force_regenerate']:
            with open(gsmout_graphlist_file) as f:
                self.write_to_log("READING PREVIOUS COMPUTATION FOR: graphs")
                graphs = json.load(f)
        else:
            from gsmtosimilarity.graph_similarity import read_graph_from_file
            directory = self.legacy_pipeline.graph_grammars_with_datagramdb(gsm_sentences=gsm_sentences)
            graphs = []
            import os
            for x in os.walk(directory):
                graphs = [None for _ in range(len(x[1]))]
                for result_folder in x[1]:
                    resultFile = os.path.join(x[0], result_folder, "result.json")
                    graphs[int(result_folder)] = read_graph_from_file(resultFile)
                break  # // Skipping the remaining subfolder
            with open(gsmout_graphlist_file, "w") as f:
                json.dump(graphs, f, indent=4)
        return graphs


    def semantic_transformation(self, graphs, stanza_db, dumpFile=None):
        # TODO: find a more explicative name
        from graph_repr.internal_graph import to_internal_graph
        from graph_repr.internal_graph import assign_singletons
        from graph_repr.internal_graph import assign_to_all
        allNodes = []
        for graph, stanza_row in zip(graphs, stanza_db):
            allNodes.append(assign_singletons(graph, stanza_row, self.simplistic))
        assign_to_all()
        graphs_r = [to_internal_graph(graph, stanza_row, self.rejected_edges, self.non_verbs, True, self.simplistic, nodes) for graph, stanza_row, nodes in zip(graphs, stanza_db, allNodes)]
        if dumpFile is not None:
            with open(dumpFile, "w") as f:
                print(dumpFile)
                import json
                from gsmtosimilarity.graph_similarity import EnhancedJSONEncoder
                json.dump([graph[0] for graph in graphs_r], f, cls=EnhancedJSONEncoder)
        return graphs_r

    def getLogicalRepresentation(self, graph_e_n_list):
        from graph_repr.internal_graph import create_sentence_obj
        # graph, edges, nodes = graph_e_n
        sentences = [create_sentence_obj(self.cfg, graph.edges, nodes, self.transitive_verbs, self.legacy_pipeline) for graph, nodes, edges in graph_e_n_list]
        gsmout_graphlist_file = self.cfg["hand_dataset"] + "_logical_rewriting.json"
        if not os.path.isfile(gsmout_graphlist_file):
            with open(gsmout_graphlist_file, "w") as f:
                print(gsmout_graphlist_file)
                import json
                from gsmtosimilarity.graph_similarity import EnhancedJSONEncoder
                json.dump(sentences, f, cls=EnhancedJSONEncoder, indent=4)
                # sys.exit(101)
        return sentences

    def transformation_pipeline(self, sentences):
        # Performing MultiNamedEntity Recognition
        self.generate_MEUdb(sentences)

        # Converting into the C++ format
        gsm_sentences = self.generate_gsm_from_stanfordnlp(sentences)

        # Running the Graph Grammar Rewriting
        graphs = self.apply_graph_grammar(gsm_sentences)

        # Perform the internal rewriting
        graphs = self.semantic_transformation(graphs, self.stanza_db)

        # TODO If transform into graphs, then return directly graphs
        #      Otherwise, call getLogicalRepresentation and return those instead
        if "graphs" in self.cfg['similarity']:
            return [graph[0] for graph in graphs]
        else:
            return self.getLogicalRepresentation(graphs)

    def generate_MEUdb(self, sentences):
        if 'crawl_to_gsm' in self.cfg and 'stanza_db' in self.cfg['crawl_to_gsm'] and \
                os.path.isfile(self.cfg['crawl_to_gsm']['stanza_db']) and not self.cfg['force_regenerate']:
            with open(self.cfg['crawl_to_gsm']['stanza_db']) as f:
                self.write_to_log("READING PREVIOUS COMPUTATION FOR: stanza_db")
                self.stanza_db = json.load(f)
        else:
            self.stanza_db = multi_named_entity_recognition(0, None, self.legacy_pipeline, sentences)

    def generate_gsm_from_stanfordnlp(self, sentences):
        gsm_dbs = ""
        filepath = ""
        if 'gsm_sentences' in self.cfg and os.path.isfile(self.cfg['gsm_sentences']) and not self.cfg[
            'force_regenerate']:
            filepath = os.path.abspath(self.cfg['gsm_sentences'])
            with open(filepath) as f:
                self.write_to_log("READING PREVIOUS COMPUTATION FOR: gsm_dbs")
                gsm_dbs = f.read()
        else:
            gsm_dbs, filepath = stanford_nlp_to_gsm(self, sentences)  # some strings
        # with open("/home/giacomo/dumping_ground/gsm.txt", "w") as f:
        #     print("gsm.txt")
        #     import json
        #     f.write(gsm_dbs)
        return filepath

    def getSimilarityFunction(self, sentences):
        if 'IDEAS24' in self.cfg['similarity']:
            if 'graphs' in self.cfg['similarity']:
                return self.legacy_pipeline.graph_with_logic_similarity
            else:
                from Parmenides.TBox.CrossMatch import DoExpand
                doexp = DoExpand(self.cfg['ontology'], self.cfg['TBox'])

                return SentenceExpansion(sentences, doexp)
        else:
            return self.legacy_pipeline.sc.string_similarity



