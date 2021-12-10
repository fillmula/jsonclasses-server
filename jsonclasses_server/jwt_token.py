from __future__ import annotations
from datetime import timedelta, datetime
from jsonclasses.pkgutils import check_and_install_packages
from jsonclasses.cgraph import CGraph
from jsonclasses.uconf import uconf
from jsonclasses.orm import ORMObject


default_operator_conf = {
    "secretKey": "!@#$%^&*())(*&^%$#@"
}

def check_jwt_installed() -> None:
    packages = {'jwt': ('pyjwt', '>=2.1.0,<3.0.0')}
    check_and_install_packages(packages)


def decode_jwt_token(token: str, gname: str = 'default') -> ORMObject | None:
    check_jwt_installed()
    from jwt import decode
    operator_conf = uconf().get('operator') or default_operator_conf
    secret_key = operator_conf.get('secret_key')
    decoded = decode(token, secret_key, algorithms=['HS256'])
    id = decoded['id']
    class_name = decoded['class']
    expired_at = decoded['expired_at']
    graph = CGraph(gname)
    cls = graph.fetch(class_name).cls
    return cls.id(id).exec()


def encode_jwt_token(operator: ORMObject, expired_in: timedelta) -> str:
    check_jwt_installed()
    from jwt import encode
    operator_conf = uconf().get('operator') or default_operator_conf
    secret_key = operator_conf.get('secret_key')
    data = {
        'class': operator.__class__.__name__,
        'id': operator._id,
        'expired_at': (datetime.now() + expired_in).timestamp()
    }
    return encode(data, secret_key, algorithm='HS256')
