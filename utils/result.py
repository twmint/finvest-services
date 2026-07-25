from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True)
class Result(Generic[T, E]):
    value: T | None
    error: E | None

    @property
    def ok(self) -> bool:
        return self.error is None
