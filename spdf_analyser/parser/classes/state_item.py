from ... import *

from .production_rule import ProductionRule
from .symbol import Terminal
from .transition import Transition


class StateItem:
    __slots__ = ("production", "dot_position", "lookaheads", "transition")

    def __init__(self, production: ProductionRule, dot_position: int = 0, lookaheads: Iterable[Terminal] = tuple(), transition: Optional[Transition] = None) -> None:
        self.production: ProductionRule = production
        self.dot_position: int = dot_position
        self.lookaheads: Tuple[Terminal] = tuple(lookaheads)
        self.transition: Optional[Transition] = transition

    def __eq__(self, other: Any) -> bool:
        return (isinstance(other, StateItem) and 
                self.production == other.production and 
                self.dot_position == other.dot_position and
                self.lookaheads == other.lookaheads and
                self.transition == other.transition)

    def __hash__(self) -> int:
        return hash((self.production, self.dot_position, self.lookaheads, self.transition))

    def __str__(self) -> str:
        rhs = list(self.production.rhs)
        rhs.insert(self.dot_position, '•') # Insert dot at the correct position
        return f"[{self.production.lhs} -> {' '.join(map(str, rhs))}, {{{', '.join(map(str, self.lookaheads))}}}{f' ({self.transition.from_symbol} -> {self.transition.to_state})' if self.transition else ''}]"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__str__()})"

    def has_base_item(base: Self, iter: Iterable[Self]) -> Tuple[int]:
        has_base = []
        for i, item in enumerate(iter):
            if item.production == base.production\
                and item.dot_position == base.dot_position\
                and item.transition == base.transition:
                has_base.append(i)
        return has_base