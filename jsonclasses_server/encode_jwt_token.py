from __future__ import annotations
from datetime import timedelta, datetime
from jsonclasses.user_conf import user_conf
from jsonclasses.orm_object import ORMObject


def encode_jwt_token(operator: ORMObject, expired_in: timedelta) -> str:
    from jwt import encode
    operator_conf = user_conf().get('operator')
    secret_key = operator_conf.get('secretKey')
    data = {
        'class': operator.__class__.__name__,
        'id': operator._id,
        'expired_at': (datetime.now() + expired_in).timestamp()
    }
    return encode(data, secret_key, algorithm='HS256')
