__author__ = "Oliver R. Fox, Giacomo Bergami"
__copyright__ = "Copyright 2024, Oliver R. Fox, Giacomo Bergami"
__credits__ = ["Oliver R. Fox, Giacomo Bergami"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Oliver R. Fox, Giacomo Bergami"
__status__ = "Production"
import json
import math
from collections import defaultdict
from copy import copy

from gsmtosimilarity.graph_similarity import EnhancedJSONEncoder, negations, lemmatizer, Graph
from inference_engine.EntityRelationship import Singleton, SetOfSingletons, Grouping, Relationship, replaceNamed
from inference_engine.Sentence import Sentence


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
        # Giacomo: then, we'd need to use a defaultdict(list) and merge them as https://stackoverflow.com/a/70689832/1376095
        if entity.type != "ENTITY" and entity.type != 'noun' and not simplistic and chosen_entity is None:  # TODO: FIX CHOSEN ENTITY NOT NONE
            chosen_entity = entity
        else:
            extra = " ".join((extra, entity.named_entity))  # Ensure there is no leading space

    extra = extra.strip()  # Remove whitespace

    if chosen_entity is None and not simplistic:
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
            named_entity=name,
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


def assign_type_to_singleton(item, stanza_row, nodes, key):
    associations = dict()

    # TODO: merge the nodes together that belong to the same spatio-temporal entities,
    #       or multi-named entities known from ConceptNet5

    # Compare overlap of min begin and max end char from MEU and edges like "compound" etc.
    meu_entities = []
    entities = []

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
                if meu not in meu_entities:
                    meu_entities.append(meu)
                if item not in entities:
                    entities.append(item)

            # if start_graph >= start_intersection and start_meu >= start_intersection and \
            #         end_graph <= end_intersection and end_meu <= end_intersection:
            #     if meu not in meu_entities:
            #         meu_entities.append(meu)
            #     if item not in entities:
            #         entities.append(item)

    associations[item] = entities

    # print(associations[item])
    # print(meu_entities)

    for association in associations[item]:
        if len(meu_entities) > 0:
            best_score = max(map(lambda y: y['confidence'], meu_entities))
            best_items = [y for y in meu_entities if y['confidence'] == best_score]
            best_type = None
            if len(best_items) == 1:
                best_item = best_items[0]
                best_type = best_item['type']
            else:
                best_types = list(set(map(lambda best_item: best_item['type'], best_items)))
                best_type = None
                if len(best_types) == 1:
                    best_type = best_types[0]
                elif "LOC" in best_types and "GPE" in best_types:
                    best_type = "LOC"
                else:
                    best_type = "None"
            if isinstance(association, Singleton):
                item = Singleton(
                    named_entity=association.named_entity,
                    properties=association.properties,
                    min=association.min,
                    max=association.max,
                    type=best_type,
                    confidence=best_score
                )
            else:
                item = association

            # Giacomo: This was a bug: you were discarding relevant AND/OR information!
            if isinstance(nodes[key], SetOfSingletons):
                if isinstance(item, SetOfSingletons):
                    set_item = item
                else:
                    new_set = []
                    confidence = 1
                    for entity in nodes[key].entities:
                        if (entity.confidence < best_score or math.isnan(best_score)) and \
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
                if nodes[key].confidence < best_score or math.isnan(best_score):
                    nodes[key] = item
                else:
                    nodes[key] = association

    return nodes


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


def create_cop(edge, kernel, targetOrSource):
    if targetOrSource == 'target':
        temp_prop = dict(copy(kernel.target.properties))
        target_json = json.dumps(edge.target, cls=EnhancedJSONEncoder)
        target_dict = dict(json.loads(target_json))
        temp_prop['cop'] = target_dict
        new_target = Singleton(
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
                        edge_label = Singleton(edge_label_name, edge_label.properties, edge_label.min, edge_label.max,
                                               edge_label.type, edge_label.confidence)
                        break

            # If not a transitive verb, remove target as target reflects direct object
            # Giacomo: You had to include lemmatization!!!!
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

        if n < len(edges):
            kernel = edges[-1]
    kernel_nodes = set()
    if kernel is not None:
        if kernel.source is not None:
            kernel_nodes.add(kernel.source)
        if kernel.target is not None:
            kernel_nodes.add(kernel.target)
    for edge in edges:
        type_key = edge.source.type if isinstance(edge.source.type, str) else edge.source.type.name
        if type_key == 'JJ' or type_key == 'JJS':
            kernel = create_cop(edge, kernel, 'source')
            continue
        if type_key not in 'NEG':
            if edge.source not in kernel_nodes and edge.source not in properties[type_key]:
                properties[type_key].append(edge.source)
        type_key = edge.target.type if isinstance(edge.target.type, str) else edge.target.type.name
        if type_key == 'JJ' or type_key == 'JJS':
            kernel = create_cop(edge, kernel, 'target')
            continue
        if type_key not in 'NEG':
            if edge.target not in kernel_nodes and edge.target not in properties[type_key]:
                properties[type_key].append(edge.target)

    from gsmtosimilarity.stanza_pipeline import StanzaService

    el = " ".join(map(lambda y: y["lemma"], filter(lambda x: x["upos"] != "AUX", StanzaService().stNLP(lemmatizer.lemmatize(kernel.edgeLabel.named_entity, 'v')).to_dict()[0])))
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
    final =  rewrite_kernels(sentence)
    print(json.dumps(final, cls=EnhancedJSONEncoder))
    return final


def group_nodes(nodes, parsed_json):
    # Get all nodes from resulting graph and create list of Singletons
    number_of_nodes = range(len(parsed_json))
    for row in number_of_nodes:
        item = parsed_json[row]
        if 'conj' in item['properties']:
            continue  # add set of singletons later as we might not have all nodes yet
        else:
            minV = -1
            maxV = -1
            typeV = "None"
            if len(item['xi']) > 0:  # xi might be empty?
                name = item['xi'][0]
                minV = int(item['properties']['begin'])
                maxV = int(item['properties']['end'])
                typeV = item['ell'][0] if len(item['ell'])>0 else "None"
            else:
                name = '?'  # Yes, it might be empty if the node is invented, this is the only use case

            nodes[item['id']] = Singleton(
                named_entity=name,
                properties=frozenset(item['properties'].items()),
                min=minV,
                max=maxV,
                type=typeV,
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
            elif ('nor' in conj) or ('neither' in conj):
                group_type = Grouping.NEITHER
            elif 'or' in conj:
                group_type = Grouping.OR
            else:
                group_type = Grouping.NONE
            for edge in item['phi']:
                if 'orig' in edge['containment']:
                    grouped_nodes.append(nodes[edge['content']])
        else:
            for edge in item['phi']:
                is_current_edge_compound = 'compound' in edge['containment']
                if is_current_edge_compound:
                    is_compound = True
                    grouped_nodes.append(nodes[edge['score']['child']])

        if has_conj:
            if group_type == Grouping.NEITHER:
                grouped_nodes = [SetOfSingletons(type=Grouping.NOT, entities=tuple([x]), min=x.min, max=x.max,
                                                 confidence=x.confidence) for x in grouped_nodes]
                grouped_nodes = tuple(grouped_nodes)
                group_type = Grouping.AND
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


def to_internal_graph(parsed_json, stanza_row, rejected_edges, non_verbs, do_rewriting, is_rewriting_simplistic):
    nodes = {}
    group_nodes(nodes, parsed_json)
    print(nodes)

    # Loop over resulting graph again and create array of edges now we have all Singletons
    edges = []
    if stanza_row is not None:
        # Assign types to nodes
        for key in nodes:
            item = nodes[key]

            # If key is SetOfSingletons, loop over each Singleton and make association to type
            # Giacomo: FIX, but only if they are not logical predicates
            if isinstance(item, SetOfSingletons) and ((nodes[key].type == Grouping.NONE) or (nodes[key].type == Grouping.GROUPING)):
                for entity in item.entities:
                    nodes = assign_type_to_singleton(entity, stanza_row, nodes, key)
            else:
                nodes = assign_type_to_singleton(item, stanza_row, nodes, key)

        # With types assigned, merge SetOfSingletons into Singleton
        for key in nodes:
            item = nodes[key]

            if isinstance(item, SetOfSingletons):
                if item.type == Grouping.GROUPING:
                    if do_rewriting:
                        nodes = merge_set_of_singletons(item, nodes, key, is_rewriting_simplistic)

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
                # with open(cfg['rejected_edge_types'], 'r') as f:
                #     rejected_edges = f.read()
                if edge['containment'] not in rejected_edges:
                        if 'orig' not in edge['containment']:
                            x = edge['containment']  # Name of edge label

                            # Giacomo: the former code was not able to handle: "does not play"
                            querywords = x.split()
                            resultwords = [word for word in querywords if word.lower() not in negations]
                            x = ' '.join(resultwords)
                            # for name in negations:  # No / not
                            #     x = re.sub("\b(" + name + ")\b", " ", x)
                            # x = x.strip()  # Strip of leading/trailing whitespace

                            has_negations = any(map(lambda x: x in edge['containment'], negations))

                            # Check if name of edge is in "non verbs"
                            edge_type = "verb"
                            # with open(cfg['non_verbs'], "r") as f:
                            #     non_verbs = f.readlines()
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
    # print(json.dumps(Graph(edges=edges), cls=EnhancedJSONEncoder))
    # sentence = create_sentence_obj(cfg, edges, nodes)
    # print(json.dumps(sentence, cls=EnhancedJSONEncoder))
    return tuple([Graph(edges=edges), nodes, edges])
