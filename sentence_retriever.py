#!/usr/bin/env python3
import urllib.request
import json
import stanza
import os
import sys

if __name__ == '__main__':
        u = "https://s3.amazonaws.com/commensenseqa/train_rand_split.jsonl"
        if len(sys.argv)>1:
                u = sys.argv[1]
        stanza.download('en',processors='tokenize,pos')
        data = urllib.request.urlopen(u)
        with open("commonsenseqatrain.txt","w") as f:
                for line in data:
                        l = json.loads(line)
                        if "stem" in l:
                                document = nlp(l["stem"])
                                for sentence in document.sentences:
                                        f.write(sentence.text+os.linesep)
