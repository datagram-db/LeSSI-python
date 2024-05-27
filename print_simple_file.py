import json
import os

if __name__ == '__main__':
    impl = "/home/giacomo/dump_impl.json"
    with open(impl) as f:
        d = json.load(f)
    with open(impl+"_txt.txt","w") as w:
        for k,v in d.items():
            w.write(k+os.linesep)
            w.write((os.linesep).join(map(lambda x: "  - "+x, v)))
            w.write(os.linesep)
            w.write(os.linesep)
