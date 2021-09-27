from __future__ import annotations
from typing import Any, NamedTuple, Optional
from jsonclasses.jobject import JObject


class ACtx(NamedTuple):
    id: Optional[Any] = None
    prid: Optional[Any] = None
    operator: Optional[type[JObject]] = None
    qs: Optional[str] = None
    body: Optional[dict[str, Any]] = None
