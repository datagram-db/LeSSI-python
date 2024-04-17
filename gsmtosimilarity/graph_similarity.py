import dataclasses
import functools
import functools
import json
import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import List

from gsmtosimilarity.string_similarity_factory import StringSimilarity

negations = {'not', 'no', 'but'}
location_types = {'GPE', 'LOC'}


class Grouping(Enum):
    AND = 0
    OR = 1
    NEITHER = 2
    NOT = 3
    NONE = 4
    GROUPING = 5


# class Properties(TypedDict):  # Key-Value association
#     property: str  # Key
#     value: Union[int, str, float, bool]  # Value


class NodeEntryPoint:
    pass


@dataclass(order=True, frozen=True, eq=True)
class Singleton(NodeEntryPoint):  # Graph node representing just one entity
    named_entity: str  # String representation of the entity
    properties: frozenset  # Key-Value association for such entity
    min: int
    max: int
    type: str
    confidence: float


@dataclass(order=True, frozen=True, eq=True)
class SetOfSingletons(NodeEntryPoint):  # Graph node representing conjunction/disjunction/exclusion between entities
    type: Grouping  # Type of node grouping
    entities: List[NodeEntryPoint]  # A list of entity nodes
    min: int
    max: int
    confidence: float


@dataclass(order=True, frozen=True, eq=True)
class Relationship:  # Representation of an edge
    source: NodeEntryPoint  # Source node
    target: NodeEntryPoint  # Target node
    edgeLabel: Singleton  # Edge label, also represented as an entity with properties
    isNegated: bool = False  # Whether the edge expresses a negated action


@dataclass(order=True, frozen=True, eq=True)
class Sentence:
    kernel: Relationship
    properties: dict = field(default_factory=lambda: {
        'time': List[NodeEntryPoint],
        'loc': List[NodeEntryPoint]
    })


@dataclass(order=True, frozen=True, eq=True)
class Graph:
    edges: List[Relationship]  # A graph is defined as a collection of edges


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        elif isinstance(o, frozenset):
            return dict(o)
        elif isinstance(o, Grouping):
            return o.name
        return super().default(o)


class SimilarityScore:  # Defining the graph similarity score
    def __init__(self, cfg):
        self.entity_similarity = StringSimilarity(cfg, 'string_similarity')
        if 'verb_similarity' in cfg:
            self.rel_similarity = StringSimilarity(cfg, 'verb_similarity')
        else:
            self.rel_similarity = self.entity_similarity

    @functools.lru_cache
    def string_distance(self, x: str, y: str) -> float:  # between 0 and 1
        return 1.0 - self.entity_similarity.string_similarity(x, y)

    @functools.lru_cache
    def string_similarity(self, x: str, y: str) -> float:  # between 0 and 1
        return self.entity_similarity.string_similarity(x, y)

    @functools.lru_cache
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

    @functools.lru_cache
    def singleton_dist(self, x: Singleton, y: Singleton, isRel=False) -> float:  # between 0 and 1
        if (x is None) or (y is None):
            return 0.0
        elif isRel:
            return 1.0 - self.rel_similarity.string_similarity(x.named_entity, y.named_entity)
        else:
            return self.string_distance(x.named_entity, y.named_entity)

    @functools.lru_cache
    def entity_distance(self, x: NodeEntryPoint, y: NodeEntryPoint) -> float:
        if (x is None) or (y is None):
            return 0.0
        elif isinstance(x, Singleton) and isinstance(y, Singleton):
            return self.singleton_dist(x, y)
        elif isinstance(x, Singleton):
            if y.type == Grouping.AND:
                return 1.0
            elif y.type == Grouping.OR:
                return self.entity_distance(x, min(y.entities, key=lambda z: self.entity_distance(x, z)))
            elif y.type == Grouping.NOT:
                assert len(y.entities) == 1
                return self.entity_distance(x, y.entities[0])
            else:
                raise ValueError(str(y.type) + " is not supported")
        elif isinstance(y, Singleton):
            if x.type == Grouping.AND:
                return self.entity_distance(min(x.entities, key=lambda z: self.entity_distance(z, y)), y)
            elif x.type == Grouping.OR:
                return 1.0
            elif x.type == Grouping.NOT:
                assert len(x.entities) == 1
                return self.entity_distance(x.entities[0], y)
            else:
                raise ValueError(str(y.type) + " is not supported")
        else:
            assert len(x.entities) > 0
            assert len(y.entities) > 0
            S1 = set(x.entities)
            S2 = set(y.entities)
            d = defaultdict(set)
            d_inv = defaultdict(set)
            matches = []
            total_cost = 0

            for z in S1:
                yMin = min(S2, key=lambda k: self.entity_distance(z, k))
                distance = self.entity_distance(z, yMin)
                total_cost = total_cost + distance
                matches.append(tuple([z, distance, yMin]))
                d[z].add(yMin)
                d_inv[yMin].add(z)
            S1_inv = set()
            S2_inv = set()
            empty_set = set()

            for edge2 in y.entities:
                S2_inv = S2_inv.union(d_inv.get(edge2, empty_set))
            for edge1 in x.entities:
                S1_inv = S1_inv.union(d.get(edge1, empty_set))
            # unmatchingDistance = (len(S1.difference(S2_inv)) + len(S2.difference(S1_inv)))
            if x.type == Grouping.AND:
                if y.type == Grouping.AND:
                    if len(S2) == len(S1_inv):
                        return float(total_cost) / float(len(matches))
                    else:
                        return 1.0  # If some of elements could not be derived from the left, the left does not entail the right
                elif y.type == Grouping.OR:
                    return float(total_cost) / float(len(matches))  # Assuming there is at least one alignment
                else:
                    return 1.0  # Contradiction
            elif x.type == Grouping.OR:
                if y.type == Grouping.AND:
                    return 1.0  # Cannot convert a disjunction into a conjunction
                elif y.type == Grouping.OR:
                    return float(total_cost + len(S2.difference(S1_inv))) / float(
                        len(matches) + len(S2.difference(S1_inv)))
                else:
                    return 1.0  # Contradiction
            elif x.type == Grouping.NOT:
                if y.type == Grouping.NOT:
                    return self.entity_distance(x.entities[0], y.entities[0])
                else:
                    return 1.0

    @functools.lru_cache
    def edge_distance(self, x: Relationship, y: Relationship):
        # L = (x.source.named_entity,x.edgeLabel.named_entity,x.target.named_entity)
        # R = (y.source.named_entity,y.edgeLabel.named_entity,y.target.named_entity)
        # print (str(L) +" vs "+str(R))
        srcSim = 1.0 - self.entity_distance(x.source, y.source)
        dstSim = 1.0 - self.entity_distance(x.target, y.target)
        edgeSim = 1.0 - self.singleton_dist(x.edgeLabel, y.edgeLabel, True) * (1 if x.isNegated == y.isNegated else 0)
        return 1.0 - (srcSim * dstSim * edgeSim)

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
        unmatchingSimilarity = 1.0 - (unmatchingDistance / (1 + unmatchingDistance))
        totalSimilarity = 1.0 - (total_cost / (1 + total_cost))
        # total_cost += ((len(S1.difference(S2_inv)) + len(S2.difference(S1_inv))) / 2.0)
        return 1.0 - totalSimilarity * unmatchingSimilarity


def load_file_for_similarity(cfg, result_json):
    with (open(result_json) as user_file):  # result.json from C++
        parsed_json = json.load(user_file)

        number_of_nodes = range(len(parsed_json))
        edges = []
        nodes = {}

        # Get all nodes from resulting graph and create list of Singletons
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
                    properties=frozenset(item['properties'].items()),
                    min=int(item['properties']['begin']),
                    max=int(item['properties']['end']),
                    type="None",
                    confidence=0
                )

        # Check if conjugation ('conj') exists and if true exists, merge into SetOfSingletons
        # Also if 'compound' relationship is present, merge parent and child nodes
        for row in number_of_nodes:
            item = parsed_json[row]
            grouped_nodes = []
            has_conj = 'conj' in item['properties']
            is_compound = False
            if has_conj:
                conj = item['properties']['conj']
                if 'and' in conj:
                    group_type = Grouping.AND
                elif 'or' in conj:
                    group_type = Grouping.OR
                else:
                    group_type = Grouping.NONE
                for edge in item['phi']:
                    if 'orig' in edge['containment']:
                        grouped_nodes.append(nodes[edge['content']])
            else:
                for edge in item['phi']:
                    is_compound = 'compound' in edge['containment']
                    if is_compound:
                        grouped_nodes.append(nodes[edge['score']['child']])

            if has_conj:
                nodes[item['id']] = SetOfSingletons(
                    type=group_type,
                    entities=tuple(grouped_nodes),
                    min=min(grouped_nodes, key=lambda x: x.min).min,
                    max=max(grouped_nodes, key=lambda x: x.max).max,
                    confidence=-1
                )
            elif is_compound:
                grouped_nodes.insert(0, nodes[item['id']])
                nodes[item['id']] = SetOfSingletons(
                    type=Grouping.GROUPING,
                    entities=tuple(grouped_nodes),
                    min=min(grouped_nodes, key=lambda x: x.min).min,
                    max=max(grouped_nodes, key=lambda x: x.max).max,
                    confidence=-1
                )

        # print("nodes", nodes)

        # Loop over resulting graph again and create array of edges now we have all Singletons
        if 'crawl_to_gsm' in cfg:
            if 'stanza_db' in cfg['crawl_to_gsm']:
                with open(cfg['crawl_to_gsm']['stanza_db']) as stanza_db_file:
                    stanza_json = json.load(stanza_db_file)

                    # Assign types to nodes
                    for key in nodes:
                        item = nodes[key]

                        # If key is SetOfSingletons, loop over each Singleton and make association to type
                        if isinstance(item, SetOfSingletons):
                            for entity in item.entities:
                                nodes = assign_type_to_singleton(entity, stanza_json, nodes, key)
                        else:
                            nodes = assign_type_to_singleton(item, stanza_json, nodes, key)

                    # With types assigned, merge SetOfSingletons into Singleton
                    for key in nodes:
                        item = nodes[key]

                        if isinstance(item, SetOfSingletons):
                            if item.type == Grouping.GROUPING:
                                if 'rewriting_strategy' in cfg and cfg['rewriting_strategy'] is not None:
                                    simplistic = cfg['rewriting_strategy'] == 'simplistic'
                                    nodes = merge_set_of_singletons(item, nodes, key, simplistic)

                    # Check for negation in node 'xi' and 'properties
                    for key in nodes:
                        grouped_nodes = []
                        sing_item = nodes[key]  # Singleton node

                        for row in range(len(parsed_json)):  # Find node in JSON so we can get child nodes
                            json_item = parsed_json[row]
                            is_prop_negated = False

                            for prop_key in json_item['properties']:  # Check properties for negation
                                prop = json_item['properties'][prop_key]
                                if prop in negations:
                                    is_prop_negated = True

                            # Check if name is not/no or if negation found in properties
                            if key == json_item['id']:
                                if sing_item.named_entity in negations:
                                    for edge in json_item['phi']:
                                        child = nodes[edge['score']['child']]
                                        if child.named_entity not in negations:
                                            grouped_nodes.append(child)
                                            nodes[key] = SetOfSingletons(
                                                type=Grouping.NOT,
                                                entities=tuple(grouped_nodes),
                                                min=min(grouped_nodes, key=lambda x: x.min).min,
                                                max=max(grouped_nodes, key=lambda x: x.max).max,
                                                confidence=-1
                                            )
                                elif is_prop_negated:
                                    nodes[key] = SetOfSingletons(
                                        type=Grouping.NOT,
                                        entities=tuple([sing_item]),
                                        min=sing_item.min,
                                        max=sing_item.max,
                                        confidence=-1
                                    )

                    # print(nodes)

                    for row in range(len(parsed_json)):
                        item = parsed_json[row]
                        for edge in item['phi']:
                            # Make sure current edge is not in list of rejected edges, e.g. 'compound'
                            with open(cfg['rejected_edge_types'], 'r') as f:
                                rejected_edges = f.read()
                                if edge['containment'] not in rejected_edges:
                                    if 'orig' not in edge['containment']:
                                        x = edge['containment']  # Name of edge label

                                        for name in negations:  # No / not
                                            x = re.sub("\b(" + name + ")\b", " ", x)
                                        x = x.strip()  # Strip of leading/trailing whitespace

                                        has_negations = any(map(lambda x: x in edge['containment'], negations))

                                        # Check if name of edge is in "non verbs"
                                        edge_type = "verb"
                                        with open(cfg['non_verbs'], "r") as f:
                                            non_verbs = f.readlines()
                                            for non_verb in non_verbs:
                                                if x == non_verb.strip():
                                                    edge_type = "non_verb"
                                                    break

                                        edges.append(Relationship(
                                            source=nodes[edge['score']['parent']],
                                            target=nodes[edge['score']['child']],
                                            edgeLabel=Singleton(named_entity=x, properties=frozenset(dict().items()),
                                                                min=-1,
                                                                max=-1, type=edge_type,
                                                                confidence=nodes[item['id']].confidence),
                                            isNegated=has_negations
                                        ))
        print(json.dumps(Graph(edges=edges), cls=EnhancedJSONEncoder))

        # sentence = create_sentence_obj(cfg, edges, nodes)
        # print(json.dumps(sentence, cls=EnhancedJSONEncoder))

        return Graph(edges=edges)


def create_sentence_obj(cfg, edges, nodes):
    if len(edges) <= 0:
        create_existential(edges, nodes)
    # With graph created, make the 'Sentence' object
    kernel = None
    properties = defaultdict(list)
    for edge in edges:
        if edge.edgeLabel.type == "verb":
            # If not a transitive verb, remove target as target reflects direct object
            with open(cfg['transitive_verbs'], "r") as f:
                transitive_verbs = f.read()
                if edge.edgeLabel.named_entity not in transitive_verbs:
                    kernel = Relationship(
                        source=edge.source,
                        target=None,
                        edgeLabel=edge.edgeLabel,
                        isNegated=edge.isNegated
                    )
                else:
                    kernel = edge
    # If kernel is none, look for existential
    if kernel is None:
        for edge in edges:
            if isinstance(edge.source, SetOfSingletons):
                for entity in edge.target.entities:
                    for prop in entity.properties:
                        if prop[1] == '∃':
                            kernel = edge
                            break
            else:
                for prop in edge.target.properties:
                    if prop[1] == '∃':
                        kernel = edge
                        break
    if kernel is None:
        n = len(edges)
        create_existential(edges, nodes)

        if n < len(edges):
            kernel = edges[-1]
    kernel_nodes = set()
    if kernel is not None:
        if kernel.source is not None:
            kernel_nodes.add(kernel.source)
        if kernel.target is not None:
            kernel_nodes.add(kernel.target)
    for edge in edges:
        if edge.edgeLabel.type == "non_verb":
            if edge.source not in kernel_nodes:
                properties[edge.source.type if isinstance(edge.source.type, str) else edge.source.type.name].append(
                    edge.source)
            if edge.target not in kernel_nodes:
                properties[edge.target.type if isinstance(edge.target.type, str) else edge.target.type.name].append(
                    edge.target)
    sentence = Sentence(
        kernel=kernel,
        properties=dict(properties)
    )
    return sentence


def create_existential(edges, nodes):
    for key in nodes:
        node = nodes[key]
        for prop in dict(node.properties):
            if 'kernel' in prop:
                edges.append(Relationship(
                    source=node,
                    target=Singleton(
                        named_entity="there",
                        properties=frozenset(dict().items()),
                        min=-1,
                        max=-1,
                        type="non_verb",
                        confidence=-1
                    ),
                    edgeLabel=Singleton(
                        named_entity="is",
                        properties=frozenset(dict().items()),
                        min=-1,
                        max=-1,
                        type="verb",
                        confidence=-1
                    ),
                    isNegated=False
                ))

                return


def assign_type_to_singleton(item, stanza_json, nodes, key):
    associations = dict()

    # TODO: merge the nodes together that belong to the same spatio-temporal entities,
    #       or multi-named entities known from ConceptNet5

    # Compare overlap of min begin and max end char from MEU and edges like "compound" etc.
    meu_entities = []
    entities = []

    # Loop over Stanza MEU and GSM result and evaluate overlapping words from chars
    for stanza_row in range(len(stanza_json)):
        stanza_item = stanza_json[stanza_row]
        for meu in stanza_item['multi_entity_unit']:
            start_meu = meu['start_char']
            end_meu = meu['end_char']

            start_graph = item.min
            end_graph = item.max

            # https://scicomp.stackexchange.com/questions/26258/the-easiest-way-to-find-intersection-of-two-intervals/26260#26260
            if start_graph > end_meu or start_meu > end_graph:
                continue
            else:
                start_intersection = max(start_meu, start_graph)
                end_intersection = min(end_meu, end_graph)

                if start_graph >= start_intersection and start_meu >= start_intersection and \
                        end_graph <= end_intersection and end_meu <= end_intersection:
                    if meu not in meu_entities:
                        meu_entities.append(meu)
                    if item not in entities:
                        entities.append(item)

    associations[item] = entities

    # print(associations[item])
    # print(meu_entities)

    for association in associations[item]:
        if len(meu_entities) > 0:
            best_item = max(meu_entities, key=lambda y: y['confidence'])
            item = Singleton(
                named_entity=association.named_entity,
                properties=association.properties,
                min=association.min,
                max=association.max,
                type=best_item['type'],
                confidence=best_item['confidence']
            )

            if isinstance(nodes[key], SetOfSingletons):
                new_set = []
                confidence = 1
                for entity in nodes[key].entities:
                    if (entity.confidence < best_item['confidence'] or math.isnan(best_item['confidence'])) and \
                            item.named_entity == entity.named_entity:  # Should this be == or in?
                        new_set.append(item)
                        confidence *= item.confidence
                    else:
                        new_set.append(entity)
                        confidence *= entity.confidence

                set_item = SetOfSingletons(
                    type=Grouping.GROUPING,
                    entities=tuple(new_set),
                    min=nodes[key].min,
                    max=nodes[key].max,
                    confidence=confidence
                )
                nodes[key] = set_item
            else:
                if nodes[key].confidence < best_item['confidence'] or math.isnan(best_item['confidence']):
                    nodes[key] = item
                else:
                    nodes[key] = association

    return nodes


def merge_set_of_singletons(item, nodes, key, simplistic):
    chosen_entity = None
    extra = ""
    norm_confidence = 1
    fusion_properties = dict()

    # Sort entities based on word position to keep correct order
    sorted_entities = sorted(item.entities, key=lambda x: float(dict(x.properties)['pos']))
    for entity in sorted_entities:
        norm_confidence *= entity.confidence
        fusion_properties = fusion_properties | dict(entity.properties)  # TODO: Most properties are overwritten?

        if entity.type != "ENTITY" and not simplistic:
            chosen_entity = entity
        else:
            # Ensure there is no leading space
            extra = " ".join((extra, entity.named_entity))

    extra = extra.strip()  # Remove whitespace

    if chosen_entity is None and not simplistic:
        # TODO: Later we will use Prostgres

        # Null new properties for ? object
        new_properties = {
            "specification": "none",
            "begin": str(sorted_entities[0].min),
            "end": str(sorted_entities[len(sorted_entities) - 1].max),
            "pos": str(dict(sorted_entities[0].properties)['pos']),
            "number": "none",
            "extra": extra
        }

        new_properties = new_properties | fusion_properties

        new_item = Singleton(
            named_entity="?",
            properties=frozenset(new_properties.items()),
            min=sorted_entities[0].min,
            max=sorted_entities[len(sorted_entities) - 1].max,
            type='None',
            confidence=norm_confidence
        )
    elif chosen_entity is not None and not simplistic:
        # Convert back from frozenset to append new "extra" attribute
        new_properties = dict(chosen_entity.properties)
        new_properties["extra"] = extra

        new_item = Singleton(
            named_entity=chosen_entity.named_entity,
            properties=frozenset(new_properties.items()),
            min=sorted_entities[0].min,
            max=sorted_entities[len(sorted_entities) - 1].max,
            type=chosen_entity.type,
            confidence=norm_confidence
        )
    elif simplistic:
        new_properties = {
            "specification": "none",
            "begin": str(sorted_entities[0].min),
            "end": str(sorted_entities[len(sorted_entities) - 1].max),
            "pos": str(dict(sorted_entities[0].properties)['pos']),
            "number": "none"
            # "extra": extra  # This attribute is used as named_entity so no longer needed in properties
        }

        new_properties = new_properties | fusion_properties

        if chosen_entity is not None:
            # TODO: Postgres
            type = chosen_entity.type
        else:
            type = "ENTITY"

        new_item = Singleton(
            named_entity=extra,
            properties=frozenset(new_properties.items()),
            min=sorted_entities[0].min,
            max=sorted_entities[len(sorted_entities) - 1].max,
            type=type,  # TODO: What should this type be?
            confidence=norm_confidence
        )
    else:
        print("Error")

    nodes[key] = new_item

    return nodes


if __name__ == '__main__':
    # TODO: Load all graph results from output of GSM C++ code
    result_json = './result.json'
    print(load_file_for_similarity(result_json))
