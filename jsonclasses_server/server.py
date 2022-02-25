from __future__ import annotations
from traceback import print_exception
from thunderlight import Ctx, Next, App, gimme, use
from jsonclasses.uconf import uconf
from jsonclasses.excs import (ObjectNotFoundException,
                              ValidationException,
                              UniqueConstraintException,
                              UnauthorizedActionException)
from .excs import AuthenticationException
from .jwt_token import decode_jwt_token
from jwt import DecodeError


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
        print_exception(type[e], value=e, tb=e.__traceback__)
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
async def handle_cors_headers_middleware(ctx: Ctx, next: Next) -> None:
    res = ctx.res
    cors = uconf().get('cors') or {}
    if ctx.req.method == 'OPTIONS': # handle cors options
        res.code = 204
        res.headers['Access-Control-Allow-Origin'] = cors.get('allowOrigin') or '*'
        res.headers['Access-Control-Allow-Methods'] = cors.get('allowMethods') or 'OPTIONS, POST, GET, PATCH, DELETE'
        res.headers['Access-Control-Allow-Headers'] = cors.get('allowHeaders') or '*'
        res.headers['Access-Control-Max-Age'] = cors.get('maxAge') or '86400'
        res.empty()
        return
    res.headers['Access-Control-Allow-Origin'] = cors.get('allowOrigin') or '*'
    await next(ctx)


@use
async def set_operator_middleware(ctx: Ctx, next: Next) -> None:
    if 'authorization' not in ctx.req.headers:
        ctx.state.operator = None
        await next(ctx)
    else:
        authorization = ctx.req.headers['authorization']
        token = authorization[7:]
        try:
            decoded = decode_jwt_token(token)
            ctx.state.operator = decoded
        except DecodeError:
            ctx.state.operator = None
            content = _error_content('Unauthorized', 'authorization token is invalid')
            ctx.res.code = 401
            ctx.res.json(content)
        except ObjectNotFoundException:
            ctx.state.operator = None
            content = _error_content('Unauthorized', 'user is not authorized')
            ctx.res.code = 401
            ctx.res.json(content)
        await next(ctx)


def server() -> App:
    return gimme()
