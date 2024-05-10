__author__ = "Giacomo Bergami"
__copyright__ = "Copyright 2024, Giacomo Bergami"
__credits__ = ["Giacomo Bergami"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Giacomo Bergami"
__email__ = "bergamigiacomo@gmail.com"
__status__ = "Production"

from collections import defaultdict
from enum import Enum
from functools import reduce
from typing import List
import pandas
# from deephaven.TableTools import newTable, intCol, emptyTable

# from deephaven import new_table
# from deephaven.column import string_col, int_col
# from deephaven.constants import NULL_INT

from logical_repr.Sentences import Formula


class PairwiseCases(Enum):
    NonImplying = 0
    Implying = 1
    MutuallyExclusive = 2


class CountingDictionary:
    def __init__(self):
        self.counter = dict()
        self.reverseConstituent = dict()

    def add(self, x):
        if x not in self.counter:
            self.reverseConstituent[len(self.counter)] = x
            self.counter[x] = len(self.counter)
        return self.counter[x]

    def __len__(self):
        return len(self.counter)

    def fromId(self, x):
        return self.reverseConstituent[int(x)]

    def contains(self, x):
        if x not in self.counter:
            return -1
        return self.counter[x]


def with_variables_from(f, l, cd: CountingDictionary, fn, selection=False):
    pdf = reduce(lambda x, y: x.merge(y, how="cross"), [pandas.DataFrame({str(x): [1, 0]}) for x in l])
    L = []
    for x in pdf.to_dict(orient='records'):
        d = dict()
        for k, v in x.items():
            d[cd.fromId(int(k))] = v
        x[fn] = f.semantic(d)
        if not selection or x[fn] > 0.0:
            L.append(x)
    return pandas.DataFrame(L)


def with_true_variables_from(l):
    return pandas.DataFrame({str(x): [1] for x in l})


class SentenceExpansion:
    def __init__(self, sentence_list: List[Formula], kb):
        self.sentence_list = []
        self.sentence_to_id = dict()
        for idx in range(len(sentence_list)):
            self.sentence_to_id[sentence_list[idx]] = idx
            self.sentence_list.append(sentence_list[idx].strippedByType())
        self.kb = kb
        self.minimal_constituents = CountingDictionary()
        self.U = None
        self.d = defaultdict(set)
        self.buildup = False

    def expand_sentence(self, sentence_id) -> List[Formula]:
        # TODO: use the Knowledge Base to expand the interpretations
        return self.sentence_list[sentence_id].getAtoms()

    def get_mutual_truth(self, i, j):
        # TODO: if i mutual exclusive from j, then this should have been
        # Inferred at the expansion phase by explicitly stating so
        # If i entails j, we should have used an appropriate table
        # Otherwise, i and j are not mutually implying each other.
        # This is what is returned at the moment
        return PairwiseCases.NonImplying

    def mutual_truth(self, i, j):
        test = self.get_mutual_truth(i, j)
        # relation = Relation()
        # relation.add_attributes([str(i), str(j)])
        if test == PairwiseCases.NonImplying:
            return pandas.DataFrame({str(i): [0, 0, 1, 1],
                                     str(j): [0, 1, 0, 1]})
        elif test == PairwiseCases.Implying:
            return pandas.DataFrame({str(i): [0, 0, 1],
                                     str(j): [0, 1, 1]})
        elif test == PairwiseCases.MutuallyExclusive:
            return pandas.DataFrame({str(i): [0, 1],
                                     str(j): [1, 0]})

    def universal_truth(self):
        L = list()
        N = len(self.minimal_constituents)
        if N == 0:
            # relation = Relation(name="R")
            return pandas.DataFrame({})
        if N == 1:
            return pandas.DataFrame({"T": [0, 1]})
        else:
            for i in range(N):
                for j in range(N):
                    if i != j:
                        L.append(self.mutual_truth(i, j))
            return reduce(lambda x, y: x.merge(y), L)

    def collect_sentence_constituents(self, sentence_id):
        for i in range(len(self.sentence_list)):
            for x in self.expand_sentence(sentence_id):
                self.d[sentence_id].add(self.minimal_constituents.add(x))

    def build_up_truth_table(self):
        if not self.buildup:
            for i in range(len(self.sentence_list)):
                self.collect_sentence_constituents(i)
            self.U = self.universal_truth()
            self.buildup = True

    def __call__(self, i, j):
        return self.get_straightforward_id_similarity(self.sentence_to_id[i], self.sentence_to_id[j])

    def get_straightforward_id_similarity(self, i, j):
        self.build_up_truth_table()
        Ri = with_variables_from(self.sentence_list[i], self.d[i], self.minimal_constituents, "R" + str(i), True)
        Rj = with_variables_from(self.sentence_list[j], self.d[j], self.minimal_constituents, "R" + str(j))
        result = self.U.merge(Ri).merge(Rj)[list(set(Ri.columns).union(set(Rj.columns)))].drop_duplicates()[
            ["R" + str(j)]].prod(axis=1)
        total = result.sum(axis=0) / len(result)
        # print(f"{i}~{j} := {total}")
        return total
