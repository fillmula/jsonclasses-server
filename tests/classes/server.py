from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from jsonclasses import jsonclass, jsonenum, types
from jsonclasses_pymongo import pymongo
from jsonclasses_server import api, authorized, server



@jsonenum
class Sex(Enum):
    MALE = 1
    FEMALE = 2


@authorized
@api
@pymongo
@jsonclass(can_update=types.getop.isthis)
class User:
    id: str = types.readonly.str.primary.mongoid.required
    username: str = types.str.unique.authidentity.required
    password: str = types.writeonly.str.length(8, 16).authby(types.eq(types.passin)).required
    sex: Optional[Sex] = types.writeonce.enum(Sex)
    articles: list[Article] = types.listof('Article').linkedby('author')
    created_at: datetime = types.readonly.datetime.tscreated.required
    updated_at: datetime = types.readonly.datetime.tsupdated.required


@api
@pymongo
@jsonclass
class Article:
    id: str = types.readonly.str.primary.mongoid.required
    title: str
    content: str
    author: User = types.objof('User').linkto.asopd.required
    created_at: datetime = types.readonly.datetime.tscreated.required
    updated_at: datetime = types.readonly.datetime.tsupdated.required


@api
@pymongo
@jsonclass
class Song:
    id: str = types.readonly.str.primary.mongoid.required
    name: str
    year: int | None
    created_at: datetime = types.readonly.datetime.tscreated.required
    updated_at: datetime = types.readonly.datetime.tsupdated.required


app = server()
