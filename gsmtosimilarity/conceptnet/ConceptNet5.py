import math
import os.path
import urllib.request
import numpy
import pandas as pd
from gsmtosimilarity.conceptnet.SimplifiedFuzzyStringMatching import SimplifiedFuzzyStringMatching
from sentence_transformers import util

def kernel_n(x, y, K):
    return float(K(x,y)/math.sqrt(K(x,x)*K(y,y)))

class ConceptNet5Numberbatch:
    def __init__(self, lan, minTheta):
        if lan is None:
            lan = "en"
        self.minTheta = minTheta
        self.dictionary = SimplifiedFuzzyStringMatching()
        if not os.path.exists("mini.h5"):
            print("Downloading Mini HDF5 data...")
            urllib.request.urlretrieve("http://conceptnet.s3.amazonaws.com/precomputed-data/2016/numberbatch/19.08/mini.h5", "mini.h5")
        self.f = pd.read_hdf("mini.h5", 'mat', encoding='utf-8')
        self.data_pts = dict()
        for x in self.f.index:
            concept = x.split("/")
            if (concept[2] == lan):
                key = concept[3].replace("_", " ")
                idx, present = self.dictionary.put(key)
                if not present:
                    self.data_pts[idx] = (numpy.array(self.f.loc[x]))

    def getEmbedding(self, x):
        return self.dictionary.fuzzyMatch(self.minTheta, x)

    def string_similarity(self, x, y):
        L = {z for k,v in self.getEmbedding(x).items() for z in v}
        R = {z for k,v in self.getEmbedding(y).items() for z in v}
        K = util.pairwise_dot_score
        finalScore = 0.0
        for inL in L:
            vec =self.data_pts[inL]
            for inR in R:
                score = kernel_n(vec, self.data_pts[inR], K)
                if score > finalScore:
                    finalScore = score
        return finalScore


if __name__ == "__main__":
    cn5n = ConceptNet5Numberbatch("en", 0.8)
    print(cn5n.string_similarity("cat", "mouse"))

