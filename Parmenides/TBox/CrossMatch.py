import copy
import json

from Parmenides.paremenides import Parmenides
from logical_repr.Sentences import formula_from_dict, FBinaryPredicate, make_variable, make_name

def object_magic(id):
    import ctypes
    return ctypes.cast(id, ctypes.py_object).value

def transitive_closure(a):
    closure = set(a)
    while True:
        new_relations = set((x,w) for x,y in closure for q,w in closure if q == y)
        closure_until_now = closure | new_relations
        if closure_until_now == closure:
            break
        closure = closure_until_now
    return closure

# def do_match_old(formula, qq, onto_query, p, replacement_map):
#     # Lz = []
#     from collections import defaultdict
#     from Parmenides.TBox.SentenceMatch import structure_dictionary
#     d = defaultdict(list)
#     fugitive = dict()
#     # for x in match(formula, q):
#     # print(formula)
#
#     ## 0. Preserving the original ids
#     ORIG = set(formula.collectIds())
#     ## 1. Matching the query with the data
#     rw_1 = formula.matchWith(qq, d, None, fugitive)
#     ## 2. Within the data, I'm applying the substitution required by the matching and rewriting semantics
#     rw_2 = rw_1.replaceWith(replacement_map, d=d, fugitive=fugitive)
#
#
#     ## 3. Defining the correspondences across the same variable object and across matchings
#     dd = structure_dictionary(d)
#     print(dd)
#     N = len(dd)
#     for i in range(N):
#         ## 4. For each replacement record m
#         m = dd.to_dict('records')[i]
#         ## 5. Using this to instantiate the parametrized ontology query using the matched data
#         QInst = Parmenides.instantiate_query_with_map(onto_query, m)
#         ## 6. Running the ontology query over the instantiated query
#         Ly = list(p.multiple_queries(QInst))
#         if len(Ly) > 0:  ## Determining the match only if we have one element
#             for z in Ly:
#                 m = m | z
#             # 7. Determining the rewriting transformation for each element of interest
#             ddd = dict()
#             for k,v in m.items():
#                 if k != "obj":
#                     ddd["@"+str(k)] = v
#                 else:
#                     ddd[k] = v
#             # 8. Partially instantiating the matched data to be rewritten
#             rw_2 = rw_2.replaceWith(ddd, True, d, fugitive=fugitive)
#             dd = structure_dictionary(d)
#
#     ## 9. Determining the unresolved objects
#     TCL = transitive_closure(fugitive.items())
#     DST = set(rw_2.collectIds())
#     DST = {x[0] for x in TCL}.intersection(DST)
#     ORIG = {x[1] for x in TCL}.intersection(ORIG)
#     object_magic(list(DST)[1]).isUnresolved()
#     finalReplacement = dict({object_magic(x[0]):object_magic(x[1]) for x in TCL if (x[0] in DST and object_magic(x[0]).isUnresolved()) and x[1] in ORIG})
#     if len(finalReplacement) > 0:
#         rw_2 = rw_2.replaceWith(finalReplacement)
#     return rw_2 ## Returning the variable instantiation for both the ontology match as well as the node match


class DoMatchRec:
    def __init__(self, onto_query, p, ORIG):
        self.onto_query = onto_query
        self.p = p
        self.ORIG = ORIG
        self.result = []

    def do_match_rec(self, i, d, fugitive_init, rw_2):
        if i < 0:
            TCL = transitive_closure(fugitive_init.items())
            DST = set(rw_2.collectIds())
            DST = {x[0] for x in TCL}.intersection(DST)
            ORIG = {x[1] for x in TCL}.intersection(self.ORIG)
            finalReplacement = dict({object_magic(x[0]): object_magic(x[1]) for x in TCL if
                                     (x[0] in DST and object_magic(x[0]).isUnresolved()) and x[1] in ORIG})
            if len(finalReplacement) > 0:
                rw_2 = rw_2.replaceWith(finalReplacement)
            # yield rw_2
            self.result.append(rw_2)
        else:
            from Parmenides.TBox.SentenceMatch import structure_dictionary
            dd = structure_dictionary(d)
            ## 4. For each replacement record m
            data_match_morphism = dd.to_dict('records')[i]
            ## 5. Using this to instantiate the parametrized ontology query using the matched data
            QInst = Parmenides.instantiate_query_with_map(self.onto_query, data_match_morphism)
            Ly = list(self.p.multiple_queries(QInst))
            if len(Ly) > 0:  ## Determining the match only if we have one element
                for ontology_navigation_morphism in Ly:
                    merged_morphism = data_match_morphism | ontology_navigation_morphism
                    # 7. Determining the rewriting transformation for each element of interest
                    merged_morphism_ddd = dict()
                    d_local = copy.deepcopy(d)
                    local_fugitive = copy.deepcopy(fugitive_init)
                    for k, v in merged_morphism.items():
                        if k != "obj":
                            merged_morphism_ddd["@" + str(k)] = v
                        else:
                            merged_morphism_ddd[k] = v
                    # 8. Partially instantiating the matched data to be rewritten
                    rw_2_dis = rw_2.replaceWith(merged_morphism_ddd, True, d_local, fugitive=local_fugitive)
                    self.do_match_rec(i-1, d_local, local_fugitive, rw_2_dis)
            else:
                self.do_match_rec(i - 1, d, fugitive_init, rw_2)

def do_match(formula, qq, onto_query, p, replacement_map):
    # Lz = []
    from collections import defaultdict
    from Parmenides.TBox.SentenceMatch import structure_dictionary
    d = defaultdict(list)
    fugitive_init = dict()
    # for x in match(formula, q):
    # print(formula)

    ## 0. Preserving the original ids
    ORIG = set(formula.collectIds())
    ## 1. Matching the query with the data
    rw_1 = formula.matchWith(qq, d, None, fugitive_init)
    ## 2. Within the data, I'm applying the substitution required by the matching and rewriting semantics
    rw_init = rw_1.replaceWith(replacement_map, d=d, fugitive=fugitive_init)

    ## 3. Defining the correspondences across the same variable object and across matchings
    N = len(structure_dictionary(d))
    qRec = DoMatchRec(onto_query, p, ORIG)
    qRec.do_match_rec(N-1, d, fugitive_init, rw_init)
    return qRec.result


q1 = """        {
        "args": [{
        "rel": "have",
        "src": {
            "name": "city center",
            "type": "None",
            "specification": "",
            "cop": null,
            "meta": "FVariable"
        },
        "dst": {
            "name": "XXXXX",
            "type": "JJ",
            "specification": null,
            "cop": null,
            "meta": "FVariable"
        },
        "score": 1.0,
        "properties": {
            "DATE": [
                {
                    "name": "Saturdays",
                    "type": "DATE",
                    "specification": null,
                    "cop": null,
                    "meta": "FVariable"
                }
            ]
        },
        "meta": "FBinaryPredicate"
        },{
        "rel": "have",
        "src": {
            "name": "city center",
            "type": "None",
            "specification": "",
            "cop": null,
            "meta": "FVariable"
        },
        "dst": {
            "name": "YYYYY",
            "type": "JJ",
            "specification": null,
            "cop": null,
            "meta": "FVariable"
        },
        "score": 1.0,
        "properties": {
            "DATE": [
                {
                    "name": "Saturdays",
                    "type": "DATE",
                    "specification": null,
                    "cop": null,
                    "meta": "FVariable"
                }
            ]
        },
        "meta": "FBinaryPredicate"
        }],
        "meta": "FAnd"
    }"""

q1bis = """        {
        "args": [{
        "rel": "have",
        "src": {
            "name": "city center",
            "type": "None",
            "specification": "",
            "cop": null,
            "meta": "FVariable"
        },
        "dst": {
            "name": "busy",
            "type": "JJ",
            "specification": null,
            "cop": null,
            "meta": "FVariable"
        },
        "score": 1.0,
        "properties": {
            "DATE": [
                {
                    "name": "Saturdays",
                    "type": "DATE",
                    "specification": null,
                    "cop": null,
                    "meta": "FVariable"
                }
            ]
        },
        "meta": "FBinaryPredicate"
        },{
        "rel": "have",
        "src": {
            "name": "city",
            "type": "None",
            "specification": "",
            "cop": null,
            "meta": "FVariable"
        },
        "dst": {
            "name": "cicicicia",
            "type": "JJ",
            "specification": null,
            "cop": null,
            "meta": "FVariable"
        },
        "score": 1.0,
        "properties": {
            "DATE": [
                {
                    "name": "Saturdays",
                    "type": "DATE",
                    "specification": null,
                    "cop": null,
                    "meta": "FVariable"
                }
            ]
        },
        "meta": "FBinaryPredicate"
        }],
        "meta": "FAnd"
    }"""

def query1(qstr):
        # with open("/home/giacomo/Scaricati/newcastle_sentences.txt_logical_rewriting.json", "r") as f:
        g = Parmenides("/home/giacomo/projects/similarity-pipeline/submodules/news-crawler/Parmenides/turtle.ttl")
        list_json = json.loads(qstr)
        formula = formula_from_dict(list_json)
        qq = FBinaryPredicate("have", make_variable("x"), make_variable("y"), 1.0, frozenset())
        onto_Q = ["@x", "partOf", "^z"]
        replacement_map = {"@y": "@z"}
        do_match(formula, qq, onto_Q, g, replacement_map)

def query2():
    g = Parmenides("/home/giacomo/projects/similarity-pipeline/submodules/news-crawler/Parmenides/turtle.ttl")
    formula = FBinaryPredicate("have", make_name("flow"), make_name("Chyraa-Khoor"), 1.0, frozenset())
    qq = FBinaryPredicate("have", make_variable("x"), make_variable("y"), 1.0, frozenset())
    onto_Q = ["@x", "^y"]
    replacement_map = dict()
    do_match(formula, qq, onto_Q, g, replacement_map)


if __name__ == "__main__":
    query2()
    #query1(q1bis) #q1bis
