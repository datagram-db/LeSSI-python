import os
import csv

import stanza

from gsmtosimilarity.TwoGrams import TwoGramSetSimilarity
from gsmtosimilarity.conceptnet.SimplifiedFuzzyStringMatching import SimplifiedFuzzyStringMatching


class Admin5:
    def __init__(self):
        self.geoIdToAdmin5 = {}

        with open(os.path.join("adminCode5.txt"), 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                geoId = row[0].strip()
                admin5 = row[1].strip()
                self.geoIdToAdmin5[geoId] = admin5

    @staticmethod
    def instance():
        if not hasattr(Admin5, 'adm5'):
            Admin5.adm5 = Admin5()
        return Admin5.adm5

    def getAdmin5(self, geoId):
        return self.geoIdToAdmin5.get(geoId)

class GeoNameField:
    def __init__(self, lin):
        line = lin.split("\t")
        self.isADM = False
        self.geonameid = line[0]
        self.feature_class = line[6]
        self.feature_code = line[7]
        self.country_code = self.rectify(line[8])
        self.cont = True
        self.path = ""
        self.analyse(self.country_code)
        self.adm1 = self.rectify(line[10])
        self.analyse(self.adm1)
        self.adm2 = self.rectify(line[11])
        self.analyse(self.adm2)
        self.adm3 = self.rectify(line[12])
        self.analyse(self.adm3)
        self.adm4 = self.rectify(line[13])
        self.analyse(self.adm4)
        self.adm5 = Admin5.instance().getAdmin5(self.geonameid)
        self.analyse(self.adm5)
        if self.path.startswith("\t"):
            self.path = self.path[1:]
        if not self.isADM:
            self.path = self.path + "\t" + "P" + str(int(self.geonameid)).zfill(10)
        self.name = line[1]
        self.ascii = line[2]
        self.others = line[3].split(",")

    @staticmethod
    def rectify(x):
        x = x.strip()
        return x if x else None

    def analyse(self, x):
        if self.cont and x is not None:
            self.path += "\t" + x
        else:
            self.cont = False


def build_loc_result(text,type, start_char, end_char,monad,conf,id):
    return {                "text": text,
                "type": type,
                "start_char": start_char,
                "end_char": end_char,
                "monad": monad,
                "confidence": conf,
                            "id":id}

class ResolveMultiNamedEntity:

    def __init__(self, threshold, forinsert):
        self.threshold = threshold
        self.forinsert = forinsert
        self.result = []
        self.s = None
        self.fa = None

    def test(self, current, rest, k, v, start, end):
        if (len(rest) == 0):
            if k >= self.forinsert:
                self.result.append(build_loc_result(current, "LOC", start, end, v, k, self.fa.getValue(v)))
        else:
            next = current + " " + rest[0][0]
            val = TwoGramSetSimilarity(next, v)
            if val < k:
                if k >= self.forinsert:
                    self.result.append(build_loc_result(current, "LOC", start, end, v, k, self.fa.getValue(v)))
            else:
                self.test(next, rest[1:], val, v, start, rest[0][1])

    def start(self, stringa, s, fa, nlp):
        self.s = s
        self.fa = fa
        for sentence in nlp(stringa).sentences:
            ls = [(token.text,token.start_char,token.end_char) for token in sentence.tokens]
            for i in range(len(ls)):
                m = s.fuzzyMatch(self.threshold, ls[i][0])
                for k, v in m.items():
                    for candidate in v:
                        cand = s.get(candidate)
                        newK = TwoGramSetSimilarity(ls[i][0], cand)
                        if newK >= self.threshold:
                            self.test(ls[i][0], ls[i + 1:], newK, s.get(candidate), ls[i][1], ls[i][2])
        return self.result

class GeoNamesService:
    def __init__(self, file=None):
        self.nlp = stanza.Pipeline(lang='en', processors='tokenize')
        self.s = SimplifiedFuzzyStringMatching()
        self.name_to_id = dict()
        if file is not None and os.path.exists(file):
            with open(file) as f:
                for line in f.readlines():
                    g = GeoNameField(line)
                    self.noFileInit(g.name, g.geonameid)
                    self.noFileInit(g.ascii, g.geonameid)
                    for x in g.others:
                        self.noFileInit(x, g.geonameid)

    def noFileInit(self, x, id):
        if x not in self.name_to_id:
            self.name_to_id[x.lower()] = set()
        self.name_to_id[x.lower()].add(id)
        self.s.put(x)

    def getValue(self,x):
        return self.name_to_id[x]

    def resolveU(self, recallThreshold, precisionThreshold, s):
        ar = ResolveMultiNamedEntity(recallThreshold, precisionThreshold)
        ## TODO: 
        return ar.start(s, self.s, self, self.nlp)


if __name__ == "__main__":
    stringa = "I say that Newcastle upon has traffic"
    s = GeoNamesService()
    s.noFileInit("Newcastle Upon Tyne", "n/t/uk/e/w")
    s.noFileInit("Tyne and Wear","t/uk/e/w")
    s.noFileInit("London", "l/uk/e/w")
    s.noFileInit("Rome", "r/l/i/e/w")
    print(s.resolveU(0.1, 0.7, stringa))



