from typing import Any
from re import sub
from json import dumps
from jsonclasses.json_encoder import JSONEncoder
from jsonclasses.user_conf import user_conf
from jsonclasses.excs import (
    ObjectNotFoundException, ValidationException, UniqueConstraintException,
    UnauthorizedActionException
)
from jsonclasses.pkgutils import check_and_install_packages
from .jwt_token import check_jwt_installed, decode_jwt_token
from .api_class import API
from .actx import ACtx
from .api_record import APIRecord
from .excs import AuthenticationException


def check_fastapi_installed() -> None:
    packages = {'fastapi': ('fastapi', '>=0.70.0,<0.71.0')}
    check_and_install_packages(packages)


def create_fastapi_server(graph: str = 'default') -> Any:
    check_fastapi_installed()
    from fastapi import FastAPI, Request, Response
    from fastapi.responses import JSONResponse
    from starlette.exceptions import HTTPException as StarletteHTTPException

    app = FastAPI()
    conf = user_conf()
    cors = conf.get('cors') or {}

    def error(code: int, type: str, msg: str):
        return JSONResponse(content={
            'error': {
                'type': type,
                'message': msg
            }
        }, status_code=code)

    def jcerror(exception: Exception) -> Response:
        from fastapi.exceptions import HTTPException
        code = exception.status_code if isinstance(exception, HTTPException) else 500
        code = 404 if isinstance(exception, ObjectNotFoundException) else code
        code = 400 if isinstance(exception, ValidationException) else code
        code = 400 if isinstance(exception, UniqueConstraintException) else code
        code = 401 if isinstance(exception, UnauthorizedActionException) else code
        code = 400 if isinstance(exception, AuthenticationException) else code
        if code == 500:
            return JSONResponse(
                content={
                    'error': {
                        'type': 'Internal Server Error',
                        'message': 'There is an internal server error.'
                    }
                },
                status_code=500
            )
        message = {
            'error': {
                'type': exception.__class__.__name__,
                'message': str(exception)
            }
        }
        if isinstance(exception, ValidationException) or isinstance(exception, UniqueConstraintException):
            message['error']['fields'] = exception.keypath_messages
        return JSONResponse(status_code=code, content=message)

    async def set_operator_middleware(request, call_next):
        check_jwt_installed()
        from fastapi.exceptions import HTTPException
        from jwt import DecodeError
        if 'authorization' not in request.headers:
            request.state.operator = None
            return await call_next(request)
        authorization = request.headers['authorization']
        token = authorization[7:]
        try:
            decoded = decode_jwt_token(token, graph)
        except DecodeError:
            return error(401, 'Unauthorized', 'authorization token is invalid')
        except ObjectNotFoundException:
            return error(401, 'Unauthorized', 'user is not authorized')
        request.state.operator = decoded
        return await call_next(request)

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
                return JSONResponse(content={"data": [r.tojson() for r in result]})
            except Exception as e:
                return jcerror(e)

    def _install_r(record: APIRecord, app: 'FastAPI', url: str) -> None:
        from fastapi import Request
        rcallback = record.callback
        @app.get(url)
        def read_by_id(id: Any, request: Request):
            ctx = ACtx(id=id, qs=request.scope.get("query_string", bytes()).decode("utf-8"), operator=request.state.operator)
            try:
                [_, result] = rcallback(ctx)
                return JSONResponse(content={"data": result.tojson()})
            except Exception as e:
                return jcerror(e)

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
                return JSONResponse(content={"data": result.tojson()})
            except Exception as e:
                return jcerror(e)

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
                return JSONResponse(content={"data": result.tojson()})
            except Exception as e:
                return jcerror(e)

    def _install_d(record: APIRecord, app: 'FastAPI', url: str) -> None:
        dcallback = record.callback
        @app.delete(url, status_code=204)
        def delete(id: Any, request: Request) -> None:
            ctx = ACtx(id=id, operator=request.state.operator)
            try:
                dcallback(ctx)
            except Exception as e:
                return jcerror(e)

    def _install_s(record: APIRecord, app: 'FastAPI', url: str) -> None:
        from fastapi import Request
        scallback = record.callback
        @app.post(url)
        async def create_session(request: Request):
            ctx = ACtx(body=(await request.form() or await request.json()))
            try:
                [_, result] = scallback(ctx)
                return Response(media_type="application/json", content=dumps({"data": result}, cls=JSONEncoder).encode('utf-8'))
            except Exception as e:
                return jcerror(e)

    def _install_e(record: APIRecord, app: 'FastAPI', url: str) -> None:
        from fastapi import Request
        ecallback = record.callback
        @app.post(url)
        async def ensure(request: Request):
            ctx = ACtx(body=(await request.form() or await request.json()))
            try:
                [_, result] = ecallback(ctx)
                return JSONResponse(content={"data": result.tojson()})
            except Exception as e:
                return jcerror(e)

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
    return app
