import yaml

from crawltogsm.LegacyPipeline import LegacyPipeline
from gsmtosimilarity.graph_similarity import Singleton, Grouping, SetOfSingletons, Graph, Relationship


def singlet(x):
    return Singleton(
        named_entity=x,
        properties=frozenset(),
        min=-1,
        max=-1,
        type='None',
        confidence=1.0
    )

def _not(x):
    grouped_nodes = [x]
    SetOfSingletons(
        type=Grouping.NOT,
        entities=tuple(grouped_nodes),
        min=min(grouped_nodes, key=lambda x: x.min).min,
        max=max(grouped_nodes, key=lambda x: x.max).max,
        confidence=1
    )

def _and(x,y):
    grouped_nodes = [x,y]
    return SetOfSingletons(
        type=Grouping.AND,
        entities=tuple(grouped_nodes),
        min=min(grouped_nodes, key=lambda x: x.min).min,
        max=max(grouped_nodes, key=lambda x: x.max).max,
        confidence=1
    )

def _or(x,y):
    grouped_nodes = [x,y]
    return SetOfSingletons(
        type=Grouping.OR,
        entities=tuple(grouped_nodes),
        min=min(grouped_nodes, key=lambda x: x.min).min,
        max=max(grouped_nodes, key=lambda x: x.max).max,
        confidence=1
    )

def _neither(x,y):
    grouped_nodes = [_not(x),_not(y)]
    return SetOfSingletons(
        type=Grouping.OR,
        entities=tuple(grouped_nodes),
        min=min(grouped_nodes, key=lambda x: x.min).min,
        max=max(grouped_nodes, key=lambda x: x.max).max,
        confidence=1
    )

def edge(g, verb, h, isNegated):
    return Relationship(
                    source=g,
                    target=h,
                    edgeLabel=Singleton(
                        named_entity=verb,
                        properties=frozenset(dict().items()),
                        min=-1,
                        max=-1,
                        type="verb",
                        confidence=-1
                    ),
                    isNegated=isNegated
                )

def graph(edges):
    e = []
    for g,verb,h,isneg in edges:
        e.append(edge(g, verb, h, isneg))
    return Graph(edges=e)

if __name__ == '__main__':
    conf  = "/home/giacomo/projects/similarity-pipeline/submodules/news-crawler/config_proposed.yaml"
    try:
        with open(conf) as f:
            cfg = yaml.load(f, Loader=yaml.FullLoader)
    except FileNotFoundError:
        raise Exception("Error: missing configuration file")
    l = LegacyPipeline(cfg)
    Alice = singlet("Alice")
    Bob = singlet("Bob")
    soccer = singlet("soccer")
    a = graph([(Alice,"plays",soccer,False)])
    na = graph([(Alice,"plays",soccer,True)])
    b = graph([(Bob, "plays", soccer, False)])
    ab = graph([(_or(Alice,Bob), "plays", soccer, False)])
    # print(l.graph_similarity(a,b))
    # print(l.graph_similarity(a,na))
    # print(l.graph_similarity(a,ab))
    # print(l.graph_similarity(b,ab))
    # print(l.graph_similarity(ab,a))
    # print(l.graph_similarity(ab,b))
