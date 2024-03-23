from functools import lru_cache

from gsmtosimilarity.TwoGrams import TwoGramSetSimilarity
from gsmtosimilarity.conceptnet.ConceptNet5 import ConceptNet5Numberbatch
from gsmtosimilarity.huggingface.HuggingFace import HuggingFace
from gsmtosimilarity.levenshtein import lev, MultiLevenshtein


class StringSimilarity(object):
    def __init__(self, cfg, selector):
        self.cfg = cfg
        self.hugging = self.concept = self.pooling = None
        kind = self.cfg[selector]
        if kind == 'HuggingFace':
            self.hugging = HuggingFace(self.cfg['HuggingFace'])
        elif kind == 'ConceptNetPooling':
            self.concept = ConceptNet5Numberbatch(self.cfg['ConceptNet5Numberbatch']['lan'],
                                                  self.cfg['ConceptNet5Numberbatch']['minTheta'])
        elif kind == 'Prevailing':
            self.pooling = StringSimilarity(cfg, self.cfg['prevailing'][selector])
        self.kind = kind


    def string_similarity(self, x, y):
        if self.kind == "Levenshtein":
            return lev(x,y)
        elif self.kind == 'MultiLevenshtein':
            return MultiLevenshtein(x,y)
        elif self.kind == 'HuggingFace':
            return self.hugging.string_similarity(x,y)
        elif self.kind == 'ConceptNetPooling':
            return self.concept.string_similarity(x, y)
        elif self.kind == 'Prevailing':
            return self.semanticPrevail(x,y)

    def semanticPrevail(self, x, y):
        ml = MultiLevenshtein(x, y)
        sk = TwoGramSetSimilarity(x,y)
        score = max(ml,sk)
        if score>0.85:
            return score
        return self.pooling.string_similarity(x, y)










