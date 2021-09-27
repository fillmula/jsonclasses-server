from __future__ import annotations
from typing import Callable, NamedTuple
from .actx import ACtx


class APIRecord(NamedTuple):
    method: str
    url: str
    callback: Callable[[ACtx], None]
