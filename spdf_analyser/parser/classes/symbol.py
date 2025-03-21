from ... import *


class Symbol(ABC):
    @abstractmethod
    def __init__(self, value: str) -> None:
        pass

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Symbol) and self.__hash__() == other.__hash__()

    def __hash__(self) -> int:
        return hash(self.__str__())

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__str__()})"

    @property
    def value(self) -> str:
        return self._value

    @property
    def pattern(self) -> Pattern:
        return self._pattern

    @value.setter
    @abstractmethod
    def value(self, value) -> None:
        pass

    def is_terminal(self) -> bool:
        return isinstance(self, Terminal)

    def is_non_terminal(self) -> bool:
        return isinstance(self, NonTerminal)


class Terminal(Symbol):
    def __init__(self, value: str, escape_value: bool = False) -> None:
        self._value: str = value
        self._pattern: Pattern[str] = compile(value) if not escape_value else compile(escape(value))

    @Symbol.value.setter
    def value(self, value) -> None:
        self._value = value
        self._pattern = compile(value)


class NonTerminal(Symbol):
    def __init__(self, value: str) -> None:
        self._value: str = value
        self._pattern: Pattern[str] = compile(escape(value))

    @Symbol.value.setter
    def value(self, value) -> None:
        self._value = value
        self._pattern = compile(escape(value))