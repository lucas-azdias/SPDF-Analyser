from ... import *

from .. import DEFAULT_PARSER_EPSILON_MARKER

from .symbol import NonTerminal, Symbol


class ProductionRule:
    __slots__ = ("lhs", "rhs")

    def __init__(self, lhs: NonTerminal, rhs: Tuple[Symbol, ...]) -> None:
        self.lhs: NonTerminal = lhs
        self.rhs: Tuple[Symbol, ...] = rhs

    def __eq__(self, other: Any) -> bool:
        return (isinstance(other, ProductionRule) and 
                self.lhs == other.lhs and 
                self.rhs == other.rhs)

    def __hash__(self) -> int:
        return hash((self.lhs, self.rhs))

    def __str__(self) -> str:
        return f"{self.lhs} -> {' '.join(str(s) for s in self.rhs)}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__str__()})"

    def is_rhs_empty(self) -> bool:
        return self.rhs == "" or self.rhs == DEFAULT_PARSER_EPSILON_MARKER
