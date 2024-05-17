__author__ = "Giacomo Bergami"
__copyright__ = "Copyright 2024, Giacomo Bergami"
__credits__ = ["Giacomo Bergami"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Giacomo Bergami"
__email__ = "bergamigiacomo@gmail.com"
__status__ = "Production"

import re
from collections import defaultdict
from functools import reduce
from string import Template

import pandas
import rdflib
from rdflib.graph import Graph, ConjunctiveGraph
from rdflib import Graph, URIRef, BNode, Literal, XSD
from rdflib import Namespace
from rdflib.namespace import OWL, RDF, RDFS, FOAF

def instantiateWithMap(s:str, m:dict):
    return Template(s.replace("@","$")).safe_substitute(m)


class Parmenides():
     parmenides_ns = Namespace("https://lo-ds.github.io/parmenides#")

     def __init__(self, filename):
         self.g = rdflib.Graph()
         self.g.parse(filename)
         self.trcl = defaultdict(set)

     def extractPureHierarchy(self, t, flip=False):
         ye = list(self.single_edge("^src", t, "^dst"))
         if len(ye)==0:
             return set()
         elif flip:
             return {(x["dst"], x["src"]) for x in ye}
         else:
             return {(x["src"], x["dst"]) for x in ye}

     def getAllEntitiesBuyImmediateType(self, t):
         ye = list(self.isA("^x", str(t)))
         if len(ye) == 0:
             return set()
         else:
             return {x["x"] for x in ye}

     def getTransitiveClosureHier(self, t):
         from Parmenides.TBox.CrossMatch import transitive_closure
         if t not in self.trcl:
             s = self.extractPureHierarchy("isA", True) | self.extractPureHierarchy("partOf", False)
             self.trcl[t] = transitive_closure(s)
         return self.trcl[t]

     def name_eq(self, src, dst):
         from Parmenides.TBox.ExpandConstituents import CasusHappening
         if (src == dst):
             return CasusHappening.EQUIVALENT
         elif src is None:
             return CasusHappening.INDIFFERENT
         elif dst is None:
             return CasusHappening.IMPLICATION
         else:
             resolveTypeFromOntologyLHS = set(self.typeOf(src))
             resolveTypeFromOntologyRHS = set(self.typeOf(dst))
             isect = resolveTypeFromOntologyLHS.intersection(resolveTypeFromOntologyRHS)
             if len(resolveTypeFromOntologyLHS) == 0:
                 return CasusHappening.INDIFFERENT
             elif len(resolveTypeFromOntologyRHS) == 0:
                 return CasusHappening.INDIFFERENT
             elif len(isect) == 0:
                 return CasusHappening.INDIFFERENT
             else:
                 for k in isect:
                    if (src, dst) in self.getTransitiveClosureHier(k):
                        return CasusHappening.IMPLICATION
                 return CasusHappening.INDIFFERENT


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

     def single_edge_dst_unary_capability(self, src, edge_type, verb, subj):
         knows_query = """
         SELECT DISTINCT ?src ?edge_type ?dst ?src_label ?verb ?subj
         WHERE {
             ?src ?edge_type ?dst.
             ?dst parmenides:entryPoint ?verb_e.
             ?verb_e rdfs:label ?verb. 
             ?dst parmenides:subject ?subj_e.
             ?subj_e rdfs:label ?subj. 
             ?src rdfs:label ?src_label.
         }"""
         bindings = {}
         srcBool = False
         edgeBool = False
         verbBool = False
         subjBool = False
         objBool = False
         if not src.startswith("^"):
             bindings["src_label"] = Literal(src, datatype=XSD.string)
         else:
             srcBool = True
         if not edge_type.startswith("^"):
             bindings["edge_type"] = URIRef(Parmenides.parmenides_ns[edge_type])
         else:
             edgeBool = True
         if not verb.startswith("^"):
             bindings["verb"] = Literal(verb, datatype=XSD.string)
         else:
             verbBool = True
         if not subj.startswith("^"):
             bindings["subj"] = Literal(subj, datatype=XSD.string)
         else:
             subjBool = True
         qres = self.g.query(knows_query, initBindings=bindings)
         for x in qres:
            d = x.asdict()
            k = dict()
            if srcBool:
                k[src[1:]] = str(d.get("src_label"))
            if subjBool:
                k[subj[1:]] = str(d.get("subj"))
            if verbBool:
                k[verb[1:]] = str(d.get("verb"))
            if edgeBool:
                k[edge_type[1:]] = str(d.get("edge_type"))[len(Parmenides.parmenides_ns):]
            yield k

     def single_edge_dst_binary_capability(self, src, edge_type, verb, subj, obj):
         knows_query = """
         SELECT DISTINCT ?src ?edge_type ?dst ?src_label ?verb ?subj ?obj
         WHERE {
             ?src ?edge_type ?dst.
             ?dst parmenides:entryPoint ?verb_e.
             ?verb_e rdfs:label ?verb. 
             ?dst parmenides:subject ?subj_e.
             ?subj_e rdfs:label ?subj. 
             ?dst parmenides:d_object ?obj_e.
             ?obj_e rdfs:label ?obj. 
             ?src rdfs:label ?src_label.
         }"""
         bindings = {}
         srcBool = False
         edgeBool = False
         verbBool = False
         subjBool = False
         objBool = False
         if not src.startswith("^"):
             bindings["src_label"] = Literal(src, datatype=XSD.string)
         else:
             srcBool = True
         if not edge_type.startswith("^"):
             bindings["edge_type"] = URIRef(Parmenides.parmenides_ns[edge_type])
         else:
             edgeBool = True
         if not verb.startswith("^"):
             bindings["verb"] = Literal(verb, datatype=XSD.string)
         else:
             verbBool = True
         if not subj.startswith("^"):
             bindings["subj"] = Literal(subj, datatype=XSD.string)
         else:
             subjBool = True
         if not obj.startswith("^"):
             bindings["obj"] = Literal(obj, datatype=XSD.string)
         else:
             objBool = True
         qres = self.g.query(knows_query, initBindings=bindings)
         for x in qres:
            d = x.asdict()
            k = dict()
            if srcBool:
                k[src[1:]] = str(d.get("src_label"))
            if subjBool:
                k[subj[1:]] = str(d.get("subj"))
            if objBool:
                k[obj[1:]] = str(d.get("obj"))
            if verbBool:
                k[verb[1:]] = str(d.get("verb"))
            if edgeBool:
                k[edge_type[1:]] = str(d.get("edge_type"))[len(Parmenides.parmenides_ns):]
            yield k

     def single_edge_src_multipoint(self, src, src_spec, edge_type, dst):
         knows_query = """
         SELECT DISTINCT ?src ?edge_type ?dst ?src_label ?src_spec ?dst_label
         WHERE {
             ?src ?edge_type ?dst.
             ?src parmenides:entryPoint ?src_entry.
             ?src_entry rdfs:label ?src_label.
             ?src_multi parmenides:hasAdjective ?src_spec_node.
             ?src_spec_node rdfs:label ?src_spec.
             ?dst rdfs:label ?dst_label .
         }"""
         bindings = {}
         srcBool = False
         srcSpecBool = False
         edgeBool = False
         dstBool = False
         if not src.startswith("^"):
             bindings["src_label"] = Literal(src, datatype=XSD.string)
         else:
             srcBool = True
         if not src_spec.startswith("^"):
             bindings["src_spec"] = Literal(src_spec, datatype=XSD.string)
         else:
             srcSpecBool = True
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
            if srcSpecBool:
                k[src_spec[1:]] = str(d.get("src_spec"))
            if dstBool:
                k[dst[1:]] = str(d.get("dst_label"))
            if edgeBool:
                k[edge_type[1:]] = str(d.get("edge_type"))[len(Parmenides.parmenides_ns):]
            yield k

     def single_edge(self, src, edge_type, dst):
         m = re.match(r"(?P<main>[^\[]+)\[(?P<spec>[^\]]+)\]", src)
         if m:
             yield from self.single_edge_src_multipoint(m.group('main'), m.group('spec'), edge_type, dst)
             return
         m = re.match(r"(?P<main>[^\(]+)\((?P<subj>[^\,)]+),(?P<obj>[^\)]+)\)", dst)
         if m:
             yield from self.single_edge_dst_binary_capability(src, edge_type, m.group('main'), m.group('subj'), m.group('obj'))
             return
         m = re.match(r"(?P<main>[^\(]+)\((?P<subj>[^\)]+)\)", dst)
         if m:
             yield from self.single_edge_dst_unary_capability(src, edge_type, m.group('main'), m.group('subj'))
             return
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

         if Q is None:
             return None
         elif isinstance(Q, list):
             if len(Q)==2 or len(Q)==3:
                 return list(map(lambda x: instantiateWithMap(x, m), Q))
             else:
                 raise ValueError("Len 2 are IsA queries, while the rest are Len 3")
         elif isinstance(Q, tuple) and len(Q)==2:
             return tuple([Q[0], list(map(lambda x: Parmenides.instantiate_query_with_map(x, m), Q[1]))])
         else:
            raise ValueError("Cases error: a list will identify base queries, while a tuple will identify compound constructions")


     def old_multiple_queries(self, Q):
         if Q is None:
             return pandas.DataFrame()
         elif isinstance(Q, list):
             if len(Q)==2:
                 return pandas.DataFrame(self.isA(Q[0], Q[1]))
             elif len(Q)==3:
                 return pandas.DataFrame( self.single_edge(Q[0], Q[1], Q[2]))
         elif isinstance(Q, tuple):
             assert len(Q)==2
             if Q[0].lower() == "and":
                 return reduce(lambda x,y: x.merge(y), map(self.old_multiple_queries, Q[1]))
             else:
                 raise ValueError(Q[0]+" is unexpected")
         else:
            raise ValueError("Cases error: a list will identify base queries, while a tuple will identify compound constructions")

     def multiple_queries(self, Q):
         result = self.old_multiple_queries(Q)
         if result is not None:
             return result.to_dict('records')
         else:
             return []

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
    w = g.old_multiple_queries(tuple(["and", [["^x", "^y", "^z"], ["^a", "^b", "^z"]]]))
    for hasEdge in g.single_edge("city center", "partOf", "^var"):
        print(hasEdge)
    for outcome in g.isA("flow", "^t"):
        print(outcome)
    for outcome in g.isA("busy", "Adjective"):
        print(outcome)
    for outcome in g.single_edge("city[busy]", "relatedTo", "^d"):
        print(outcome)
    for outcome in g.single_edge("traffic jam", "capableOf", "^v(^s,^o)"):
        print(outcome)
    # print(g.typeOf("Newcastle"))
    # print(g.typeOf("city"))
    # print(g.typeOf("flow"))