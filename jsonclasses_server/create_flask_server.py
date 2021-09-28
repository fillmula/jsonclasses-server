from __future__ import annotations
from typing import Any, TypedDict, Optional, Callable, TYPE_CHECKING
from re import sub
from os import getcwd, path
from traceback import extract_tb, print_exception
from jsonclasses_orm.orm_object import ORMObject
from jsonclasses.excs import ObjectNotFoundException
from .api_class import API
from .actx import ACtx
from .api_record import APIRecord
if TYPE_CHECKING:
    from flask import Flask, Blueprint, Response


class CorsSetting(TypedDict):
    allow_headers: Optional[str]
    allow_origin: Optional[str]
    allow_methods: Optional[str]


class OperatorSetting(TypedDict):
    operator_cls: type[ORMObject]
    encode_key: str


def _remove_none(obj: dict) -> dict:
    return {k: v for k, v in obj.items() if v is not None}



def _decode_jwt_token(token: str) -> ORMObject:
    from flask import current_app
    from jwt import decode
    key = current_app.config['jsonclasses_encode_key']
    id = decode(token, key, algorithms=['HS256'])['operator']
    cls = current_app.config['jsonclasses_operator_cls']
    return cls.id(id).exec()


def _set_operator():
    from flask import request, g
    from werkzeug.exceptions import Unauthorized
    from jwt import DecodeError
    if 'authorization' not in request.headers:
        g.operator = None
        return
    authorization = request.headers['authorization']
    token = authorization[7:]
    try:
        decoded = _decode_jwt_token(token)
    except DecodeError:
        raise Unauthorized('authorization token is invalid')
    except ObjectNotFoundException:
        raise Unauthorized('user is not authorized')
    g.operator = decoded


def _ensure_operator():
    from flask import g
    from werkzeug.exceptions import Unauthorized
    if g.operator is None:
        raise Unauthorized('sign in required')


def _encode_jwt_token(operator: ORMObject) -> str:
    from flask import current_app
    from jwt import encode
    key = current_app.config['jsonclasses_encode_key']
    return encode({'operator': operator._id}, key, algorithm='HS256')


def _handle_cors_options(cors: CorsSetting) -> Callable[[], Optional[Response]]:
    from flask import request, current_app
    def handler():
        if request.method == 'OPTIONS':
            res = current_app.response_class()
            res.status_code = 204
            res.headers['Access-Control-Allow-Origin'] = cors.get('allow_origin') or '*'
            res.headers['Access-Control-Allow-Methods'] = cors.get('allow_methods') or 'OPTIONS, POST, GET, PATCH, DELETE'
            res.headers['Access-Control-Allow-Headers'] = cors.get('allow_headers') or '*'
            res.headers['Access-Control-Max-Age'] = '86400'
            return res
    return handler


def _add_cors_headers(cors: CorsSetting) -> Callable[[Response], Response]:
    def handler(response: Response) -> Response:
        res = response
        res.headers['Access-Control-Allow-Origin'] = cors.get('allow_origin') or '*'
        return res
    return handler


def _exception_handler(exception: Exception) -> tuple[Response, int]:
    from flask import Response, jsonify, current_app
    from werkzeug.exceptions import HTTPException
    from jsonclasses.excs import (ObjectNotFoundException,
                                  ValidationException,
                                  UniqueConstraintException,
                                  UnauthorizedActionException)
    code = exception.code if isinstance(exception, HTTPException) else 500
    code = 404 if isinstance(exception, ObjectNotFoundException) else code
    code = 400 if isinstance(exception, ValidationException) else code
    code = 400 if isinstance(exception, UniqueConstraintException) else code
    code = 401 if isinstance(exception, UnauthorizedActionException) else code
    if current_app.debug:
        if code == 500:
            print_exception(etype=type[exception], value=exception, tb=exception.__traceback__)
            return jsonify({
                'error': _remove_none({
                    'type': 'Internal Server Error',
                    'message': 'There is an internal server error.',
                    'error_type': exception.__class__.__name__,
                    'error_message': str(exception),
                    'fields': (exception.keypath_messages
                               if (isinstance(exception, ValidationException) or isinstance(exception, UniqueConstraintException))
                               else None),
                    'traceback': [f'file {path.relpath(f.filename, getcwd())}:{f.lineno} in {f.name}' for f in extract_tb(exception.__traceback__)],  # noqa: E501
                })
            }), code
        else:
            return jsonify({
                'error': _remove_none({
                    'type': exception.__class__.__name__,
                    'message': str(exception),
                    'fields': (exception.keypath_messages
                               if (isinstance(exception, ValidationException) or isinstance(exception, UniqueConstraintException))
                               else None),
                    'traceback': [f'file {path.relpath(f.filename, getcwd())}:{f.lineno} in {f.name}' for f in extract_tb(exception.__traceback__)],  # noqa: E501
                })
            }), code
    else:
        if code == 500:
            print_exception(etype=type[exception], value=exception, tb=exception.__traceback__)
            return jsonify({
                'error': _remove_none({
                    'type': 'Internal Server Error',
                    'message': 'There is an internal server error.'
                })
            }), code
        else:
            return jsonify({
                'error': _remove_none({
                    'type': exception.__class__.__name__,
                    'message': str(exception),
                    'fields': (exception.keypath_messages
                               if (isinstance(exception, ValidationException) or isinstance(exception, UniqueConstraintException))
                               else None)
                })
            }), code



def _try_import_flask():
    try:
        from flask import Flask
    except ModuleNotFoundError:
        raise 'please install flask in order to use create_flask_server'


def create_flask_server(graph: str = 'default',
                        cors: Optional[CorsSetting] = None,
                        operator: Optional[OperatorSetting] = None) -> Flask:
    _try_import_flask()
    from flask import request, g, jsonify, make_response, Flask, Blueprint
    app = Flask('app')
    app.url_map.strict_slashes = False
    from flask.json import JSONEncoder as FlaskJSONEncoder
    class JSJSONEncoder(FlaskJSONEncoder):
        def default(self, o: Any) -> Any:
            if hasattr(o.__class__, '__is_jsonclass__'):
                return o.tojson()
            return super().default(o)
    app.json_encoder = JSJSONEncoder
    app.register_error_handler(Exception, _exception_handler)
    app.before_request(_handle_cors_options(cors or {}))
    app.after_request(_add_cors_headers(cors or {}))
    if operator is not None:
        app.config['jsonclasses_operator_cls'] = operator['operator_cls']
        app.config['jsonclasses_encode_key'] = operator['encode_key']
        app.before_request(_set_operator)
    for record in API(graph).records:
        flask_url = sub(r':([^/]+)', '<\\1>', record.url)
        bp = Blueprint(record.uid, record.uid)
        if record.kind == 'L':
            _install_l(record, bp, flask_url)
        elif record.kind == 'R':
            _install_r(record, bp, flask_url)
        elif record.kind == 'C':
            _install_c(record, bp, flask_url)
        elif record.kind == 'U':
            _install_u(record, bp, flask_url)
        elif record.kind == 'D':
            _install_d(record, bp, flask_url)
        app.register_blueprint(bp)
    return app


def _install_l(record: APIRecord, bp: Blueprint, url: str) -> None:
    from flask import request, g, jsonify, make_response, Flask, Blueprint
    lcallback = record.callback
    def list_all():
        ctx = ACtx(qs=request.query_string.decode("utf-8") if request.query_string else None)
        [_, result] = lcallback(ctx)
        return jsonify(data=result)
    bp.get(url)(list_all)


def _install_r(record: APIRecord, bp: Blueprint, url: str) -> None:
    from flask import request, g, jsonify, make_response, Flask, Blueprint
    rcallback = record.callback
    def read_by_id(id: Any):
        ctx = ACtx(id=id)
        [_, result] = rcallback(ctx)
        return jsonify(date=result)
    bp.get(url)(read_by_id)


def _install_c(record: APIRecord, bp: Blueprint, url: str) -> None:
    from flask import request, g, jsonify, make_response, Flask, Blueprint
    ccallback = record.callback
    def create():
        ctx = ACtx(body=(request.form | request.files or request.json))
        [_, result] = ccallback(ctx)
        return jsonify(date=result)
    bp.post(url)(create)


def _install_u(record: APIRecord, bp: Blueprint, url: str) -> None:
    from flask import request, g, jsonify, make_response, Flask, Blueprint
    ucallback = record.callback
    def update(id: Any):
        ctx = ACtx(id=id, body=((request.form | request.files) or request.json))
        [_, result] = ucallback(ctx)
        return jsonify(date=result)
    bp.patch(url)(update)


def _install_d(record: APIRecord, bp: Blueprint, url: str) -> None:
    from flask import request, g, jsonify, make_response, Flask, Blueprint
    dcallback = record.callback
    def delete(id: Any):
        ctx = ACtx(id=id)
        dcallback(ctx)
        return make_response('', 204)
    bp.delete(url)(delete)
