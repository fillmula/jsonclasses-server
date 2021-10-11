from __future__ import annotations
from typing import Any, Callable, Literal, NamedTuple, Tuple
from .actx import ACtx


class APIRecord(NamedTuple):
    uid: str
    kind: Literal['C', 'R', 'U', 'D', 'L', 'S', 'E']
    method: str
    url: str
    callback: Callable[[ACtx], Tuple[int, Any]]
