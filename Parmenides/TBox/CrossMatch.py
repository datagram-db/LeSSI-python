import copy
import json

from Parmenides.paremenides import Parmenides
from logical_repr.Sentences import formula_from_dict, FBinaryPredicate, make_variable, make_name, FUnaryPredicate


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


    def do_expansion_match_iterative(self, N, struct_dict_dd, expansion):
        from Parmenides.TBox.SentenceMatch import structure_dictionary
        for i in range(N):
            data_match_morphism = struct_dict_dd.to_dict('records')[i]
            ## 5. Using this to instantiate the parametrized ontology query using the matched data
            QInst = Parmenides.instantiate_query_with_map(self.onto_query, data_match_morphism)
            Ly = list(self.p.multiple_queries(QInst))
            for ontology_navigation_morphism in Ly:
                merged_morphism = data_match_morphism | ontology_navigation_morphism
                merged_morphism_ddd = dict()
                for k, v in merged_morphism.items():
                    if k != "obj":
                        merged_morphism_ddd["@" + str(k)] = v
                rw_2_dis = expansion.replaceWith(merged_morphism_ddd, True, None, None)
                if not rw_2_dis.isUnresolved():
                    self.result.append(rw_2_dis)

    def do_replacement_match_rec(self, i, d, fugitive_init, rw_2):
        """
        This method implements the rewriting step by replacing the terms
        of a previously matched component by substituting some of the
        variables

        :param i:               Index associated to the morphisms to be used for instantiation
        :param d: dictionary    Dictionary containing the variable instantiation also associated with a
                                specific matched object, through which we are going to determine
                                how to possibly rewrite the thing given the things were matched
        :param fugitive_init:   Keeping track across mutual rewritings of which components of the original
                                expression ended up in representing the final rewriting
        :param rw_2:            Expression that needs to be rewritten after expansion
        """
        if i < 0: # If I applied all the morphisms, then I can attempt at rewriting
            ## 9. Determining the association between the original data-matched elements, and
            ## the same sub-expression after rewriting. This is required to fall-back to the non-
            ## matched part under the circumstantces that the update over certain sub-expressions
            ## was not effective, thus requiring to fall-back to the original data without
            ## any kind of rewriting
            TCL = transitive_closure(fugitive_init.items())
            ## Determining actually all the sub-expressions associated to the final rewritten object
            DST = set(rw_2.collectIds())
            ## Determining which objects from the origin and the end actually appear in the matches thorugh
            ## the transitive closure and matching
            DST = {x[0] for x in TCL}.intersection(DST)
            ORIG = {x[1] for x in TCL}.intersection(self.ORIG)
            finalReplacement = dict({object_magic(x[0]): object_magic(x[1]) for x in TCL if
                                     (x[0] in DST and object_magic(x[0]).isUnresolved()) and x[1] in ORIG})
            if len(finalReplacement) > 0:
                rw_2 = rw_2.replaceWith(finalReplacement)
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
                    self.do_replacement_match_rec(i - 1, d_local, local_fugitive, rw_2_dis)
            else:
                self.do_replacement_match_rec(i - 1, d, fugitive_init, rw_2)

def do_match(formula, qq, onto_query, p, replacement_map, value_invention=None):
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
    if value_invention is None:
        ## 2. Within the data, I'm applying the substitution required by the matching and rewriting semantics
        rw_init = rw_1.replaceWith(replacement_map, d=d, fugitive=fugitive_init)

    ## 3. Defining the correspondences across the same variable object and across matchings
    struct_dict_dd = structure_dictionary(d)
    N = len(struct_dict_dd)
    qRec = DoMatchRec(onto_query, p, ORIG)

    if value_invention is None:
        qRec.do_replacement_match_rec(N - 1, d, fugitive_init, rw_init)
    else:
        qRec.do_expansion_match_iterative(N, struct_dict_dd, value_invention)
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

def query3():
    g = Parmenides("/home/giacomo/projects/similarity-pipeline/submodules/news-crawler/Parmenides/turtle.ttl")
    formula = FBinaryPredicate("have", make_name("flow"), make_name("Chyraa-Khoor"), 1.0, frozenset())
    qq = FBinaryPredicate("have", make_variable("x"), make_variable("z"), 1.0, frozenset())
    rewriting = FUnaryPredicate("be", make_variable("y"), 1.0, frozenset())
    onto_Q = ["@x", "^y"]
    replacement_map = dict()
    for x in do_match(formula, qq, onto_Q, g, replacement_map, rewriting):
        print(x)

if __name__ == "__main__":
    query3()
    #query1(q1bis) #q1bis
