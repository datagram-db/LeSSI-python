from collections import defaultdict

from scipy._lib.array_api_compat.array_api_compat import numpy

from inference_engine.EntityRelationship import NodeEntryPoint, Singleton, SetOfSingletons, Grouping
from inference_engine.Sentence import Sentence
from logical_repr.Sentences import FNot, FOr, FAnd, FUnaryPredicate, FVariable, FBinaryPredicate, Formula, \
    prune_from_cop

bogus_dst = FVariable(name="there", type="non_verb", specification=None, cop=None)
bogus_src = {"it"}

def property_write(key, val:NodeEntryPoint)->str:
    value = '""'
    # if isinstance(val, Singleton):
    return f'{key} : {value}'

def make_cop(entity)->FVariable:
    if entity is None:
        return None
    elif isinstance(entity, str):
        return FVariable(name=entity, type="JJ", specification=None, cop=None)
    else:
        return make_arg(entity)


def make_arg(entity):
    if entity is None:
        return None
    elif isinstance(entity, FVariable):
        return entity
    props = entity if isinstance(entity, dict) else dict(entity.properties)
    specification = props["extra"] if "extra" in props else None
    cop = make_cop(props["cop"]) if "cop" in props else None
    named_entity = props["named_entity"] if isinstance(entity, dict) else entity.named_entity
    type = props["type"] if isinstance(entity, dict) else entity.type
    return FVariable(name=named_entity, type=type, specification=specification, cop=cop)

def make_and(entities):
    return FAnd(args=tuple(entities))

def make_or(entities):
    return FOr(args=tuple(entities))

def make_not(param):
    return FNot(arg=param)

def make_unary(rel, dst, score, prop):
    if rel == "be": # TODO: generalise
        if dst is not None and dst.cop is not None: # TODO: generalise
            return make_binary("have", prune_from_cop(dst), dst.cop, score, prop)
        if dst is not None and (dst.type =="DATE" or dst.type =="GPE" or dst.type =="LOC") and dst.cop is not None: # TODO: generalise
            if dst.type not in prop:
                prop[dst.type] = []
            prop[dst.type].append(dst)
            return make_unary(rel, dst.cop, score, prop)
    return FUnaryPredicate(rel=rel, arg=dst, score=score, properties=prop)

def make_binary(rel, src, dst, score, prop):
    if rel == "have":# TODO: generalise
        if src is not None and (src.type =="DATE" or src.type =="GPE" or src.type =="LOC") and src.cop is None: # TODO: generalise
            if src.type not in prop:
                prop[src.type] = []
            prop[src.type].append(src)
            return make_unary("be", dst, score, prop)
    return FBinaryPredicate(rel=rel, src=src, dst=dst, score=score, properties=prop)

def make_properties(p):
    result = defaultdict(set)
    if "not" in set(map(lambda x: x.lower(), p.keys())):
        for k in filter(lambda x: x.lower() == "not", p.keys()):
            for single_val in p[k]:
                if isinstance(single_val, SetOfSingletons):
                    assert len(single_val.entities) == 1
                    single_val = single_val.entities[0]
                assert isinstance(single_val, Singleton)
                type = single_val.type
                single_val = make_not(make_arg(single_val))
                result[type].add(single_val)

    for k,v in p.items():
        if str(k) == "\u2203" or str(k).lower() == "in" or str(k).lower() == "not":
            continue
        else:
            for single_val in v:
                tmp = make_arg(single_val)
                neg_tmp = make_not(tmp)
                if neg_tmp not in result[k]:
                    result[k].add(tmp)

    result2 = dict()
    for k,v in result.items():
        result2[k] = list(v)
    return result2 #dict(result2.items())


def make_prop(src, rel, negated, score,properties, dst):
    if (dst is not None):
        if isinstance(dst, SetOfSingletons):
            if dst.type == Grouping.AND:
                return make_and(map(lambda x : make_prop(src, rel, negated, score, properties, x), dst.entities))
            elif dst.type == Grouping.OR:
                return make_or(map(lambda x: make_prop(src, rel, negated, score, properties, x), dst.entities))
            elif dst.type == Grouping.NOT:
                return make_not(make_prop(src, rel, negated, score, properties, list(dst.entities)[0]))
            else:
                n = dst.type.name
                raise RuntimeError(f"Unknown source type: {n}")
        else:
            if negated:
                return make_not(make_prop(src, rel, False, score, properties, dst))
            else:
                p = dict()
                for k,v in properties.items():
                    p[k] = v
                src = make_arg(src)
                p["src"] = []
                p["dst"] = []
                if src is not None:
                    p["src"].append(src)
                dst = make_arg(dst)
                if dst is not None:
                    p["dst"].append(dst)
                prop = make_properties(p)
                del prop["src"]
                del prop["dst"]
                if src.name.lower() in bogus_src and rel.lower() == "be":
                    if src.cop is None:
                        return make_unary(rel, dst, score, prop)
                    else:
                        src = src.cop
                if dst == bogus_dst:
                    return make_unary(rel, src, score, prop)
                else:
                    return make_binary(rel, src, dst, score, prop)
    else:
        if negated:
            return make_not(make_prop(src, rel, False, score, properties, None))
        else:
            p = dict()
            for k, v in properties.items():
                p[k] = v
            p["src"] = []
            p["dst"] = []
            if src is not None:
                p["src"].append(src)
            prop = make_properties(p)
            del prop["src"]
            if "dst" in prop:
                del prop["dst"]
            return make_unary(rel, make_arg(src), score, prop)



def src_make_prop(src, rel, negated, score,properties, dst):
    if src is not None:
        if isinstance(src, SetOfSingletons):
            if src.type == Grouping.AND:
                return make_and(map(lambda x : src_make_prop(x, rel, negated, score, properties, dst), src.entities))
            elif src.type == Grouping.OR:
                return make_or(map(lambda x: src_make_prop(x, rel, negated, score, properties, dst), src.entities))
            elif src.type == Grouping.NOT:
                return make_not(src_make_prop(list(src.entities)[0], rel, negated, score,properties, dst))
            else:
                n = src.type.name
                raise RuntimeError(f"Unknown source type: {n}")
        else:
            return make_prop(src, rel, negated,score, properties, dst)
    else:
        return make_prop(None, rel, negated, score,properties,dst)

def rewrite_kernels(obj:Sentence)->Formula:
    main_pop = obj.kernel
    properties = obj.properties
    rel = main_pop.edgeLabel.named_entity
    negated = main_pop.isNegated

    score = 1.0
    #TODO: @Olvier. this, at the end of the debugging, shall not be 0 (Giacomo)
    # score = main_pop.edgeLabel.confidence
    # if main_pop.source is not None:
    #     score *= main_pop.source.confidence
    # if main_pop.target is not None:
    #     score *= main_pop.target.confidence

    return src_make_prop(main_pop.source, rel, negated, score, properties, main_pop.target)

    # not_ = "~" if main_pop.isNegated else " "
    # rel = main_pop.edgeLabel.named_entity

    # isExactMatch = numpy.isclose(score, 1.0)
    # score = " " if isExactMatch else str(score)
    #
    # L = []
    # if main_pop.source is not None:
    #     L.append(property_write("src", main_pop.source))
    # if main_pop.target is not None:
    #     L.append(property_write("dst", main_pop.source))
    # for k,v in properties.items():
    #     L.append(property_write(k, v))
    # args = "; ".join(L)
    #
    # return f' {not_} "{rel}" {score} := {args} .'

