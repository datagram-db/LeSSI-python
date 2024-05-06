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

def literal(s:str):
    return Literal(s, datatype=XSD.string)

def boolean(s:bool):
    return Literal(s, datatype=XSD.boolean)

def onta(ns, s:str):
    return URIRef(ns[s])

class ParmenidesBuild():
    parmenides_ns = Namespace("https://lo-ds.github.io/parmenides#")

    def __init__(self):
        self.names = dict()
        self.g = Graph()
        self.classes = dict()
        self.g.bind("parmenides", ParmenidesBuild.parmenides_ns)
        self.g.bind("rdfs", RDF)


    def create_entity(self, name:str, clazzL=None):
        if name not in self.names:
            self.names[name] = onta(ParmenidesBuild.parmenides_ns, name)
            if (clazzL is not None):
                assert isinstance(clazzL, list)
                for clazz in clazzL:
                    assert clazz in self.classes
                    clazz = self.classes[clazz]
                    self.g.add((self.names[name], RDF.type, clazz))
                    self.g.add((self.names[name], RDFS.label, literal(name)))
        return  self.names[name]

    def create_class(self, name, subclazzOf=None):
        if name not in self.classes:
            clazz = onta(ParmenidesBuild.parmenides_ns, name)
            self.g.add((clazz, RDF.type, OWL.Class))
            if (subclazzOf is not None):
                subclazzOf = self.create_class(subclazzOf)
                self.g.add((clazz, RDFS.subClassOf, subclazzOf))
            self.classes[name] = clazz
        return self.classes[name]


    def serialize(self, filename):
        self.g.serialize(destination=filename)
def make_ontology_from_raw():
    p = ParmenidesBuild()
    gp_T = p.create_class("GraphParse")
    reject_T = p.create_class("Rejectable", "GraphParse")
    meta_T = p.create_class("MetaGrammaticalFunction")
    dep_T = p.create_class("dependency", "MetaGrammaticalFunction")
    gr_obj_T = p.create_class("GrammaticalFunction", "MetaGrammaticalFunction")
    verb_T = p.create_class("Verb", "GrammaticalFunction")
    tverb_T = p.create_class("TransitiveVerb", "Verb")
    iverb_T = p.create_class("IntransitiveVerb", "Verb")
    to_reject = set()
    with open("rejected_edge_types.txt", "r") as dep:
        for line in dep:
            line = line.strip()
            to_reject.add(line)
    with open("non_verb_types.txt", "r") as dep:
        for line in dep:
            line = line.strip()
            classes = ["dependency"]
            if line in to_reject:
                classes.append("Rejectable")
            p.create_entity(line, classes)
    with open("transitive_verbs.txt", "r") as dep:
        for line in dep:
            line = line.strip()
            classes = ["TransitiveVerb"]
            if line in to_reject:
                classes.append("Rejectable")
            p.create_entity(line, classes)
    p.serialize("turtle.ttl")