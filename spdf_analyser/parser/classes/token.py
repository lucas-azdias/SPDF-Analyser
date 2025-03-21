from ... import *


class Token:
    __slots__ = ("category", "string", "line", "position")

    def __init__(self, category: str, string: str, line: int, position: int) -> None:
        self.category: str = category
        self.string: str = string
        self.line: str = line
        self.position: str = position

    def __eq__(self, other: Any) -> bool:
        return (isinstance(other, Token) and 
                self.category == other.category and 
                self.string == other.string and
                self.line == other.line and
                self.position == other.position)

    def __hash__(self) -> int:
        return hash((self.category, self.string, self.line, self.position))

    def __str__(self) -> str:
        return f"<category={self.category}, string=\"{self.string}\", line={self.line}, position={self.position}>"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__str__()})"