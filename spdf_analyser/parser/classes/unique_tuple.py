from ... import *

from .unique_list import UniqueList


T = TypeVar("T")


class UniqueTuple(Generic[T], Tuple[T]):
    def __new__(cls, iterable: Optional[Iterable[T]] = None) -> Self:
        return super().__new__(cls, UniqueList(iterable))

    def __sub__(self, other: Iterable[T]) -> Self:
        result = [item for item in self if item not in other]
        return UniqueTuple(result)

    def __repr__(self) -> str:
        return f"UniqueTuple({super().__repr__()})"