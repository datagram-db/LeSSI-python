__author__ = "Giacomo Bergami"
__copyright__ = "Copyright 2024, Giacomo Bergami"
__credits__ = ["Giacomo Bergami"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Giacomo Bergami"
__email__ = "bergamigiacomo@gmail.com"
__status__ = "Production"
import rdflib
from rdflib.graph import Graph, ConjunctiveGraph
from rdflib import Graph, URIRef, BNode, Literal, XSD
from rdflib import Namespace
from rdflib.namespace import OWL, RDF, RDFS, FOAF

class Parmenides():
     def __init__(self, filename):
         self.g = rdflib.Graph()
         self.g.parse(filename)

     def _single_unary_query(self, knows_query, f):
         qres = self.g.query(knows_query)
         for row in qres:
             yield f(row)
     def get_transitive_verbse(self):
         knows_query = """
         SELECT DISTINCT ?c
         WHERE {
             ?a a parmenides:TransitiveVerb.
             ?a rdfs:label ?c .
         }"""
         return self._single_unary_query(knows_query, lambda x: x.c)

     def get_universal_dependencies(self):
         knows_query = """
         SELECT DISTINCT ?c
         WHERE {
             ?a a parmenides:dependency.
             ?a rdfs:label ?c .
         }"""
         return self._single_unary_query(knows_query, lambda x: x.c)

     def get_rejected_edges(self):
         knows_query = """
         SELECT DISTINCT ?c
         WHERE {
             ?a a parmenides:Rejectable.
             ?a rdfs:label ?c .
         }"""
         return self._single_unary_query(knows_query, lambda x: x.c)


if __name__ == "__main__":
    g =  Parmenides("/home/giacomo/projects/similarity-pipeline/submodules/news-crawler/Parmenides/parmenides.ttl")
    # knows_query = """
    # SELECT DISTINCT ?c
    # WHERE {
    #     ?a a parmenides:Rejectable.
    #     ?a rdfs:label ?c .
    # }"""
    # qres = g.query(knows_query)
    for row in g.get_rejected_edges():
        print(row)