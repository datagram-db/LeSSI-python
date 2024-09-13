__author__ = "Oliver R. Fox, Giacomo Bergami"
__copyright__ = "Copyright 2024, Oliver R. Fox, Giacomo Bergami"
__credits__ = ["Oliver R. Fox, Giacomo Bergami"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Oliver R. Fox, Giacomo Bergami"
__status__ = "Production"

import json
import math
from collections import defaultdict, deque
from copy import copy

import numpy

from gsmtosimilarity.graph_similarity import EnhancedJSONEncoder, negations, lemmatizer, Graph
from inference_engine.EntityRelationship import Singleton, SetOfSingletons, Grouping, Relationship, replaceNamed
from inference_engine.Sentence import Sentence

from allChunks import allChunks
from itertools import repeat


def most_specific_type(types):
    if "GPE" in types:
        return "GPE"
    elif "LOC" in types:
        return "LOC"
    elif "ORG" in types:
        return "ORG"
    elif "noun" in types:
        return "noun"
    elif "ENTITY" in types:
        return "ENTITY"
    else:
        return "None"


def score_from_meu(min_value, max_value, item_type, stanza_row):
    max_value = max_value
    matched_meus = []

    for meu in stanza_row['multi_entity_unit']:
        start_meu = meu['start_char']
        end_meu = meu['end_char']
        if min_value == start_meu and end_meu == max_value:
            # TODO: mgu or its opposite...
            if (most_specific_type([item_type, meu['type']]) == meu['type'] or
                    item_type == meu['type'] or
                    item_type == "None"):
                matched_meus.append(meu)

    if len(matched_meus) == 0:
        return 0, "None"
    else:
        max_score = max(map(lambda x: x['confidence'], matched_meus))
        return max_score, most_specific_type(
            list(map(lambda x: x['type'], filter(lambda x: x['confidence'] == max_score, matched_meus))))


def merge_set_of_singletons(item, simplistic, stanza_row):
    chosen_entity = None
    extra = ""
    norm_confidence = 1
    fusion_properties = dict()

    # Sort entities based on word position to keep correct order
    sorted_entities = sorted(item.entities, key=lambda x: float(dict(x.properties)['pos']))

    sorted_entity_names = list(map(getattr, sorted_entities, repeat('named_entity')))
    d = dict(zip(range(len(sorted_entity_names)), sorted_entity_names))  # dictionary for storing the replacing elements
    for x in allChunks(list(d.keys())):
        if all(y in d for y in x):
            exp = " ".join(map(lambda z: sorted_entity_names[z], x))
            min_value = min(map(lambda z: sorted_entities[z].min, x))
            max_value = max(map(lambda z: sorted_entities[z].max, x))
            # max_value = min_value + len(exp)

            all_types = [sorted_entities[z].type for z in x]
            specific_type = most_specific_type(all_types)
            candidate_meu_score, candidate_meu_type = score_from_meu(min_value, max_value, specific_type, stanza_row)
            allProd = numpy.prod(list(map(lambda z: sorted_entities[z].confidence, x)))

            # if (score_from_meu(exp, min_value, max_value, specific_type, stanza_row) >=
            #         numpy.prod(list(map(lambda z: score_from_meu(sorted_entities[z].named_entity, sorted_entities[z].min, max_value, sorted_entities[z].type, stanza_row), x)))):
            if ((candidate_meu_score >= allProd) or
                    ((specific_type != candidate_meu_type) and (
                            most_specific_type([specific_type, candidate_meu_type]) == candidate_meu_type))):
                candidate_delete = set()
                for k, v in d.items():
                    if isinstance(k, int):
                        if k in x:
                            candidate_delete.add(k)
                    elif isinstance(k, tuple):
                        if len(set(x).intersection(set(k))) > 0:
                            candidate_delete.add(k)
                for z in candidate_delete:
                    d.pop(z)
                d[x] = exp
    print(d)

    # for entity in sorted_entities:
    #     norm_confidence *= entity.confidence
    #     fusion_properties = fusion_properties | dict(entity.properties)  # TODO: Most properties are overwritten?
    #     # Giacomo: then, we'd need to use a defaultdict(list) and merge them as https://stackoverflow.com/a/70689832/1376095
    #     if entity.type != "ENTITY" and entity.type != 'noun' and not simplistic and chosen_entity is None:  # TODO: FIX CHOSEN ENTITY NOT NONE
    #         chosen_entity = entity
    #     else:
    #         extra = " ".join((extra, entity.named_entity))  # Ensure there is no leading space

    # TODO: Remove time-space information and add as properties
    for entity in sorted_entities:
        norm_confidence *= entity.confidence
        fusion_properties = fusion_properties | dict(entity.properties)  # TODO: Most properties are overwritten?
        if entity.named_entity == list(d.values())[0]:
            chosen_entity = entity
        else:
            extra = " ".join((extra, entity.named_entity))  # Ensure there is no leading space

    extra = extra.strip()  # Remove whitespace

    if simplistic:
        new_properties = {
            "specification": "none",
            "begin": str(sorted_entities[0].min),
            "end": str(sorted_entities[len(sorted_entities) - 1].max),
            "pos": str(dict(sorted_entities[0].properties)['pos']),
            "number": "none"
        }

        new_properties = new_properties | fusion_properties

        if chosen_entity is not None:
            type = chosen_entity.type
        else:
            type = "ENTITY"

        new_item = Singleton(
            id=item.id,
            named_entity=extra,
            properties=frozenset(new_properties.items()),
            min=sorted_entities[0].min,
            max=sorted_entities[len(sorted_entities) - 1].max,
            type=type,  # TODO: What should this type be?
            confidence=norm_confidence
        )
    elif chosen_entity is None:  # Not simplistic
        if extra != '':
            name = extra
            extra = ''
        else:
            name = "?"
        # New properties for ? object
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
            id=item.id,
            named_entity=name,
            properties=frozenset(new_properties.items()),
            min=sorted_entities[0].min,
            max=sorted_entities[len(sorted_entities) - 1].max,
            type='None',
            confidence=norm_confidence
        )
    elif chosen_entity is not None:  # Not simplistic
        # Convert back from frozenset to append new "extra" attribute
        new_properties = dict(chosen_entity.properties)
        new_properties["extra"] = extra

        new_item = Singleton(
            id=item.id,
            named_entity=chosen_entity.named_entity,
            properties=frozenset(new_properties.items()),
            min=sorted_entities[0].min,
            max=sorted_entities[len(sorted_entities) - 1].max,
            type=chosen_entity.type,
            confidence=norm_confidence
        )
    else:
        print("Error")

    return new_item


def associate_to_container(item, nbb):
    if isinstance(item, SetOfSingletons):
        confidence = 1.0
        new_set = list(map(lambda x: associate_to_container(x, nbb), item.entities))
        for entity in new_set:  # nodes_key.entities:
            confidence *= entity.confidence

        set_item = SetOfSingletons(
            id=item.id,
            type=item.type,
            entities=tuple(new_set),
            min=item.min,
            max=item.max,
            confidence=confidence
        )
        return set_item
    else:
        if item not in nbb:
            nbb[item] = item
            return item
        else:
            return nbb[item]


class AssignTypeToSingleton:
    def __init__(self):
        self.associations = set()
        self.meu_entities = defaultdict(set)
        self.final_assigment = dict()

    def assign_type_to_singleton_1(self, item, stanza_row):
        # Loop over Stanza MEU and GSM result and evaluate overlapping words from chars
        for meu in stanza_row['multi_entity_unit']:
            start_meu = meu['start_char']
            end_meu = meu['end_char']
            start_graph = item.min
            end_graph = item.max
            # https://scicomp.stackexchange.com/questions/26258/the-easiest-way-to-find-intersection-of-two-intervals/26260#26260
            if start_graph > end_meu or start_meu > end_graph:
                continue
            else:
                # start_intersection = max(start_meu, start_graph)
                # end_intersection = min(end_meu, end_graph)
                if not (start_graph > end_meu or start_meu > end_graph):
                    self.meu_entities[item].add(frozenset(meu.items()))
                    self.associations.add(item)
                # if start_graph >= start_intersection and start_meu >= start_intersection and \
                #         end_graph <= end_intersection and end_meu <= end_intersection:
                #     if meu not in meu_entities:
                #         meu_entities.append(meu)
                #     if item not in entities:
                #         entities.append(item)
        # self.associations[item] = entities
        # print(associations[item])
        # print(meu_entities)

    def assign_type_to_all_singletons(self):
        if len(self.final_assigment) > 0:
            return self.final_assigment
        for item in self.associations:
            # for association in associations:
            if len(self.meu_entities[item]) > 0:
                if item.type == '∃' or item.type.startswith("JJ") or item.type.startswith("IN") or item.type.startswith(
                        "NEG"):
                    best_score = item.confidence
                    best_items = [item]
                    best_type = item.type
                else:
                    best_score = max(map(lambda y: dict(y)['confidence'], self.meu_entities[item]))
                    best_items = [dict(y) for y in self.meu_entities[item] if dict(y)['confidence'] == best_score]
                    best_type = None
                    if len(best_items) == 1:
                        best_item = best_items[0]
                        best_type = best_item['type']
                    else:
                        best_types = list(set(map(lambda best_item: best_item['type'], best_items)))
                        best_type = None
                        if len(best_types) == 1:
                            best_type = best_types[0]
                        ## TODO! type disambiguation, in future works, needs to take into account also the verb associated to it!
                        elif "PERSON" in best_types:
                            best_type = "PERSON"
                        elif "DATE" in best_types or "TIME" in best_types:
                            best_type = "DATE"
                        elif "GPE" in best_types:
                            best_type = "GPE"
                        elif "LOC" in best_types:
                            best_type = "LOC"
                        else:
                            best_type = "None"
                self.final_assigment[item] = Singleton(
                    id=item.id,
                    named_entity=item.named_entity,
                    properties=item.properties,
                    min=item.min,
                    max=item.max,
                    type=best_type,
                    confidence=best_score
                )
                # if isinstance(association, Singleton):
                #
                # else:
                #     self.final_assigment[item] = association
        return self.final_assigment


atts_global = AssignTypeToSingleton()


def assign_to_all():
    return atts_global.assign_type_to_all_singletons()


def assign_type_to_singleton(item, stanza_row, nodes, key):
    atts_global.assign_type_to_singleton_1(item, stanza_row)


def create_existential(edges, nodes):
    for key in nodes:
        node = nodes[key]
        for prop in dict(node.properties):
            if 'kernel' in prop or len(nodes) == 1:
                edges.append(Relationship(
                    source=node,
                    target=Singleton(
                        id=-1,
                        named_entity="there",
                        properties=frozenset(dict().items()),
                        min=-1,
                        max=-1,
                        type="non_verb",
                        confidence=-1
                    ),
                    edgeLabel=Singleton(
                        id=-1,
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


def create_cop(edge, kernel, targetOrSource):
    if targetOrSource == 'target':
        temp_prop = dict(copy(kernel.target.properties))
        target_json = json.dumps(edge.target, cls=EnhancedJSONEncoder)
        target_dict = dict(json.loads(target_json))
        temp_prop['cop'] = target_dict
        new_target = Singleton(
            id=kernel.target.id,
            named_entity=kernel.target.named_entity,
            properties=temp_prop,
            min=kernel.target.min,
            max=kernel.target.max,
            type=kernel.target.type,
            confidence=kernel.target.confidence
        )
        kernel = Relationship(
            source=kernel.source,
            target=new_target,
            edgeLabel=kernel.edgeLabel,
            isNegated=kernel.isNegated
        )
    else:
        temp_prop = dict(copy(kernel.source.properties))
        target_json = json.dumps(edge.source, cls=EnhancedJSONEncoder)
        target_dict = dict(json.loads(target_json))
        temp_prop['cop'] = target_dict
        new_source = Singleton(
            id=kernel.source.id,
            named_entity=kernel.source.named_entity,
            properties=temp_prop,
            min=kernel.source.min,
            max=kernel.source.max,
            type=kernel.source.type,
            confidence=kernel.source.confidence
        )
        kernel = Relationship(
            source=new_source,
            target=kernel.target,
            edgeLabel=kernel.edgeLabel,
            isNegated=kernel.isNegated
        )
    return kernel


def create_sentence_obj(cfg, edges, nodes, transitive_verbs, legacy):
    if len(edges) <= 0:
        create_existential(edges, nodes)
    # With graph created, make the 'Sentence' object
    kernel = None
    properties = defaultdict(list)
    for edge in edges:
        if edge.edgeLabel.type == "verb":
            edge_label = edge.edgeLabel
            if edge.isNegated:
                for name in negations:
                    if name in edge_label.named_entity:
                        edge_label_name = edge_label.named_entity.replace(name, "")
                        edge_label_name = edge_label_name.strip()
                        edge_label = Singleton(edge_label.id, edge_label_name, edge_label.properties, edge_label.min, edge_label.max,
                                               edge_label.type, edge_label.confidence)
                        break

            # If not a transitive verb, remove target as target reflects direct object
            if len(legacy.lemmatize_sentence(edge.edgeLabel.named_entity).intersection(transitive_verbs)) == 0:
                kernel = Relationship(
                    source=edge.source,
                    target=None,
                    edgeLabel=edge_label,
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

        if n <= len(edges):
            kernel = edges[-1]
    kernel_nodes = set()
    if kernel is not None:
        if kernel.source is not None:
            kernel_nodes.add(kernel.source)
        if kernel.target is not None:
            kernel_nodes.add(kernel.target)
    for edge in edges:
        type_key = edge.source.type if isinstance(edge.source.type, str) else edge.source.type.name

        # Source
        if type_key == 'JJ' or type_key == 'JJS':
            kernel = create_cop(edge, kernel, 'source')
            continue
        if type_key not in 'NEG':
            if edge.source.type == Grouping.MULTIINDIRECT:
                continue
            elif edge.source not in kernel_nodes and edge.source not in properties[type_key]:
                properties[type_key].append(edge.source)
        type_key = edge.target.type if isinstance(edge.target.type, str) else edge.target.type.name

        # Target
        if type_key == 'JJ' or type_key == 'JJS':
            kernel = create_cop(edge, kernel, 'target')
            continue
        if type_key not in 'NEG':
            if edge.target.type == Grouping.MULTIINDIRECT:
                continue
                # for target_edge in edge.target.entities:
                #     type_key2 = target_edge.type if isinstance(target_edge.type, str) else target_edge.type.name
                #     if type_key2 not in 'NEG':
                #         if target_edge not in kernel_nodes and target_edge not in properties[type_key2]:
                #             properties[type_key2].append(target_edge)
            elif edge.target not in kernel_nodes and edge.target not in properties[type_key]:
                properties[type_key].append(edge.target)

    from gsmtosimilarity.stanza_pipeline import StanzaService
    el = " ".join(map(lambda y: y["lemma"], filter(lambda x: x["upos"] != "AUX", StanzaService().stNLP(
        lemmatizer.lemmatize(kernel.edgeLabel.named_entity, 'v')).to_dict()[0])))
    sentence = Sentence(
        kernel=Relationship(
            source=kernel.source,
            target=kernel.target,
            edgeLabel=replaceNamed(kernel.edgeLabel, el),
            isNegated=kernel.isNegated
        ),
        properties=dict(properties)
    )
    from logical_repr.rewrite_kernels import rewrite_kernels
    final = rewrite_kernels(sentence)
    print(json.dumps(final, cls=EnhancedJSONEncoder))
    return final


def group_nodes(nodes, parsed_json, simplsitic):
    # Get all nodes from resulting graph and create list of Singletons
    number_of_nodes = range(len(parsed_json))
    for row in number_of_nodes:
        item = parsed_json[row]
        if 'conj' in item['properties'] or 'multipleindobj' in item['ell']:
            continue  # add set of singletons later as we might not have all nodes yet
        else:
            minV = -1
            maxV = -1
            typeV = "None"
            if len(item['xi']) > 0:
                name = item['xi'][0]
                minV = int(item['properties']['begin'])
                maxV = int(item['properties']['end'])
                typeV = item['ell'][0] if len(item['ell']) > 0 else "None"
            else:
                name = '?'  # xi might be empty if the node is invented

            nodes[item['id']] = Singleton(
                id=item['id'],
                named_entity=name,
                properties=frozenset(item['properties'].items()),
                min=minV,
                max=maxV,
                type=typeV,
                confidence=1.0
            )
    # Check if conjugation ('conj') exists and if true exists, merge into SetOfSingletons
    # Also if 'compound' relationship is present, merge parent and child nodes
    for row in number_of_nodes:
        item = parsed_json[row]
        grouped_nodes = []
        has_conj = 'conj' in item['properties']
        has_multipleindobj = 'multipleindobj' in item['ell']
        is_compound = False
        group_type = None
        norm_confidence = 1.0
        if has_conj:
            conj = item['properties']['conj'].strip()
            if len(conj) == 0:
                conj = bfs(parsed_json, item['id'])

            if 'and' in conj or 'but' in conj:
                group_type = Grouping.AND
            elif ('nor' in conj) or ('neither' in conj):
                group_type = Grouping.NEITHER
            elif 'or' in conj:
                group_type = Grouping.OR
            else:
                group_type = Grouping.NONE
            for edge in item['phi']:
                if 'orig' in edge['containment']:
                    node = nodes[edge['content']]
                    grouped_nodes.append(node)
                    norm_confidence *= node.confidence
        elif has_multipleindobj:
            for edge in item['phi']:
                if 'orig' in edge['containment']:
                    node = nodes[edge['content']]
                    grouped_nodes.append(node)
                    norm_confidence *= node.confidence
        else:
            for edge in item['phi']:
                is_current_edge_compound = 'compound' in edge['containment']
                if is_current_edge_compound:
                    is_compound = True
                    node = nodes[edge['score']['child']]
                    grouped_nodes.append(node)
                    norm_confidence *= node.confidence

        if simplsitic and len(grouped_nodes) > 0:
            sorted_entities = sorted(grouped_nodes, key=lambda x: float(dict(x.properties)['pos']))
            sorted_entity_names = list(map(getattr, sorted_entities, repeat('named_entity')))

            all_types = list(map(getattr, sorted_entities, repeat('type')))
            specific_type = most_specific_type(all_types)

            if group_type == Grouping.OR:
                name = " or ".join(sorted_entity_names)
            elif group_type == Grouping.AND:
                name = " and ".join(sorted_entity_names)
            elif group_type == Grouping.NEITHER:
                name = " nor ".join(sorted_entity_names)
                name = f"neither {name}"
            else:
                name = " ".join(sorted_entity_names)

            nodes[item['id']] = Singleton(
                id=item['id'],
                named_entity=name,
                properties=frozenset(item['properties'].items()),
                min=min(grouped_nodes, key=lambda x: x.min).min,
                max=max(grouped_nodes, key=lambda x: x.max).max,
                type=specific_type,
                confidence=norm_confidence
            )
        elif not simplsitic:
            if has_conj:
                if group_type == Grouping.NEITHER:
                    grouped_nodes = [SetOfSingletons(id=x.id, type=Grouping.NOT, entities=tuple([x]), min=x.min, max=x.max,
                                                     confidence=x.confidence) for x in grouped_nodes]
                    grouped_nodes = tuple(grouped_nodes)
                    group_type = Grouping.AND
                nodes[item['id']] = SetOfSingletons(
                    id=item['id'],
                    type=group_type,
                    entities=tuple(grouped_nodes),
                    min=min(grouped_nodes, key=lambda x: x.min).min,
                    max=max(grouped_nodes, key=lambda x: x.max).max,
                    confidence=norm_confidence
                )
            elif is_compound:
                grouped_nodes.insert(0, nodes[item['id']])
                nodes[item['id']] = SetOfSingletons(
                    id=item['id'],
                    type=Grouping.GROUPING,
                    entities=tuple(grouped_nodes),
                    min=min(grouped_nodes, key=lambda x: x.min).min,
                    max=max(grouped_nodes, key=lambda x: x.max).max,
                    confidence=norm_confidence
                )
            elif has_multipleindobj:
                nodes[item['id']] = SetOfSingletons(
                    id=item['id'],
                    type=Grouping.MULTIINDIRECT,
                    entities=tuple(grouped_nodes),
                    min=min(grouped_nodes, key=lambda x: x.min).min,
                    max=max(grouped_nodes, key=lambda x: x.max).max,
                    confidence=norm_confidence
                )


def bfs(lists, s):
    nodes = {x['id']:x for x in lists}

    visited = set()

    # Create a queue for BFS
    q = deque()

    # Mark the source node as visited and enqueue it
    visited.add(s)
    q.append(s)

    # Iterate over the queue
    while q:

        # Dequeue a vertex from queue and print it
        id = q.popleft()

        if 'cc' in nodes[id]['properties']:
            return nodes[id]['properties']['cc']

        # Get all adjacent vertices of the dequeued
        # vertex. If an adjacent has not been visited,
        # mark it visited and enqueue it
        for edge in nodes[id]['phi']:
            dst = edge['score']['child']
            if dst not in visited:
                visited.add(dst)
                q.append(dst)

    return ''


def assign_singletons(parsed_json, stanza_row, simplsitic):
    nodes = {}
    group_nodes(nodes, parsed_json, simplsitic)

    # Loop over resulting graph again and create array of edges now we have all Singletons
    if stanza_row is not None:
        for key in nodes:
            associate_type_to_item(nodes[key], key, nodes, stanza_row)  # Assign types to nodes
    return nodes


def to_internal_graph(parsed_json, stanza_row, rejected_edges, non_verbs, do_rewriting, is_rewriting_simplistic, nodes):
    # Loop over resulting graph again and create array of edges now we have all Singletons
    edges = []
    nbb = assign_to_all()  # Assign types to nodes
    if stanza_row is not None:
        for key in nodes:
            item = nodes[key]
            if not isinstance(item, SetOfSingletons):
                nodes[key] = associate_to_container(item, nbb)

        for key in nodes:
            item = nodes[key]
            if isinstance(item, SetOfSingletons):
                nodes[key] = associate_to_container(item, nbb)


        # With types assigned, merge SetOfSingletons into Singleton
        for key in nodes:
            item = nodes[key]
            if isinstance(item, SetOfSingletons) and do_rewriting:
                if item.type == Grouping.MULTIINDIRECT:
                    # If entities is only 1 item, then we can simply replace the item.id
                    if len(item.entities) == 1:
                        entity = item.entities[0]
                        if isinstance(entity, SetOfSingletons):
                            nodes[item.id] = merge_set_of_singletons(entity, is_rewriting_simplistic, stanza_row)
                        else:
                            nodes[item.id] = associate_to_container(entity, nbb)
                    # If more than 1 item, then we replace the entity.id for each orig of the 'multiindirectobj'
                    else:
                        # nodes[item.id] = associate_to_container(item, nbb)
                        for entity in item.entities:
                            if isinstance(entity, SetOfSingletons):
                                nodes[entity.id] = merge_set_of_singletons(entity, is_rewriting_simplistic, stanza_row)
                            else:
                                nodes[entity.id] = associate_to_container(entity, nbb)
                    # grouped_nodes = list(
                    #     map(lambda x: merge_set_of_singletons(x, is_rewriting_simplistic, stanza_row),
                    #         item.entities))
                    # nodes[key] = SetOfSingletons(  # Do not know the key
                    #     type=Grouping.MULTIINDIRECT,
                    #     entities=tuple(grouped_nodes),
                    #     min=min(grouped_nodes, key=lambda x: x.min).min,
                    #     max=max(grouped_nodes, key=lambda x: x.max).max,
                    #     confidence=item.confidence
                    # )
                if item.type == Grouping.GROUPING:
                    # TODO: MAYBE NOT WORKING?
                    nodes[key] = merge_set_of_singletons(item, is_rewriting_simplistic, stanza_row)

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
                    ## TODO: there was a case where sing_item didn't have the field named_entity
                    ##       Please double check if this will fix it...
                    if hasattr(sing_item, "named_entity") and sing_item.named_entity in negations:
                        for edge in json_item['phi']:
                            child = nodes[edge['score']['child']]
                            if child.named_entity not in negations:
                                grouped_nodes.append(child)
                                nodes[key] = SetOfSingletons(
                                    type=Grouping.NOT,
                                    entities=tuple(grouped_nodes),
                                    min=min(grouped_nodes, key=lambda x: x.min).min,
                                    max=max(grouped_nodes, key=lambda x: x.max).max,
                                    confidence=child.confidence
                                )
                    elif is_prop_negated:
                        nodes[key] = SetOfSingletons(
                            type=Grouping.NOT,
                            entities=tuple([sing_item]),
                            min=sing_item.min,
                            max=sing_item.max,
                            confidence=sing_item.confidence
                        )

        for row in range(len(parsed_json)):
            item = parsed_json[row]
            for edge in item['phi']:
                # Make sure current edge is not in list of rejected edges, e.g. 'compound'
                if edge['containment'] not in rejected_edges:
                    if 'orig' not in edge['containment']:
                        x = edge['containment']  # Name of edge label

                        # Giacomo: the former code was not able to handle: "does not play"
                        querywords = x.split()
                        resultwords = [word for word in querywords if word.lower() not in negations]
                        x = ' '.join(resultwords)

                        has_negations = any(map(lambda x: x in edge['containment'], negations))

                        # Check if name of edge is in "non verbs"
                        edge_type = "verb"
                        for non_verb in non_verbs:
                            if x == non_verb.strip():
                                edge_type = "non_verb"
                                break

                        if nodes[edge['score']['child']].type == Grouping.MULTIINDIRECT:
                            for node in nodes[edge['score']['child']].entities:
                                edges.append(Relationship(
                                    source=nodes[edge['score']['parent']],
                                    target=nodes[node.id],
                                    edgeLabel=Singleton(id=item['id'], named_entity=x,
                                                        properties=frozenset(dict().items()),
                                                        min=-1,
                                                        max=-1, type=edge_type,
                                                        confidence=nodes[item['id']].confidence),
                                    isNegated=has_negations
                                ))
                        else:
                            edges.append(Relationship(
                                source=nodes[edge['score']['parent']],
                                target=nodes[edge['score']['child']],
                                edgeLabel=Singleton(id=item['id'], named_entity=x,
                                                    properties=frozenset(dict().items()),
                                                    min=-1,
                                                    max=-1, type=edge_type,
                                                    confidence=nodes[item['id']].confidence),
                                isNegated=has_negations
                            ))
    print(json.dumps(Graph(edges=edges), cls=EnhancedJSONEncoder))
    return tuple([Graph(edges=edges), nodes, edges])


def associate_type_to_item(item, key, nodes, stanza_row):
    # If key is SetOfSingletons, loop over each Singleton and make association to type
    # Giacomo: FIX, but only if they are not logical predicates
    if isinstance(item,
                  SetOfSingletons):  # and ((nodes[key].type == Grouping.NONE) or (nodes[key].type == Grouping.GROUPING)):
        for entity in item.entities:
            associate_type_to_item(entity, key, nodes, stanza_row)
    else:
        assign_type_to_singleton(item, stanza_row, nodes, key)
