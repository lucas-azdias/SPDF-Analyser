from ... import *


PARSER_ACTION = Enum("PARSER_ACTION", ["SHIFT", "GOTO", "REDUCE", "ACCEPT", "ERROR", "CONFLICT"])


class ActionEntry:
    __slots__ = ("action", "param")

    def __init__(self, action: PARSER_ACTION, param: Optional[int] = None) -> None:
        self.action: PARSER_ACTION = action
        self.param: Optional[int] = param

    def __eq__(self, other: Any) -> bool:
        return (isinstance(other, ActionEntry) and 
                self.action == other.action and 
                self.param == other.param)

    def __hash__(self) -> int:
        return hash((self.action, self.param))

    def __str__(self) -> str:
        return f"<action={self.action.name}{'' if self.param is None else f', param={self.param}'}>"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__str__()})"