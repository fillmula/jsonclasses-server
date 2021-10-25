from __future__ import annotations
from typing import ClassVar, TYPE_CHECKING
from jsonclasses.orm_object import ORMObject
if TYPE_CHECKING:
    from .aconf import AConf


class APIObject(ORMObject):

    aconf: ClassVar[AConf]
