from __future__ import annotations
from typing import Any, TYPE_CHECKING
from .api_class import API
from .actx import ACtx
if TYPE_CHECKING:
    from flask import Flask


def try_import_flask():
    try:
        from flask import Flask
    except ModuleNotFoundError:
        raise 'please install flask in order to use create_flask_server'


def create_flask_server(graph: str = 'default') -> Flask:
    try_import_flask()
    from flask import request, g, jsonify, make_response
    app = Flask('app')
    app.url_map.strict_slashes = False
    for record in API(graph).records:
        if record.kind == 'L':
            def list_all():
                ctx = ACtx(qs=str(request.query_string))
                [_, result] = record.callback(ctx)
                return jsonify(data=result)
            app.route(record.url, methods=[record.method])(list_all)
        elif record.kind == 'R':
            def read_by_id(id: Any):
                ctx = ACtx(id=id)
                [_, result] = record.callback(ctx)
                return jsonify(date=result)
            app.route(record.url, methods=[record.method])(read_by_id)
        elif record.kind == 'C':
            def create():
                ctx = ACtx(body=(request.form | request.files or request.json))
                [_, result] = record.callback(ctx)
                return jsonify(date=result)
            app.route(record.url, methods=[record.method])(create)
        elif record.kind == 'U':
            def update(id: Any):
                ctx = ACtx(id=id, body=((request.form | request.files) or request.json))
                [_, result] = record.callback(ctx)
                return jsonify(date=result)
            app.route(record.url, methods=[record.method])(update)
        elif record.kind == 'D':
            def delete(id: Any):
                ctx = ACtx(id=id)
                record.callback(ctx)
                return make_response('', 204)
            app.route(record.url, methods=[record.method])(delete)
    return app
