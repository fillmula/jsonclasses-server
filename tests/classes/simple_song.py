from __future__ import annotations
from jsonclasses import jsonclass, types
from jsonclasses_pymongo import pymongo
from jsonclasses_server import api


@api
@pymongo
@jsonclass
class SimpleSong:
    id: str = types.readonly.str.primary.mongoid.required
    name: str = types.str.required
