from dataclasses import dataclass, field
from typing import List, Tuple, Dict


class Formula:
    pass

@dataclass(order=True, frozen=True, eq=True)
class FVariable(Formula):
    name: str
    type: str
    specification: str #extra
    cop: Formula
    meta: str = field(default_factory=lambda : "FVariable")

    def strippedByType(self):
        return FVariable(name=self.name, type="TODO", specification=self.specification, cop=stripArg(self.cop))

def stripArg(x):
    if x is None:
        return x
    else:
        return x.strippedByType()

def prune_from_cop(var:FVariable):
    return FVariable(name=var.name, type=var.type, specification=var.specification, cop=None)

def stripFrozenProperties(coll):
    d = dict()
    for x,y in coll:
        if isinstance(y,Formula):
            d[x] = y.strippedByType()
        else:
            d[x] = y
    return frozenset(d.items())

@dataclass(order=True, frozen=True, eq=True)
class FUnaryPredicate(Formula):
    rel: str
    arg: Formula
    score: float
    properties: frozenset
    meta: str = field(default_factory=lambda : "FUnaryPredicate")

    def semantic(self, d:Dict[Formula, bool]):
        assert self in d
        return d[self]

    def getAtoms(self):
        s =  {self}
        return s

    def strippedByType(self):
        return FUnaryPredicate(rel=self.rel, arg=stripArg(self.src), score=self.score, properties=stripFrozenProperties(self.properties))


@dataclass(order=True, frozen=True, eq=True)
class FBinaryPredicate(Formula):
    rel:str
    src: Formula
    dst: Formula
    score: float
    properties: frozenset
    meta: str = field(default_factory=lambda : "FBinaryPredicate")

    def semantic(self, d:Dict[Formula, bool]):
        assert self in d
        return d[self]

    def getAtoms(self):
        s = {self}
        return s

    def strippedByType(self):
        return FBinaryPredicate(rel=self.rel, src=stripArg(self.src), dst=stripArg(self.dst), score=self.score, properties=stripFrozenProperties(self.properties))

@dataclass(order=True, frozen=True, eq=True)
class FAnd(Formula):
    args: Tuple[Formula]
    meta: str = field(default_factory=lambda : "FAnd")

    def semantic(self, d:Dict[Formula, bool]):
        # assert self in d
        return min(map(lambda x: x.semantic(d), self.args))

    def getAtoms(self):
        s = set()
        for x in self.args:
            s = s.union(x.getAtoms())
        return s

    def strippedByType(self):
        return FAnd(args=tuple(map(lambda x: x.strippedByType(), self.args)))

@dataclass(order=True, frozen=True, eq=True)
class FOr(Formula):
    args: Tuple[Formula]
    meta: str = field(default_factory=lambda : "FOr")

    def semantic(self, d:Dict[Formula, bool]):
        return max(map(lambda x: x.semantic(d), self.args))

    def getAtoms(self):
        s = set()
        for x in self.args:
            s = s.union(x.getAtoms())
        return s

    def strippedByType(self):
        return FOr(args=tuple(map(lambda x: x.strippedByType(), self.args)))

@dataclass(order=True, frozen=True, eq=True)
class FNot(Formula):
    arg: Formula
    meta: str = field(default_factory=lambda : "FNot")

    def semantic(self, d:Dict[Formula, bool]):
        return 1-self.arg.semantic(d)

    def getAtoms(self):
        return self.arg.getAtoms()

    def strippedByType(self):
        return FNot(arg=self.arg.strippedByType())

