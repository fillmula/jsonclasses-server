from __future__ import annotations
from typing import Any, Callable, Literal, NamedTuple, Tuple
from .actx import ACtx


class APIRecord(NamedTuple):
    kind: Literal['C', 'R', 'U', 'D', 'L']
    method: str
    url: str
    callback: Callable[[ACtx], Tuple[int, Any]]
