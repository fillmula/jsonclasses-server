from typing import Any, TypedDict, Optional, Callable, TYPE_CHECKING
from re import sub
from os import getcwd, path
from json import dumps
from jsonclasses.json_encoder import JSONEncoder
from jsonclasses_orm.orm_object import ORMObject
from traceback import extract_tb, print_exception
from jsonclasses.excs import ObjectNotFoundException
from .api_class import API
from .actx import ACtx
from .api_record import APIRecord



class CorsSetting(TypedDict):
    allow_headers: Optional[str]
    allow_origin: Optional[str]
    allow_methods: Optional[str]


class OperatorSetting(TypedDict):
    operator_cls: type[ORMObject]
    encode_key: str

def _remove_none(obj: dict) -> dict:
    return {k: v for k, v in obj.items() if v is not None}


def _exception_handler(_, exception: Exception) -> 'Response':
    from fastapi import HTTPException, FastAPI
    from jsonclasses.excs import (ObjectNotFoundException,
                                  ValidationException,
                                  UniqueConstraintException,
                                  UnauthorizedActionException)
    code = exception.code if isinstance(exception, HTTPException) else 500
    code = 404 if isinstance(exception, ObjectNotFoundException) else code
    code = 400 if isinstance(exception, ValidationException) else code
    code = 400 if isinstance(exception, UniqueConstraintException) else code
    code = 401 if isinstance(exception, UnauthorizedActionException) else code
    if FastAPI.debug == True:
        if code == 500:
            print_exception(type[exception], value=exception, tb=exception.__traceback__)
            message = {
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
            }
            return Response(media_type="application/json", content=dumps(message, cls=JSONEncoder), status_code=code)
        else:
            message = {
                'error': _remove_none({
                    'type': exception.__class__.__name__,
                    'message': str(exception),
                    'fields': (exception.keypath_messages
                               if (isinstance(exception, ValidationException) or isinstance(exception, UniqueConstraintException))
                               else None),
                    'traceback': [f'file {path.relpath(f.filename, getcwd())}:{f.lineno} in {f.name}' for f in extract_tb(exception.__traceback__)],  # noqa: E501
                })
            }
            return Response(media_type="application/json", content=dumps(message, cls=JSONEncoder), status_code=code)
    else:
        if code == 500:
            print_exception(type[exception], value=exception, tb=exception.__traceback__)
            message = {
                'error': _remove_none({
                    'type': 'Internal Server Error',
                    'message': 'There is an internal server error.'
                })
            }
            return Response(media_type="application/json", content=dumps(message, cls=JSONEncoder), status_code=code)
        else:
            message = {
                'error': _remove_none({
                    'type': exception.__class__.__name__,
                    'message': str(exception),
                    'fields': (exception.keypath_messages
                               if (isinstance(exception, ValidationException) or isinstance(exception, UniqueConstraintException))
                               else None)
                })
            }
            return Response(media_type="application/json", content=dumps(message, cls=JSONEncoder), status_code=code)

def _try_import_fastapi():
    try:
        from fastapi import FastAPI
    except ModuleNotFoundError:
        raise 'please install fastapi in order to use create_fastapi_server'

def create_fastapi_server(graph: str = 'default',
                          cors: Optional[CorsSetting] = {},
                          operator: Optional[OperatorSetting] = None) -> 'FastAPI':
    _try_import_fastapi()
    from pydantic import BaseSettings
    class Settings(BaseSettings):
        jsonclasses_operator_cls: Optional[type[ORMObject]]
        jsonclasses_encode_key: Optional[str]
        operator: Optional[Any]
    settings = Settings()
    from fastapi import FastAPI, Request
    app = FastAPI()
    from functools import lru_cache
    @lru_cache()
    def get_settings():
        return Settings()
    app.add_exception_handler(Exception, _exception_handler)
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[cors.get('allow_origin')] if cors.get('allow_origin') is not None else ['*'],
        allow_credentials=True,
        allow_methods=[cors.get('allow_methods')] if cors.get('allow_methods') is not None else ['OPTIONS', 'POST', 'GET', 'PATCH', 'DELETE'],
        allow_headers=[cors.get('allow_headers')] if cors.get('allow_headers') is not None else ['*'],
        max_age=86400
    )
    if operator is not None:
        settings.jsonclasses_operator_cls = operator['operator_cls']
        settings.jsonclasses_encode_key = operator['encode_key']
        @app.middleware("http")
        def _decode_jwt_token(token: str) -> ORMObject:
            from jwt import decode
            key = settings['jsonclasses_encode_key']
            id = decode(token, key, algorithms=['HS256'])['operator']
            cls = settings['jsonclasses_operator_cls']
            return cls.id(id).exec()
        async def SetOperatorMiddleware(request: Request, call_next):
            from werkzeug.exceptions import Unauthorized
            from jwt import DecodeError
            if 'authorization' not in request.headers:
                settings.operator = None
                return
            authorization = request.headers['authorization']
            token = authorization[7:]
            try:
                decoded = _decode_jwt_token(token)
            except DecodeError:
                raise Unauthorized('authorization token is invalid')
            except ObjectNotFoundException:
                raise Unauthorized('user is not authorized')
            settings.operator = decoded
            response = await call_next(request)
            return response
    for record in API(graph).records:
        fastapi_url = sub(r':([^/]+)', '{\\1}', record.url)
        if record.kind == 'L':
            _install_l(record, app, fastapi_url)
        elif record.kind == 'E':
            _install_e(record, app, fastapi_url)
        elif record.kind == 'R':
            _install_r(record, app, fastapi_url)
        elif record.kind == 'C':
            _install_c(record, app, fastapi_url)
        elif record.kind == 'U':
            _install_u(record, app, fastapi_url)
        elif record.kind == 'D':
            _install_d(record, app, fastapi_url)
        elif record.kind == 'S':
            _install_s(record, app, fastapi_url)
    return app


def _install_l(record: APIRecord, app: 'FastAPI', url: str) -> None:
    from fastapi import Request
    lcallback = record.callback
    @app.get(url)
    def list_all(request: Request):
        params = str(request._query_params)
        ctx = ACtx(qs=params if params else None)
        [_, result] = lcallback(ctx)
        return Response(media_type="application/json", content=dumps(result, cls=JSONEncoder))

def _install_e(record: APIRecord, app: 'FastAPI', url: str) -> None:
    from fastapi import Request
    ecallback = record.callback
    @app.post(url)
    async def ensure(request: Request):
        ctx = ACtx(body=(await request.form() or await request.json()))
        [_, result] = ecallback(ctx)
        return Response(media_type="application/json", content=dumps(result, cls=JSONEncoder))


def _install_r(record: APIRecord, app: 'FastAPI', url: str) -> None:
    from fastapi import Request
    rcallback = record.callback
    @app.get(url)
    def read_by_id(id: Any):
        ctx = ACtx(id=id)
        [_, result] = rcallback(ctx)
        [_, result] = rcallback(ctx)
        return Response(media_type="application/json", content=dumps(result, cls=JSONEncoder))

def _install_c(record: APIRecord, app: 'FastAPI', url: str) -> None:
    from fastapi import Request
    ccallback = record.callback
    @app.post(url)
    async def create(request: Request):
        ctx = ACtx(body=(await request.form() or await request.json()))
        [_, result] = ccallback(ctx)
        return Response(media_type="application/json", content=dumps(result, cls=JSONEncoder))

def _install_u(record: APIRecord, app: 'FastAPI', url: str) -> None:
    from fastapi import Request
    ucallback = record.callback
    @app.patch(url)
    async def update(id: Any, request: Request):
        ctx = ACtx(id=id, body=(await request.json()))
        [_, result] = ucallback(ctx)
        return Response(media_type="application/json", content=dumps(result, cls=JSONEncoder))

def _install_d(record: APIRecord, app: 'FastAPI', url: str) -> None:
    dcallback = record.callback
    @app.delete(url, status_code=204)
    def delete(id: Any) -> None:
        ctx = ACtx(id=id)
        dcallback(ctx)

def _install_s(record: APIRecord, app: 'FastAPI', url: str) -> None:
    from fastapi import Request
    scallback = record.callback
    @app.post(url)
    async def create_session(request: Request):
        ctx = ACtx(body=(await request.form() or await request.json()))
        [_, result] = scallback(ctx)
        return Response(media_type="application/json", content=dumps(result, cls=JSONEncoder))
