from ... import *


# Declare generic types
Key = TypeVar("Key")
Value = TypeVar("Value")


class Table(ABC, Generic[Key, Value]):
    __slots__ = ()

    def __init__(self, value_type: Optional[Type[Value]] = None) -> None:
        self._table: Dict[Key, Value] = defaultdict(value_type)
        self._value_type: Type = value_type

    def __eq__(self, other: Any) -> bool:
        return (isinstance(other, Table) and 
                self._table == other._table)

    def __hash__(self) -> int:
        return hash((self._table))

    def __str__(self) -> str:
        # TODO VISUALIZATION
        return self._table.__str__()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__str__()})"

    def __iter__(self) -> Generator[Tuple[Key, Value], Any, None]:
        yield from self._table.items()
    
    def __getitem__(self, index: Key) -> Value:
        return self._table[index]

    def __bool__(self) -> bool:
        return len(self._table.items()) > 0

    @property
    def table(self) -> Dict[Key, Value]:
        return self._table

    @property
    def value_type(self) -> Type[Value]:
        return self._value_type

    @abstractmethod
    def build(self) -> None:
        pass

    def from_keys(self, keys: Optional[Iterable[Any]] = None) -> None:
        self._table: Dict[Key, Value] = defaultdict(self._value_type)
        if keys:
            self._table.update([
                (k, self._value_type() if self._value_type else None) for k in keys
            ])