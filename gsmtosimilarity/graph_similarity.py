import json
from collections import defaultdict
from typing import Union, List, TypedDict
from dataclasses import dataclass
from enum import Enum

import numpy as np
from sentence_transformers import SentenceTransformer, util

from gsmtosimilarity.string_similarity_factory import StringSimilarity


class Grouping(Enum):
    AND = 0
    OR = 1
    NEITHER = 2
    NOT = 3
    NONE = 4


# class Properties(TypedDict):  # Key-Value association
#     property: str  # Key
#     value: Union[int, str, float, bool]  # Value


class NodeEntryPoint:
    pass


@dataclass(order=True, frozen=True, eq=True)
class Singleton(NodeEntryPoint):  # Graph node representing just one entity
    named_entity: str  # String representation of the entity
    properties: frozenset  # Key-Value association for such entity


@dataclass(order=True, frozen=True, eq=True)
class SetOfSingletons(NodeEntryPoint):  # Graph node representing conjunction/disjunction/exclusion between entities
    type: Grouping  # Type of node grouping
    entities: List[NodeEntryPoint]  # A list of entity nodes


@dataclass(order=True, frozen=True, eq=True)
class Relationship:  # Representation of an edge
    source: NodeEntryPoint  # Source node
    target: NodeEntryPoint  # Target node
    edgeLabel: Singleton  # Edge label, also represented as an entity with properties
    isNegated: bool = False  # Whether the edge expresses a negated action


@dataclass(order=True, frozen=True, eq=True)
class Graph:
    edges: List[Relationship]  # A graph is defined as a collection of edges


class SimilarityScore:  # Defining the graph similarity score
    def __init__(self, cfg):
        self.entity_similarity = StringSimilarity(cfg, 'string_similarity')
        if 'verb_similarity' in cfg:
            self.rel_similarity = StringSimilarity(cfg, 'verb_similarity')
        else:
            self.rel_similarity = self.entity_similarity

    def string_distance(self, x: str, y: str) -> float:  # between 0 and 1
        return 1.0 - self.entity_similarity.string_similarity(x,y)

    def string_similarity(self, x: str, y: str) -> float:  # between 0 and 1
        return self.entity_similarity.string_similarity(x,y)

    def properties_distance(self, x: frozenset, y: frozenset) -> float:
        if (len(x) == 0) and (len(y) == 0):
            return 0
        x = dict(x)
        y = dict(y)
        L = set(x.keys())
        I = L.intersection(set(y.keys()))
        U = L.union(set(y.keys()))
        missing = len(U.difference(I))
        others = 0
        other_dist = 0
        for k in I:
            l = x[k]
            r = y[k]
            if type(l) != type(r):
                missing = missing + 1.0
            else:
                others = others + 1.0
                compute = 0.0
                number = False
                if isinstance(l, str):
                    compute = self.string_distance(l, r)
                elif isinstance(l, bool):
                    l = 1 if l else 0
                    r = 1 if r else 0
                    number = True
                else:
                    number = True
                if number:
                    compute = (abs(l - r) * 1.0) / (1.0 + abs(l - r) * 1.0)
                other_dist = other_dist + compute
        return (missing + other_dist) / (missing + others)

    def singleton_dist(self, x: Singleton, y: Singleton, isRel=False) -> float:  # between 0 and 1
        if isRel:
            return 1.0-self.rel_similarity.string_similarity(x.named_entity, y.named_entity)
        else:
            return self.string_distance(x.named_entity, y.named_entity)

    def entity_distance(self, x: NodeEntryPoint, y: NodeEntryPoint) -> float:
        if isinstance(x, Singleton) and isinstance(y, Singleton):
            return self.singleton_dist(x, y)
        elif isinstance(x, Singleton):
            if y.type == Grouping.AND:
                return 0.0
            elif y.type == Grouping.OR:
                return min(y.entities, key=lambda z: self.entity_distance(x, z))
            elif y.type == Grouping.NOT:
                assert len(y.entities)==1
                return 1.0 - self.entity_distance(x, y.entities[0])
            else:
                raise ValueError(str(y.type)+" is not supported")
        elif isinstance(y, Singleton):
            if y.type == Grouping.AND:
                return min(y.entities, key=lambda z: self.entity_distance(x, z))
            elif y.type == Grouping.OR:
                return 0.0
            elif y.type == Grouping.NOT:
                assert len(x.entities)==1
                return 1.0 - self.entity_distance(x.entities[0], y)
            else:
                raise ValueError(str(y.type)+" is not supported")
        else:
            assert len(x.entities)>0
            assert len(y.entities)>0
            matches = []
            
            for z in x.entities:
                yMin = min(y.entities, key=lambda k: self.entity_similarity(z, k))
                matches.append(tuple([x, yMin]))


    def edge_distance(self, x: Relationship, y: Relationship):
        L = (x.source.named_entity,x.edgeLabel.named_entity,x.target.named_entity)
        R = (y.source.named_entity,y.edgeLabel.named_entity,y.target.named_entity)
        print (str(L) +" vs "+str(R))
        srcSim = 1.0 - self.entity_distance(x.source, y.source)
        dstSim = 1.0 - self.entity_distance(x.target, y.target)
        edgeSim = 1.0 - self.singleton_dist(x.edgeLabel, y.edgeLabel, True) * (1 if x.isNegated == y.isNegated else 0)
        return 1.0- (srcSim * dstSim * edgeSim)

    def graph_distance(self, g1: Graph, g2: Graph):
        if len(g1.edges) == 0 or len(g2.edges) == 0:
            return []
        d = defaultdict(set)
        d_inv = defaultdict(set)
        S1 = set(g1.edges)
        S2 = set(g2.edges)
        total_cost = 0
        L = []
        for edge1 in g1.edges:
            edge2_cand = min(g2.edges, key=lambda edge2: self.edge_distance(edge1, edge2))
            distance = self.edge_distance(edge1, edge2_cand)
            L.append(tuple([edge1, distance, edge2_cand]))
            total_cost += distance
            d[edge1].add(edge2_cand)
            d_inv[edge2_cand].add(edge1)
        S1_inv = set()
        S2_inv = set()
        empty_set = set()
        for edge2 in g2.edges:
            S2_inv = S2_inv.union(d_inv.get(edge2, empty_set))
        for edge1 in g1.edges:
            S1_inv = S1_inv.union(d.get(edge1, empty_set))
        unmatchingDistance = (len(S1.difference(S2_inv)) + len(S2.difference(S1_inv)))
        unmatchingSimilarity = 1.0 - (unmatchingDistance/(1+unmatchingDistance))
        totalSimilarity = 1.0 - (total_cost/(1+total_cost))
        # total_cost += ((len(S1.difference(S2_inv)) + len(S2.difference(S1_inv))) / 2.0)
        return 1.0 - totalSimilarity*unmatchingSimilarity


# def print_hi(name):
#     # Use a breakpoint in the code line below to debug your script.
#     print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.

def load_file_for_similarity(result_json):
    with open(result_json) as user_file:  # always take "final_db.json" as input
        parsed_json = json.load(user_file)

        number_of_nodes = range(len(parsed_json))
        edges = []
        nodes = {}
        for row in number_of_nodes:
            item = parsed_json[row]
            if 'conj' in item['properties']:
                continue  # add set of singletons later as we might not have all nodes yet
            else:
                if len(item['xi']) > 0:  # xi might be empty?
                    name = item['xi'][0]
                else:
                    name = ''

                nodes[item['id']] = Singleton(
                    named_entity=name,
                    properties=frozenset(item['properties'].items())
                )

        for row in number_of_nodes:
            item = parsed_json[row]
            conj_nodes = []
            if 'conj' in item['properties']:
                conj = item['properties']['conj']
                if 'and' in conj:
                    group_type = Grouping.AND
                elif 'or' in conj:
                    group_type = Grouping.OR
                else:
                    group_type = Grouping.NONE
                for edge in item['phi']:
                    if 'orig' in edge['containment']:
                        conj_nodes.append(nodes[edge['content']])

            if len(conj_nodes) > 0:
                nodes[item['id']] = SetOfSingletons(
                    type=group_type,
                    entities=conj_nodes
                )
            elif len(conj_nodes) == 1:
                nodes[item['id']] = conj_nodes[0]

        # print(nodes)

        for row in range(len(parsed_json)):
            item = parsed_json[row]

            for edge in item['phi']:
                # skip if containment is conj
                if 'orig' not in edge['containment']:
                    edges.append(Relationship(
                        source=nodes[edge['score']['parent']],
                        target=nodes[edge['score']['child']],
                        edgeLabel=Singleton(named_entity=edge['containment'].replace("not", " ").strip(), properties=frozenset(dict().items())),
                        isNegated=('not' in edge['containment'])
                    ))
        # print(graph)
        return Graph(edges=edges)

if __name__ == '__main__':
    # print_hi('PyCharm')
    # TODO: Load all graph results from output of GSM C++ code
    result_json = './result.json'
    print(load_file_for_similarity(result_json))
