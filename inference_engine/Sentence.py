from dataclasses import dataclass, field
from typing import List

from inference_engine.EntityRelationship import Relationship, NodeEntryPoint

@dataclass(order=True, frozen=True, eq=True)
class Sentence:
    kernel: Relationship
    properties: dict = field(default_factory=lambda: {
        'time': List[NodeEntryPoint],
        'loc': List[NodeEntryPoint]
    })