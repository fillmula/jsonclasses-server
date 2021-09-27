from __future__ import annotations
from typing import Any, Callable, NamedTuple, Tuple
from .actx import ACtx


class APIRecord(NamedTuple):
    method: str
    url: str
    callback: Callable[[ACtx], Tuple[int, Any]]
