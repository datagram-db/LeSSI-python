from dataclasses import dataclass, field
from typing import List, Tuple


class Formula:
    pass

@dataclass(order=True, frozen=True, eq=True)
class FVariable(Formula):
    name: str
    type: str
    specification: str #extra
    cop: Formula
    meta: str = field(default_factory=lambda : "FVariable")

def prune_from_cop(var:FVariable):
    return FVariable(name=var.name, type=var.type, specification=var.specification, cop=None)

@dataclass(order=True, frozen=True, eq=True)
class FUnaryPredicate(Formula):
    rel: str
    arg: Formula
    score: float
    properties: dict = field(default_factory=lambda: {
    })
    meta: str = field(default_factory=lambda : "FUnaryPredicate")

@dataclass(order=True, frozen=True, eq=True)
class FBinaryPredicate(Formula):
    rel:str
    src: Formula
    dst: Formula
    score: float
    properties: dict = field(default_factory=lambda: {
    })
    meta: str = field(default_factory=lambda : "FBinaryPredicate")

@dataclass(order=True, frozen=True, eq=True)
class FAnd(Formula):
    args: Tuple[Formula]
    meta: str = field(default_factory=lambda : "FAnd")

@dataclass(order=True, frozen=True, eq=True)
class FOr(Formula):
    args: Tuple[Formula]
    meta: str = field(default_factory=lambda : "FOr")

@dataclass(order=True, frozen=True, eq=True)
class FNot(Formula):
    arg: Formula
    meta: str = field(default_factory=lambda : "FNot")