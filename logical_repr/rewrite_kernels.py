from scipy._lib.array_api_compat.array_api_compat import numpy

from inference_engine.EntityRelationship import NodeEntryPoint, Singleton
from inference_engine.Sentence import Sentence

def property_write(key, val:NodeEntryPoint)->str:
    value = '""'
    # if isinstance(val, Singleton):
    return f'{key} : {value}'

def rewrite_kernels(obj:Sentence)->str:
    main_pop = obj.kernel
    properties = obj.properties

    not_ = "~" if main_pop.isNegated else " "
    rel = main_pop.edgeLabel.named_entity
    score = main_pop.edgeLabel.confidence
    if main_pop.source is not None:
        score *= main_pop.source.confidence
    if main_pop.target is not None:
        score *= main_pop.target.confidence
    isExactMatch = numpy.isclose(score, 1.0)
    score = " " if isExactMatch else str(score)

    L = []
    if main_pop.source is not None:
        L.append(property_write("src", main_pop.source))
    if main_pop.target is not None:
        L.append(property_write("dst", main_pop.source))
    for k,v in properties.items():
        L.append(property_write(k, v))
    args = "; ".join(L)

    return f' {not_} "{rel}" {score} := {args} .'

