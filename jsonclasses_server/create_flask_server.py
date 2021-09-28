from __future__ import annotations
from typing import Any, TYPE_CHECKING
from re import sub
from .api_class import API
from .actx import ACtx
from .api_record import APIRecord
if TYPE_CHECKING:
    from flask import Flask, Blueprint


def try_import_flask():
    try:
        from flask import Flask
    except ModuleNotFoundError:
        raise 'please install flask in order to use create_flask_server'


def create_flask_server(graph: str = 'default') -> Flask:
    try_import_flask()
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
