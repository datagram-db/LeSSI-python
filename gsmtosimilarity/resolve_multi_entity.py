from gsmtosimilarity.TwoGrams import TwoGramSetSimilarity


def build_loc_result(text, type, start_char, end_char, monad, conf, id):
    return map(lambda x: {"text": text,
                          "type": type,
                          "start_char": start_char,
                          "end_char": end_char,
                          "monad": monad,
                          "confidence": conf,
                          "id": x}, id)


class ResolveMultiNamedEntity:

    def __init__(self, threshold, forinsert):
        self.threshold = threshold
        self.forinsert = forinsert
        self.result = []
        self.s = None
        self.fa = None

    def test(self, current, rest, k, v, start, end, type):
        if len(rest) == 0:
            if k >= self.forinsert:
                for j in build_loc_result(current, type, start, end, v, k, self.fa.get_value(v)):
                    self.result.append(j)
        else:
            next = current + " " + rest[0][0]
            val = TwoGramSetSimilarity(next, v)
            if val < k:
                if k >= self.forinsert:
                    for j in build_loc_result(current, type, start, end, v, k, self.fa.get_value(v)):
                        self.result.append(j)
            else:
                self.test(next, rest[1:], val, v, start, rest[0][1], type)

    def start(self, stringa, s, fa, nlp, type):
        self.s = s
        self.fa = fa
        self.result.clear()
        for sentence in nlp(stringa).sentences:
            ls = [(token.text, token.start_char, token.end_char) for token in sentence.tokens]
            for i in range(len(ls)):
                m = s.fuzzyMatch(self.threshold, ls[i][0])
                for k, v in m.items():
                    for candidate in v:
                        cand = s.get(candidate)
                        newK = TwoGramSetSimilarity(ls[i][0], cand)
                        if newK >= self.threshold:
                            self.test(ls[i][0], ls[i + 1:], newK, s.get(candidate), ls[i][1], ls[i][2], type)
        return self.result