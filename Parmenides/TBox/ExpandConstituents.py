from collections import defaultdict
from enum import Enum

from logical_repr.Sentences import FVariable, FNot


class ExpandConstituents:
    def __init__(self, expander):
        self.expander = expander
        self.constituent_expansion_map = defaultdict(set)

    def expand_formula(self, formula):
        ### Defining the expansion of one single rule
        if formula is None or formula in self.constituent_expansion_map:
            return
        for expansion in self.expander(formula):
            self.constituent_expansion_map[formula].add(expansion)
            self.expand_formula(formula)
        if formula not in self.constituent_expansion_map:
            self.constituent_expansion_map[formula] = set()

    def getExpansionLeaves(self):
        return {x for x, y in self.constituent_expansion_map.items() if len(y) == 0}

def get_formula_expansion(expander, formula):
    ec = ExpandConstituents(expander)
    ec.expand_formula(formula)
    return ec.getExpansionLeaves()


class CasusHappening(Enum):
    EQUIVALENT = 0
    IMPLICATION = 1
    EXCLUSIVES = 2
    INDIFFERENT = 3
    NONE = 4

def transformCaseWhenOneArgIsNegated(orig:CasusHappening):
    d = {CasusHappening.NONE: CasusHappening.NONE,
     CasusHappening.INDIFFERENT: CasusHappening.INDIFFERENT,
    CasusHappening.EQUIVALENT: CasusHappening.EXCLUSIVES,
     CasusHappening.EXCLUSIVES: CasusHappening.EQUIVALENT}
    return d[orig]

def test_pairwise_sentence_similarity(d, x, y, store=True):
    val = CasusHappening.NONE
    if (x == y):
        val = CasusHappening.EQUIVALENT
    elif (x == FNot(y)) or (y == FNot(x)):
        val = CasusHappening.EXCLUSIVES
    elif isinstance(x, FNot):
        val = transformCaseWhenOneArgIsNegated(test_pairwise_sentence_similarity(d, x.arg, y, False))
    elif isinstance(y, FNot):
        val = transformCaseWhenOneArgIsNegated(test_pairwise_sentence_similarity(d, x, y.arg, False))
    else:
        ## TODO:
        print("WARNING: CASE NOT BEING COVERED")
        pass
    if store:
        d[(x, y)] = val
    return val

class ExpandConstituents:
    def __init__(self, expander, list_of_rules):
        self.set_of_rules = list_of_rules
        self.expander = expander
        #Expanding the constituents
        if not all(lambda x: isinstance(x, FVariable), self.set_of_rules):
            raise ValueError("Error: all the rules within the set of rules must represent FVariables")
        self.expansion_dictionary = {rule: get_formula_expansion(self.expander, rule) for rule in self.set_of_rules}

        self.result_cache = dict()
        self.constituents = set()
        for y in self.expansion_dictionary.values():
            self.constituents = self.constituents.union(set(y))
        self.outcome_implication_dictionary = {(x,y):CasusHappening.NONE for x in self.constituents for y in self.constituents}
        for x in self.constituents:
            for y in self.constituents:
                test_pairwise_sentence_similarity(self.outcome_implication_dictionary, x, y, True)

    def determine(self, i:int, j:int):
        assert i<len(self.set_of_rules)
        assert j<len(self.set_of_rules)
        if (i,j) in self.result_cache:
            return self.result_cache[(i,j)]
        from logical_repr.sentence_expansion import PairwiseCases
        val = PairwiseCases.NonImplying
        expansionLeft = self.expansion_dictionary[self.set_of_rules[i]]
        expansionRight = self.expansion_dictionary[self.set_of_rules[j]]
        result = set()
        for x in expansionLeft:
            for y in expansionRight:
                assert (x,y) in self.outcome_implication_dictionary
                tmp = self.outcome_implication_dictionary[(x,y)]
                if tmp == CasusHappening.EXCLUSIVES:
                    val = PairwiseCases.MutuallyExclusive
                    break
                else:
                    result.add(tmp)
            if val == PairwiseCases.MutuallyExclusive:
                break
        if val != PairwiseCases.MutuallyExclusive:
            if CasusHappening.EQUIVALENT in result:
                val = PairwiseCases.Equivalent
            elif CasusHappening.IMPLICATION in result:
                val = PairwiseCases.Implying
            else:
                val = PairwiseCases.NonImplying
        self.result_cache[(i, j)] = val
        return val










