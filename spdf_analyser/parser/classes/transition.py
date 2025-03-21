from ... import *

from .symbol import Symbol


class Transition:
    __slots__ = ("from_symbol", "to_state")

    def __init__(self, from_symbol: Symbol, to_state: int) -> None:
        self.from_symbol: Symbol = from_symbol
        self.to_state: int = to_state

    def __eq__(self, other: Any) -> bool:
        return (isinstance(other, Transition) and 
                self.from_symbol == other.from_symbol and 
                self.to_state == other.to_state)

    def __hash__(self) -> int:
        return hash((self.from_symbol, self.to_state))

    def __str__(self) -> str:
        return f"{self.from_symbol} -> {self.to_state}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__str__()})"