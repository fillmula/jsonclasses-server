from __future__ import annotations
from typing import Any, Optional
from jsonclasses.jobject import JObject


class ACtx:
    id: Optional[str]
    prid: Optional[str]
    operator: Optional[type[JObject]]
    qs: Optional[str]
    body: Optional[dict[str, Any]]
