from __future__ import annotations
from typing import Any
from thunderlight import Ctx, Next, app, use, get, post, patch, delete
from jsonclasses.uconf import uconf
from jsonclasses.excs import (ObjectNotFoundException,
                              ValidationException,
                              UniqueConstraintException,
                              UnauthorizedActionException)
from .actx import ACtx
from .api_class import API
from .api_record import APIRecord
from .excs import AuthenticationException
from .jwt_token import check_jwt_installed, decode_jwt_token


def create_server(graph: str = 'default') -> Any:

    cors = uconf().get('cors') or {}

    def _error_content(type: str, msg: str) -> dict[str, str]:
        return {
            'error': {
                'type': type,
                'message': msg
            }
        }

    @use
    async def error_handler(ctx: Ctx, next: Next) -> None:
        try:
            await next(ctx)
        except Exception as e:
            code = 500
            code = 404 if isinstance(e, ObjectNotFoundException) else code
            code = 400 if isinstance(e, ValidationException) else code
            code = 400 if isinstance(e, UniqueConstraintException) else code
            code = 401 if isinstance(e, UnauthorizedActionException) else code
            code = 400 if isinstance(e, AuthenticationException) else code
            if code == 500:
                content = _error_content('Internal Server Error', 'There is an internal server error.')
            content = _error_content(e.__class__.__name__, str(e))
            if isinstance(e, ValidationException) or isinstance(e, UniqueConstraintException):
                content['error']['fields'] = e.keypath_messages
            ctx.res.code = code
            ctx.res.json(content)

    @use
    async def handle_cors_headers_middleware(ctx: Ctx, _: Next) -> None:
        res = ctx.res
        if ctx.req.method == 'OPTIONS': # handle cors options
            res.code = 204
            res.headers = {
                'Access-Control-Allow-Origin': cors.get('allowOrigin') or '*',
                'Access-Control-Allow-Methods': cors.get('allowMethods') or 'OPTIONS, POST, GET, PATCH, DELETE',
                'Access-Control-Allow-Headers': cors.get('allowHeaders') or '*',
                'Access-Control-Max-Age': cors.get('maxAge') or '86400'
            }
            res.empty()

    @use
    async def set_operator_middleware(ctx: Ctx, next: Next) -> None:
        check_jwt_installed()
        from jwt import DecodeError
        req = ctx.req
        if 'authorization' not in ctx.req.headers:
            ctx.state.operator = None
            await next(ctx)
        else:
            authorization = req.headers['authorization']
            token = authorization[7:]
            try:
                decoded = decode_jwt_token(token, graph)
                ctx.state.operator = decoded
            except DecodeError:
                content = _error_content('Unauthorized', 'authorization token is invalid')
                ctx.res.code = 401
                ctx.res.json(content)
            except ObjectNotFoundException:
                content = _error_content('Unauthorized', 'user is not authorized')
                ctx.res.code = 401
                ctx.res.json(content)
            await next(ctx)


    def _install_l(record: APIRecord, url: str) -> None:
        @get(url)
        async def list_all(ctx: Ctx):
            lcallback = record.callback
            actx = ACtx(qs=ctx.req.qs, operator=ctx.state.operator)
            [_, result] = lcallback(actx)
            ctx.res.json({"data": [r for r in result]})

    def _install_r(record: APIRecord, url: str) -> None:
        rcallback = record.callback
        @get(url)
        async def read_by_id(ctx: Ctx):
            id = ctx.req.args.get('id')
            actx = ACtx(id=id, qs=ctx.req.qs, operator=ctx.state.operator)
            [_, result] = rcallback(actx)
            ctx.res.json({"data": result})

    def _install_c(record: APIRecord, url: str) -> None:
        ccallback = record.callback
        @post(url)
        async def create(ctx: Ctx):
            actx = ACtx(body=(await ctx.req.dict()),
                    qs=ctx.req.qs,
                    operator=ctx.state.operator)
            [_, result] = ccallback(actx)
            ctx.res.json({"data": result})

    def _install_u(record: APIRecord, url: str) -> None:
        ucallback = record.callback
        @patch(url)
        async def update(ctx: Ctx):
            id = ctx.req.args.get('id')
            actx = ACtx(id=id, body=(await ctx.req.dict()),
                    qs=ctx.req.qs,
                    operator=ctx.state.operator)
            [_, result] = ucallback(actx)
            ctx.res.json({"data": result})

    def _install_d(record: APIRecord, url: str) -> None:
        dcallback = record.callback
        @delete(url)
        def delete_by_id(ctx: Ctx) -> None:
            id = ctx.req.args.get('id')
            actx = ACtx(id=id, operator=ctx.state.operator)
            ctx.res.code = 204
            dcallback(actx)

    def _install_s(record: APIRecord, url: str) -> None:
        scallback = record.callback
        @post(url)
        async def create_session(ctx: Ctx):
            actx = ACtx(body=(await ctx.req.dict()))
            [_, result] = scallback(actx)
            ctx.res.json({"data": result})

    def _install_e(record: APIRecord, url: str) -> None:
        ecallback = record.callback
        @post(url)
        async def ensure(ctx: Ctx):
            actx = ACtx(body=(await ctx.req.dict()))
            [_, result] = ecallback(actx)
            ctx.res.json({"data": result})


    for record in API(graph).records:
        if record.kind == 'L':
            _install_l(record, record.url)
        elif record.kind == 'E':
            _install_e(record, record.url)
        elif record.kind == 'R':
            _install_r(record, record.url)
        elif record.kind == 'C':
            _install_c(record, record.url)
        elif record.kind == 'U':
            _install_u(record, record.url)
        elif record.kind == 'D':
            _install_d(record, record.url)
        elif record.kind == 'S':
            _install_s(record, record.url)
    return app
