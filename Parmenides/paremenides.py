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
     parmenides_ns = Namespace("https://lo-ds.github.io/parmenides#")

     def __init__(self, filename):
         self.g = rdflib.Graph()
         self.g.parse(filename)

     def _single_unary_query(self, knows_query, f):
         qres = self.g.query(knows_query)
         for row in qres:
             yield f(row)
     def get_transitive_verbs(self):
         knows_query = """
         SELECT DISTINCT ?c
         WHERE {
             ?a a parmenides:TransitiveVerb.
             ?a rdfs:label ?c .
         }"""
         return self._single_unary_query(knows_query, lambda x: str(x.c))

     def get_universal_dependencies(self):
         knows_query = """
         SELECT DISTINCT ?c
         WHERE {
             ?a a parmenides:dependency.
             ?a rdfs:label ?c .
         }"""
         return self._single_unary_query(knows_query, lambda x: str(x.c))

     def typeOf(self, src):
         knows_query = """
         SELECT DISTINCT ?dst 
         WHERE {
             ?src a ?dst.
             ?src rdfs:label ?src_label.
         }"""
         qres = self.g.query(knows_query, initBindings={"src_label":Literal(src, datatype=XSD.string)})
         s = set()
         for x in qres:
            s.add(str(x.dst))
         return s

     def isA(self, src, type):
         knows_query = """
         SELECT DISTINCT ?src ?dst
         WHERE {
             ?src a ?dst.
             ?src rdfs:label ?src_label.
         }"""
         bindings = {}
         srcBool = False
         dstBool = False
         if not src.startswith("^"):
             bindings["src_label"] = Literal(src, datatype=XSD.string)
         else:
             srcBool = True
         if not type.startswith("^"):
             bindings["dst"] = URIRef(Parmenides.parmenides_ns[type])
         else:
             dstBool = True
         qres = self.g.query(knows_query, initBindings=bindings)
         for x in qres:
             d = x.asdict()
             k = dict()
             if srcBool:
                 k[src[1:]] = str(d.get("src_label"))
             if dstBool:
                 k[type[1:]] = str(d.get("dst"))[len(Parmenides.parmenides_ns):]
             yield k

     def single_edge(self, src, edge_type, dst):
         knows_query = """
         SELECT DISTINCT ?src ?edge_type ?dst ?src_label ?dst_label
         WHERE {
             ?src ?edge_type ?dst.
             ?src rdfs:label ?src_label.
             ?dst rdfs:label ?dst_label .
         }"""
         bindings = {}
         srcBool = False
         edgeBool = False
         dstBool = False
         if not src.startswith("^"):
             bindings["src_label"] = Literal(src, datatype=XSD.string)
         else:
             srcBool = True
         if not edge_type.startswith("^"):
             bindings["edge_type"] = URIRef(Parmenides.parmenides_ns[edge_type])
         else:
             edgeBool = True
         if not dst.startswith("^"):
             bindings["dst_label"] = Literal(dst, datatype=XSD.string)
         else:
             dstBool = True
         qres = self.g.query(knows_query, initBindings=bindings)
         for x in qres:
            d = x.asdict()
            k = dict()
            if srcBool:
                k[src[1:]] = str(d.get("src_label"))
            if dstBool:
                k[dst[1:]] = str(d.get("dst_label"))
            if edgeBool:
                k[edge_type[1:]] = str(d.get("edge_type"))[len(Parmenides.parmenides_ns):]
            yield k


     @staticmethod
     def instantiate_query_with_map(Q, m):
         if isinstance(Q, list):
             if len(Q)==2 or len(Q)==3:
                 return list(map(lambda x: m.get(x[1:], "") if x.startswith("@") else x, Q))
             else:
                 raise ValueError("Len 2 are IsA queries, while the rest are Len 3")
         elif isinstance(Q, tuple) and len(Q)==2:
             return tuple([Q[0], list(map(lambda x: Parmenides.instantiate_query_with_map(x, m), Q[1]))])
         else:
            raise ValueError("Cases error: a list will identify base queries, while a tuple will identify compound constructions")


     def multiple_queries(self, Q):
         if isinstance(Q, list):
             if len(Q)==2:
                 yield from self.isA(Q[0], Q[1])
             elif len(Q)==3:
                 yield from self.single_edge(Q[0], Q[1], Q[2])
             else:
                 yield from []
         elif isinstance(Q, tuple):
             assert len(Q)==2
             if Q[0].lower() == "and":
                 d = dict()
                 for x in Q[1]:
                     for x in self.multiple_queries(x):
                         d = d | x
                 yield d
                 return True
             # elif Q[0].lower() == "or":
             #     for x in Q[1]:
             #         yield from self.multiple_queries(x)
             else:
                 raise ValueError(Q[0]+" is unexpected")
         else:
            raise ValueError("Cases error: a list will identify base queries, while a tuple will identify compound constructions")

     def get_rejected_edges(self):
         knows_query = """
         SELECT DISTINCT ?c
         WHERE {
             ?a a parmenides:Rejectable.
             ?a rdfs:label ?c .
         }"""
         return self._single_unary_query(knows_query, lambda x: str(x.c))


if __name__ == "__main__":
    g =  Parmenides("/home/giacomo/projects/similarity-pipeline/submodules/news-crawler/Parmenides/turtle.ttl")
    # knows_query = """
    # SELECT DISTINCT ?c
    # WHERE {
    #     ?a a parmenides:Rejectable.
    #     ?a rdfs:label ?c .
    # }"""
    # qres = g.query(knows_query)
    for hasEdge in g.single_edge("city center", "partOf", "^var"):
        print(hasEdge)
    for outcome in g.isA("flow", "^t"):
        print(outcome)
    for outcome in g.isA("busy", "Adjective"):
        print(outcome)
    # print(g.typeOf("Newcastle"))
    # print(g.typeOf("city"))
    # print(g.typeOf("flow"))