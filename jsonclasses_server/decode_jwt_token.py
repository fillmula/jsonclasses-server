from __future__ import annotations
from datetime import timedelta, datetime
from jsonclasses.cgraph import CGraph
from jsonclasses.user_conf import user_conf
from jsonclasses.orm_object import ORMObject


def decode_jwt_token(token: str, gname: str = 'default') -> ORMObject | None:
    from jwt import decode
    operator_conf = user_conf().get('operator')
    secret_key = operator_conf.get('secretKey')
    decoded = decode(token, secret_key, algorithms=['HS256'])
    id = decoded['id']
    class_name = decoded['class']
    expired_at = decoded['expired_at']
    graph = CGraph(gname)
    cls = graph.fetch(class_name).cls
    return cls.id(id).exec()
