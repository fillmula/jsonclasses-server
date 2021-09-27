from __future__ import annotations
from typing import ClassVar
from jsonclasses_orm.orm_object import ORMObject
from .aconf import AConf


class APIObject(ORMObject):

    aconf: ClassVar[AConf]
