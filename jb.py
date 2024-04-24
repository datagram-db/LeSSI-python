import urllib.request
import json
from collections import defaultdict
import random

import stanza
import os
import sys
from nltk.tokenize import sent_tokenize

from CleanPipeline import CleanPipeline

S = set()
d = defaultdict(set)

def request(self, sentence):
    from crawltogsm.generate_gsm_cypher_db import stanford_nlp_to_gsm
    g = str(stanford_nlp_to_gsm(self, list(sentence)))
    graphs = g.split("""~~
""")
    assert len(graphs) == len(sentence)
    for g,s in zip(graphs,sentence):
        N = g.count(""".
    
    id:""")+1
        d[N].add(tuple([g,s]))

def load_from_remote(u):
    global S
    print(f"Downloading: {u}")
    data = urllib.request.urlopen(u)
    for line in data:
        l = json.loads(line)
        if "question" in l and "stem" in l["question"]:
            document = sent_tokenize(l["question"]["stem"])
            for sentence in document:
                S = S.union(set(filter(lambda y: len(y) > 0, map(lambda x: x.strip(), str(sentence).rstrip('.').split(".")))))


def part1():
    conf = "/home/giacomo/projects/similarity-pipeline/submodules/news-crawler/config_proposed.yaml"
    clean_pipeline = CleanPipeline().instance()
    clean_pipeline.init(conf)
    clean_pipeline.cfg
    load_from_remote("https://s3.amazonaws.com/commensenseqa/train_rand_split.jsonl")
    load_from_remote("https://s3.amazonaws.com/commensenseqa/test_rand_split_no_answers.jsonl")
    S = set(filter(lambda sentence: any(map(lambda x: x.isalpha,sentence)), S))
    # request(clean_pipeline, S)
    with open("commonsenseqatrain.txt", "w") as f:
        f.write(os.linesep.join(S))

from wonderwords import RandomSentence

def part2():
    with open("/home/giacomo/Scrivania/commonsenseqatrain.txt", "r") as f:
        for line in f.readlines():
            line = line.strip()
            d[len(line.split())].add(line)
    dd = defaultdict(set)
    for k in sorted(d):
        v = d[k]
        print(f"of length {k}: #{len(v)} sentences")
        # dd[len(v)].add(k)
    lengths = [5,10,15,18]
    N = 4
    K = 300
    dd = {x: random.sample(list(d[x]), K) for x in lengths}
    idx = [int((z+1)*K/N) for z in range(N)]
    for y in dd:
        for z in idx:
            with open("/home/giacomo/Scrivania/commonsenseqatrain_"+str(z)+"_"+str(y)+".txt","w") as f:
                f.write(os.linesep.join(dd[y][0:z]))
    # upper_bound = min(map(lambda x : len(d[x]), lengths)) ~ 300
    # for k in sorted(dd):
    #     s = ", ".join(map(str,dd[k]))
    #     print(f"with {k} sentences: {s} (#{len(dd[k])})")

if __name__ == '__main__':

    # s = RandomSentence()
    # s.bare_bone_sentence() # Len 3
    # s.simple_sentence()    # Len 4
    # s.bare_bone_with_adjective() # Len 4
    # s.sentence()           # Len 4
    part2()
    # if len(sys.argv) > 1:
    #     u = sys.argv[1]
    # # stanza.download('en',processors='tokenize,pos')
    # # nlp = stanza.Pipeline(lang='en',processors='tokenize', tokenize_no_ssplit=True)
    # data = urllib.request.urlopen(u)
    # print(data)
    # with open("commonsenseqatrain.txt", "w") as f:
    #     for line in data:
    #         print(line)
    #         l = json.loads(line)
    #         if "question" in l and "stem" in l["question"]:
    #             document = sent_tokenize(l["question"]["stem"])
    #             for sentence in document:
    #                 S.add(set(filter(lambda y: len(y)>0, map(lambda x: x.strip(), str(sentence).rstrip('.').split(".")))))
