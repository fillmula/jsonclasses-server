from __future__ import annotations
from jsonclasses_server.auth_conf import AuthConf
from typing import ClassVar, Any, cast
from qsparser import stringify
from jsonclasses.ctx import Ctx as JCtx
from thunderlight import Ctx, get, post, patch, delete
from .api_object import APIObject
from .aconf import AConf
from .jwt_token import encode_jwt_token
from .nameutils import (
    cname_to_pname, cname_to_srname, fname_to_pname, pname_to_cname,
    pname_to_fname
)
from .excs import AuthenticationException


class API:

    _graph_map: dict[str, API] = {}
    _initialized_map: dict[str, bool] = {}

    def __new__(cls: type[API], graph_name: str) -> API:
        if not cls._graph_map.get(graph_name):
            cls._graph_map[graph_name] = super(API, cls).__new__(cls)
        return cls._graph_map[graph_name]

    def __init__(self: API, graph_name: str) -> None:
        if self.__class__._initialized_map.get(graph_name):
            return
        self._graph_name: str = graph_name
        self._default_aconf = AConf(
            cls=None,
            name=None,
            enable='CRUDL',
            disable=None,
            cname_to_pname=cname_to_pname,
            fname_to_pname=fname_to_pname,
            pname_to_cname=pname_to_cname,
            pname_to_fname=pname_to_fname,
            cname_to_srname=cname_to_srname)
        self.__class__._initialized_map[graph_name] = True
        return None

    default: ClassVar[API]

    @property
    def aconf(self: API) -> AConf:
        """The default API configuration for all classes on this graph."""
        return self._default_aconf

    def record_auth(self: API, cls: type[APIObject], auth_conf: AuthConf) -> None:
        aconf = cls.aconf
        auth_conf: AuthConf = cls.auth_conf
        basename = aconf.name or aconf.cname_to_pname(cls.__name__)
        url = f'/{basename}/session'
        ai_fields = cls.cdef._auth_identity_fields
        ai_names = [f.name for f in ai_fields]
        ai_json_names = [f.json_name for f in ai_fields]
        ai_valid_names = set(ai_names + ai_json_names)
        ab_fields = cls.cdef._auth_by_fields
        ab_names = [f.name for f in ab_fields]
        ab_json_names = [f.json_name for f in ab_fields]
        ab_valid_names = set(ab_names + ab_json_names)
        auth_conf.info._identities = ai_names
        auth_conf.info._bys = ab_names
        srname = aconf.cname_to_srname(cls.__name__)
        auth_conf.info._srname = srname
        @post(url)
        async def create_session(ctx: Ctx):
            body = cast(dict[str, Any], ctx.req.json)
            ai_set = set(body.keys()).intersection(ai_valid_names)
            len_ai_set = len(ai_set)
            if len_ai_set < 1:
                raise AuthenticationException('no identity provided')
            if len_ai_set > 1:
                raise AuthenticationException('multiple identities provided')
            ab_set = set(body.keys()).intersection(ab_valid_names)
            len_ab_set = len(ab_set)
            if len_ab_set < 1:
                raise AuthenticationException('no authentication provided')
            if len_ab_set > 1:
                raise AuthenticationException('multiple authentications provided')
            u_ai_name = ai_set.pop()
            u_ab_name = ab_set.pop()
            ai_value = body[u_ai_name]
            ab_value = body[u_ab_name]
            ai_name = cls.cdef.jconf.input_key_strategy(u_ai_name)
            ab_name = cls.cdef.jconf.input_key_strategy(u_ab_name)
            obj = cls.one(**{ai_name: ai_value}).optional.exec()
            if obj is None:
                raise AuthenticationException('authorizable unit not found')
            checker = cls.cdef.field_named(ab_name).fdef.auth_by_checker
            jctx = JCtx.rootctxp(obj, ab_name, getattr(obj, ab_name), ab_value)
            newval = checker.modifier.transform(jctx)
            jctx = JCtx.rootctxp(obj, ab_name, newval, ab_value)
            checker.modifier.validate(jctx)
            token = encode_jwt_token(obj, auth_conf.expires_in)
            srname = auth_conf.info.srname
            json_obj = obj.opby(obj).tojson()
            if ctx.req.query != '':
                json_obj = cls.id(obj._id, ctx.req.query).exec().opby(obj).tojson()
            result = {'token': token, srname: json_obj}
            ctx.res.json({"data": result})

    def record(self: API, cls: type[APIObject], aconf: AConf) -> None:
        name = aconf.name or aconf.cname_to_pname(cls.__name__)
        url = f'/{name}'
        id_url = f'{url}/:id'
        e_url = f'{url}/ensure'
        if 'L' in aconf.actions:
            self.record_l(cls, url)
        if 'E' in aconf.actions:
            self.record_e(cls, e_url)
        if 'R' in aconf.actions:
            self.record_r(cls, id_url)
        if 'C' in aconf.actions:
            self.record_c(cls, url)
        if 'U' in aconf.actions:
            self.record_u(cls, id_url)
            self.record_um(cls, url)
        if 'D' in aconf.actions:
            self.record_d(cls, id_url)
            self.record_dm(cls, url)

    def record_l(self: API, cls: type[APIObject], url: str) -> None:
        @get(url)
        async def list_all(ctx: Ctx):
            result = cls.find(ctx.req.query).exec()
            filtered = []
            for item in result:
                try:
                    filtered.append(item.opby(ctx.state.operator).tojson())
                except Exception as e:
                    continue
            ctx.res.json({ 'data': filtered })

    def record_r(self: API, cls: type[APIObject], url: str) -> None:
        @get(url)
        async def read_by_id(ctx: Ctx):
            id = ctx.req.args.get('id')
            result = cls.id(id, ctx.req.query).exec().opby(ctx.state.operator)
            ctx.res.json({'data': result.tojson()})

    def record_c(self: API, cls: type[APIObject], url: str) -> None:
        @post(url)
        async def create(ctx: Ctx):
            resource = ctx.req.json
            url_qs = ctx.req.query
            upsert: dict[str, Any] = resource.get('_upsert')
            create = resource.get('_create')
            if upsert and create is None:
                query = stringify(upsert.get('_query'))
                qs = query if url_qs == '' else f'{query}&{url_qs}'
                input_data = upsert.get('_data')
                if input_data is not None:
                    result = cls.one(qs).optional.exec()
                    if result:
                        result.opby(ctx.state.operator).set(**input_data).save()
                    else:
                        result = cls(**input_data).opby(ctx.state.operator).save()
                    ctx.res.json({"data": result.tojson()})
            elif create and upsert is None:
                if isinstance(create, list):
                    result: list[dict[str, Any]] = []
                    for i in create:
                        i_result = cls(**(i or {})).opby(ctx.state.operator).save()
                        if url_qs != '':
                            i_result = cls.id(i_result._id, url_qs).exec().opby(ctx.state.operator)
                        result.append(i_result.tojson())
                    ctx.res.json({"data": result})
                elif isinstance(create, dict):
                    data = create.get('_data')
                    result = cls(**(data or {})).opby(ctx.state.operator).save()
                    if url_qs != '':
                        result = cls.id(result._id, url_qs).exec().opby(ctx.state.operator)
                    ctx.res.json({"data": result.tojson()})
            else:
                result = cls(**(resource or {})).opby(ctx.state.operator).save()
                if url_qs != '':
                    result = cls.id(result._id, url_qs).exec().opby(ctx.state.operator)
                ctx.res.json({"data": result.tojson()})

    def record_u(self: API, cls: type[APIObject], url: str) -> None:
        @patch(url)
        async def update_one(ctx: Ctx):
            id = ctx.req.args.get('id')
            body = ctx.req.json
            result = cls.id(id, ctx.req.query).exec().opby(ctx.state.operator).set(**(body or {})).save()
            ctx.res.json({'data': result.tojson()})


    def record_um(self: API, cls: type[APIObject], url: str) -> None:
        @patch(url)
        async def update_many(ctx: Ctx):
            resource = ctx.req.json
            update = resource.get('_update')
            uq = stringify(update['_query'])
            qs = uq if ctx.req.query == '' else f'{uq}&{ctx.req.query}'
            result = cls.find(qs).exec()
            updated = []
            for item in result:
                updated.append(item.opby(ctx.state.operator).set(**(update['_data'] or {})).save().tojson())
            ctx.res.json({'data': updated})

    def record_d(self: API, cls: type[APIObject], url: str) -> None:
        @delete(url)
        async def delete_by_id(ctx: Ctx) -> None:
            id = ctx.req.args.get('id')
            cls.id(id).exec().opby(ctx.state.operator).delete()
            ctx.res.empty()

    def record_dm(self: API, cls: type[APIObject], url: str) -> None:
        @delete(url)
        async def delete_by_id(ctx: Ctx) -> None:
            result = cls.find(ctx.req.query).exec()
            for item in result:
                item.opby(ctx.state.operator).delete()
            ctx.res.empty()

    def record_e(self: API, cls: type[APIObject], url: str) -> None:
        @post(url)
        async def e(ctx: Ctx) -> Any:
            body = ctx.req.json
            ufields = cls.cdef._unique_fields
            unames = [f.name for f in ufields]
            ujsonnames = [f.json_name for f in ufields]
            uvalidnames = set(unames + ujsonnames)
            matcher: dict[str, Any] = {}
            updater: dict[str, Any] = {}
            for k, v in await body.items():
                if k in uvalidnames:
                    if body[k] is not None:
                        matcher[k] = v
                else:
                    updater[k] = v
            result = cls.one(matcher).optional.exec()
            if result:
                result.opby(ctx.state.operator).set(**updater).save()
            else:
                result = cls(**body).opby(ctx.state.operator).save()
            ctx.res.json({'data': result.tojson()})


API.default = API('default')
