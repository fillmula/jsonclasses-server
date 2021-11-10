from typing import Any, Optional
from re import sub
from os import getcwd, path
from json import dumps
from jsonclasses.json_encoder import JSONEncoder
from traceback import extract_tb, print_exception
from jsonclasses.user_conf import user_conf
from .excs import AuthenticationException
from jsonclasses.excs import ObjectNotFoundException
from jsonclasses.pkgutils import check_and_install_packages
from .jwt_token import check_jwt_installed, decode_jwt_token
from .api_class import API
from .actx import ACtx
from .api_record import APIRecord


def check_fastapi_installed() -> None:
    packages = {'fastapi': ('fastapi', '>=0.70.0,<0.71.0')}
    check_and_install_packages(packages)


def _remove_none(obj: dict) -> dict:
    return {k: v for k, v in obj.items() if v is not None}


def create_fastapi_server(graph: str = 'default') -> Any:
    check_fastapi_installed()
    from fastapi import FastAPI, Request, Response
    from fastapi.responses import JSONResponse
    from starlette.exceptions import HTTPException as StarletteHTTPException

    app = FastAPI()
    conf = user_conf()
    cors = conf.get('cors') or {}

    def _exception_handler(request: Request, exception: Exception) -> Response:
        if app.debug == True:
            if isinstance(exception, WrappedException):
                exc = exception.exc
                if exception.status_code == 500:
                    print_exception(type[exc], value=exc, tb=exc.__traceback__)
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
                    return JSONResponse(content=dumps(message, cls=JSONEncoder).encode('utf-8'), status_code=exception.status_code)
                else:
                    message = {
                        'error': _remove_none({
                            'type': exc.__class__.__name__,
                            'message': str(exc),
                            'fields': (exc.keypath_messages
                                    if (isinstance(exc, ValidationException) or isinstance(exc, UniqueConstraintException))
                                    else None),
                            'traceback': [f'file {path.relpath(f.filename, getcwd())}:{f.lineno} in {f.name}' for f in extract_tb(exception.__traceback__)],  # noqa: E501
                        })
                    }
                    return JSONResponse(content=dumps(message, cls=JSONEncoder).encode('utf-8'), status_code=exception.status_code)
            else:
                print_exception(type[exception], value=exception, tb=exception.__traceback__)
                message = {
                    'error': _remove_none({
                        'type': exception.__class__.__name__,
                        'message': exception.detail,
                        'traceback': [f'file {path.relpath(f.filename, getcwd())}:{f.lineno} in {f.name}' for f in extract_tb(exception.__traceback__)],  # noqa: E501
                    })
                }
                return JSONResponse(
                    content=dumps(message, cls=JSONEncoder).encode('utf-8'),
                    status_code=exception.status_code)
        else:
            if isinstance(exception, WrappedException):
                exc = exception.exc
                if exception.status_code == 500:
                    print_exception(type[exc], value=exc, tb=exc.__traceback__)
                    message = {
                        'error': _remove_none({
                            'type': 'Internal Server Error',
                            'message': 'There is an internal server error.'
                        })
                    }
                    print("HERE1 message", message)
                    return JSONResponse(
                        content=dumps(message, cls=JSONEncoder).encode('utf-8'),
                        status_code=exception.status_code)
                else:
                    message = {
                        'error': _remove_none({
                            'type': exc.__class__.__name__,
                            'message': str(exc),
                            'fields': (exc.keypath_messages
                                    if (isinstance(exc, ValidationException) or isinstance(exc, UniqueConstraintException))
                                    else None)
                        })
                    }
                    print("HERE2 message", message)
                    return JSONResponse(
                        content=dumps(message, cls=JSONEncoder).encode('utf-8'),
                        status_code=exception.status_code)
            else:
                print_exception(type[exception], value=exception, tb=exception.__traceback__)
                message = {
                    'error': _remove_none({
                        'type': exception.__class__.__name__,
                        'message': exception.detail
                    })
                }
                return JSONResponse(
                    content=dumps(message, cls=JSONEncoder).encode('utf-8'),
                    status_code=exception.status_code)

    from jsonclasses.excs import (ValidationException,
                                  UniqueConstraintException,
                                  UnauthorizedActionException)

    class WrappedException(StarletteHTTPException):
        def __init__(self, exc: Exception) -> None:
            from fastapi import HTTPException
            code = exc.status_code if isinstance(exc, HTTPException) else 500
            code = 404 if isinstance(exc, ObjectNotFoundException) else code
            code = 400 if isinstance(exc, ValidationException) else code
            code = 400 if isinstance(exc, UniqueConstraintException) else code
            code = 401 if isinstance(exc, UnauthorizedActionException) else code
            code = 400 if isinstance(exc, AuthenticationException) else code
            super().__init__(status_code=code, detail=str(exc))
            self.exc = exc

    async def omni_catch_middleware(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            # you probably want some kind of logging here
            return JSONResponse(content={
                "error": {
                    "type": "Works",
                    "message": "OK"
                }
            }, status_code=500)

    async def set_operator_middleware(request, call_next):
        check_jwt_installed()
        from fastapi.exceptions import HTTPException
        from jwt import DecodeError
        if 'authorization' not in request.headers:
            request.state.operator = None
            response = await call_next(request)
            return response
        authorization = request.headers['authorization']
        token = authorization[7:]
        try:
            decoded = decode_jwt_token(token, graph)
        except DecodeError:
            raise WrappedException(HTTPException(401, 'authorization token is invalid'))
        except ObjectNotFoundException:
            raise WrappedException(HTTPException(401, 'user is not authorized'))
        request.state.operator = decoded
        response = await call_next(request)
        return response

    async def handle_cors_headers_middleware(request, call_next):
        if request.method == 'OPTIONS':
            return Response(status_code=204, headers={
                'Access-Control-Allow-Origin': cors.get('allowOrigin') or '*',
                'Access-Control-Allow-Methods': cors.get('allowMethods') or 'OPTIONS, POST, GET, PATCH, DELETE',
                'Access-Control-Allow-Headers': cors.get('allowHeaders') or '*',
                'Access-Control-Max-Age': cors.get('maxAge') or '86400'
            })
        else:
            res = await call_next(request)
            res.headers['Access-Control-Allow-Origin'] = cors.get('allowOrigin') or '*'
            return res

    def _install_l(record: APIRecord, app: 'FastAPI', url: str) -> None:
        from fastapi import Request
        lcallback = record.callback
        @app.get(url)
        def list_all(request: Request):
            ctx = ACtx(qs=request.scope.get("query_string", bytes()).decode("utf-8"), operator=request.state.operator)
            try:
                [_, result] = lcallback(ctx)
                return Response(media_type="application/json", content=dumps(result, cls=JSONEncoder).encode('utf-8'))
            except Exception as e:
                raise WrappedException(e)

    def _install_r(record: APIRecord, app: 'FastAPI', url: str) -> None:
        from fastapi import Request
        rcallback = record.callback
        @app.get(url)
        def read_by_id(id: Any, request: Request):
            ctx = ACtx(id=id, qs=request.scope.get("query_string", bytes()).decode("utf-8"), operator=request.state.operator)
            try:
                [_, result] = rcallback(ctx)
                return Response(media_type="application/json", content=dumps(result, cls=JSONEncoder).encode('utf-8'))
            except Exception as e:
                raise WrappedException(e)

    def _install_c(record: APIRecord, app: 'FastAPI', url: str) -> None:
        from fastapi import Request
        ccallback = record.callback
        @app.post(url)
        async def create(request: Request):
            ctx = ACtx(body=(await request.form() or await request.json()),
                    qs=request.scope.get("query_string", bytes()).decode("utf-8"),
                    operator=request.state.operator)
            try:
                [_, result] = ccallback(ctx)
                return Response(media_type="application/json", content=dumps(result, cls=JSONEncoder).encode('utf-8'))
            except Exception as e:
                raise WrappedException(e)

    def _install_u(record: APIRecord, app: 'FastAPI', url: str) -> None:
        from fastapi import Request
        ucallback = record.callback
        @app.patch(url)
        async def update(id: Any, request: Request):
            ctx = ACtx(id=id, body=(await request.form() or await request.json()),
                       qs=request.scope.get("query_string", bytes()).decode("utf-8"),
                       operator=request.state.operator)
            try:
                [_, result] = ucallback(ctx)
                return Response(media_type="application/json", content=dumps(result, cls=JSONEncoder).encode('utf-8'))
            except Exception as e:
                raise WrappedException(e)

    def _install_d(record: APIRecord, app: 'FastAPI', url: str) -> None:
        dcallback = record.callback
        @app.delete(url, status_code=204)
        def delete(id: Any, request: Request) -> None:
            ctx = ACtx(id=id, operator=request.state.operator)
            try:
                dcallback(ctx)
            except Exception as e:
                raise WrappedException(e)

    def _install_s(record: APIRecord, app: 'FastAPI', url: str) -> None:
        from fastapi import Request
        scallback = record.callback
        @app.post(url)
        async def create_session(request: Request):
            ctx = ACtx(body=(await request.form() or await request.json()))
            try:
                [_, result] = scallback(ctx)
                return Response(media_type="application/json", content=dumps(result, cls=JSONEncoder).encode('utf-8'))
            except Exception as e:
                raise WrappedException(e)

    def _install_e(record: APIRecord, app: 'FastAPI', url: str) -> None:
        from fastapi import Request
        ecallback = record.callback
        @app.post(url)
        async def ensure(request: Request):
            ctx = ACtx(body=(await request.form() or await request.json()))
            try:
                [_, result] = ecallback(ctx)
                return Response(media_type="application/json", content=dumps(result, cls=JSONEncoder).encode('utf-8'))
            except Exception as e:
                raise WrappedException(e)

    app.middleware('http')(set_operator_middleware)
    app.middleware('http')(handle_cors_headers_middleware)
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
    app.middleware('http')(omni_catch_middleware)
    return app
