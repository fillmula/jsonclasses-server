from __future__ import annotations
from datetime import timedelta, datetime
from jsonclasses_orm.orm_object import ORMObject


def encode_jwt_token(operator: ORMObject, secret_key: str, expired_in: timedelta) -> str:
    from jwt import encode
    data = {
        'operator': operator._id,
        'expired_at': (datetime.now() + expired_in).timestamp()
    }
    return encode(data, secret_key, algorithm='HS256')
