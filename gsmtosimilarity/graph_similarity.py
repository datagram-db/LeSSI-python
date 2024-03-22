import json
from collections import defaultdict
from typing import Union, List, TypedDict
from dataclasses import dataclass
from enum import Enum
from sentence_transformers import SentenceTransformer, util


class Grouping(Enum):
    AND = 0
    OR = 1
    NEITHER = 2


class Properties(TypedDict):  # Key-Value association
    property: str  # Key
    value: Union[int, str, float, bool]  # Value


class NodeEntryPoint:
    pass


@dataclass(order=True)
class Singleton(NodeEntryPoint):  # Graph node representing just one entity
    named_entity: str  # String representation of the entity
    properties: Properties  # Key-Value association for such entity


@dataclass(order=True)
class SetOfSingletons(NodeEntryPoint):  # Graph node representing conjunction/disjunction/exclusion between entities
    type: Grouping  # Type of node grouping
    entities: List[NodeEntryPoint]  # A list of entity nodes


@dataclass(order=True)
class Relationship:  # Representation of an edge
    source: NodeEntryPoint  # Source node
    target: NodeEntryPoint  # Target node
    edgeLabel: Singleton  # Edge label, also represented as an entity with properties
    isNegated: bool = False  # Whether the edge expresses a negated action


@dataclass(order=True)
class Graph:
    edges: List[Relationship]  # A graph is defined as a collection of edges

    def __init__(self):
        self.edges = list()


class SimilarityScore:  # Defining the graph similarity score
    def __init__(self):
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    def string_distance(self, x: str, y: str) -> float:  # between 0 and 1
        x_vec = self.model.encode(x, convert_to_tensor=True)
        y_vec = self.model.encode(y, convert_to_tensor=True)
        return 1.0 - util.pytorch_cos_sim(x_vec, y_vec)

    def properties_distance(self, x: Properties, y: Properties) -> float:
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

    def singleton_dist(self, x: Singleton, y: Singleton) -> float:  # between 0 and 1
        return (self.string_distance(x.named_entity, y.named_entity) + self.properties_distance(x.properties,
                                                                                                y.properties)) / 2.0

    def entity_distance(self, x: NodeEntryPoint, y: NodeEntryPoint) -> float:
        if isinstance(x, Singleton) and isinstance(y, Singleton):
            return self.singleton_dist(x, y)
        else:
            pass  # TODO

    def edge_distance(self, x: Relationship, y: Relationship):
        srcDst = self.entity_distance(x.source, y.source)
        dstDst = self.entity_distance(x.target, y.target)
        edge = self.singleton_dist(x.edgeLabel, y.edgeLabel) * (1 if x.isNegated == y.isNegated else 0)
        return (srcDst + dstDst + edge) / 3.0

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
        total_cost += ((len(S1.difference(S2_inv)) + len(S2.difference(S1_inv))) / 2.0)
        return total_cost / (1.0 + total_cost)


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


if __name__ == '__main__':
    # print_hi('PyCharm')
    # TODO: Load all graph results from output of GSM C++ code
    result_json = './result.json'
    with open(result_json) as user_file:  # always take "final_db.json" as input
        parsed_json = json.load(user_file)
        graph = Graph()
        number_of_nodes = range(len(parsed_json))

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
                    properties=item['properties']
                )

        for row in number_of_nodes:
            item = parsed_json[row]
            conj_nodes = []
            if 'conj' in item['properties']:
                conj = item['properties']['conj']

                if 'and' in conj:
                    group_type = Grouping(0)
                elif 'or' in conj:
                    group_type = Grouping(1)
                else:
                    group_type = Grouping(2)

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

        print(nodes)

        for row in range(len(parsed_json)):
            item = parsed_json[row]

            for edge in item['phi']:
                # skip if containment is conj
                if 'orig' not in edge['containment']:
                    graph.edges.append(Relationship(
                        source=nodes[edge['score']['parent']],
                        target=nodes[edge['score']['child']],
                        edgeLabel=Singleton(named_entity=edge['containment'].strip(), properties={}),
                        isNegated=('not' in edge['containment'])
                    ))

        print(graph)

        # TODO: Get similarity score of graphs
        # score = SimilarityScore()
        # score.graph_distance()
