import numpy


def chunk(x, n):
    return zip(*(x[i:] for i in range(n)))


def allChunks(l):
    l = list(l)
    s = list()
    for i in range(len(l)+1):
        if i > 1:
            for x in chunk(l, i):
                s.append(x)
    return s

def bogus_score_from_meu(x):
    x = str(x).lower()
    if x == "newcastle": #entity from the meu
        return 1 #Score in MEU for x appears within the monads in the MEU
    if x == "city":
        return 1 #Score in MEU for x appears within the monads in the MEU
    if x == "center":
        return 0.8 #Score in MEU for x appears within the monads in the MEU
    if x == "newcastle city":
        return 0 #missing
    if x == "city center":
        return 1 #Score in MEU for x appears within the monads in the MEU
    if x == "newcastle city center":
        return 0 #missing


if __name__ == "__main__":
    L = ["Newcastle", "city", "center"] #item.entities
    d = dict(zip(range(len(L)), L))
    print(d)                            #dictionary for storing the replacing elements
    for x in allChunks(list(d.keys())):
        if all(y in d for y in x):
            exp = " ".join(map(lambda z: L[z], x))
            if bogus_score_from_meu(exp) >= numpy.prod(list(map(lambda z: bogus_score_from_meu(L[z]), x))):
                candidate_delete = set()
                for k,v in d.items():
                    if isinstance(k, int):
                        if k in x:
                            candidate_delete.add(k)
                    elif isinstance(k, tuple):
                        if len(set(x).intersection(set(k)))>0:
                            candidate_delete.add(k)
                for z in candidate_delete:
                    d.pop(z)
                d[x] = exp
    print(d)