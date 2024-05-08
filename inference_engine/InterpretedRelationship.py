__author__ = "Giacomo Bergami"
__copyright__ = "Copyright 2024, Giacomo Bergami"
__credits__ = ["Giacomo Bergami"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Giacomo Bergami"
__email__ = "bergamigiacomo@gmail.com"
__status__ = "Production"
import dataclasses
from typing import List, Dict

from inference_engine.EntityRelationship import Singleton

# @dataclasses.dataclass(order=True, frozen=True, eq=True)
# class TextProvenance:
#     text: str
#     start_char: int
#     end_char: int
#
# @dataclasses.dataclass(order=True, frozen=True, eq=True)
# class Interpretation:
#     type: str
#     monad: str
#     provenance: TextProvenance
#     confidence: float
#
#     def getText(self):
#         return self.monad ##???
#
# @dataclasses.dataclass(order=True, frozen=True, eq=True)
# class InterpretedEntity:
#     entity: Singleton
#     isNegated: bool
#     interpretations: List[Interpretation]
#
#     def asInterpretations(self):
#         return [InterpretWithNegation(interpretation=x, isNegated=self.isNegated) for x in self.interpretations]
#
#
# @dataclasses.dataclass(order=True, frozen=True, eq=True)
# class InterpretWithNegation:
#     interpretation: Interpretation
#     isNegated: bool
#
# @dataclasses.dataclass(order=True, frozen=True, eq=True)
# class InterpretedRelationship:
#     rel: InterpretedEntity
#     src: InterpretedEntity
#     dst: InterpretedEntity
#     properties: dict = dataclasses.field(default_factory=lambda: {
#         'time': List[Singleton],
#         'loc': List[Singleton]
#     })
#
#     def isNegated(self) -> bool:
#         return self.rel.isNegated
#
# @dataclasses.dataclass(order=True, frozen=True, eq=True)
# class AsInterpretation:
#     rel: InterpretWithNegation
#     src: InterpretWithNegation
#     dst: InterpretWithNegation
#     properties: Dict[str, List[InterpretWithNegation]]