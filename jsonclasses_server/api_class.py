from __future__ import annotations
from jsonclasses_server.auth_conf import AuthConf
from typing import ClassVar, Tuple, Any, cast
from jsonclasses.ctx import Ctx
from .api_object import APIObject
from .aconf import AConf
from .api_record import APIRecord
from .actx import ACtx
from .encode_jwt_token import encode_jwt_token
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
        self._records: list[APIRecord] = []
        self.__class__._initialized_map[graph_name] = True
        return None

    default: ClassVar[API]

    @property
    def aconf(self: API) -> AConf:
        """The default API configuration for all classes on this graph."""
        return self._default_aconf

    def record_auth(self: API, cls: type[APIObject], auth_conf: AuthConf) -> None:
        aconf = cls.aconf
        basename = aconf.name or aconf.cname_to_pname(cls.__name__)
        name = f'/{basename}/session'
        ai_fields = cls.cdef._auth_identity_fields
        ai_names = [f.name for f in ai_fields]
        ai_json_names = [f.json_name for f in ai_fields]
        ai_valid_names = set(ai_names + ai_json_names)
        ab_fields = cls.cdef._auth_by_fields
        ab_names = [f.name for f in ab_fields]
        ab_json_names = [f.json_name for f in ab_fields]
        ab_valid_names = set(ab_names + ab_json_names)
        def auth(actx: ACtx) -> Tuple[int, Any]:
            body = cast(dict[str, Any], actx.body)
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
            ai_name = cls.cdef.jconf.key_decoding_strategy(u_ai_name)
            ab_name = cls.cdef.jconf.key_decoding_strategy(u_ab_name)
            obj = cls.one(**{ai_name: ai_value}).optional.exec()
            if obj is None:
                raise AuthenticationException('authorizable unit not found')
            checker = cls.cdef.field_named(ab_name).fdef.auth_by_checker
            ctx = Ctx.rootctxp(obj, ab_name, getattr(obj, ab_name), ab_value)
            newval = checker.modifier.transform(ctx)
            ctx = Ctx.rootctxp(obj, ab_name, newval, ab_value)
            checker.modifier.validate(ctx)
            token = encode_jwt_token(obj, auth_conf.expires_in)
            srname = aconf.cname_to_srname(cls.__name__)
            return (200, {'token': token, srname: obj})
        self._records.insert(0, APIRecord(f's_{name}', 'S', 'POST', name, auth))

    def record(self: API, cls: type[APIObject], aconf: AConf) -> None:
        name = aconf.name or aconf.cname_to_pname(cls.__name__)
        gname = f'/{name}'
        sname = f'{gname}/:id'
        ename = f'{gname}/ensure'
        if 'L' in aconf.actions:
            self.record_l(cls, aconf, name, gname, sname)
        if 'E' in aconf.actions:
            self.record_e(cls, name, ename)
        if 'R' in aconf.actions:
            self.record_r(cls, aconf, name, gname, sname)
        if 'C' in aconf.actions:
            self.record_c(cls, aconf, name, gname, sname)
        if 'U' in aconf.actions:
            self.record_u(cls, aconf, name, gname, sname)
        if 'D' in aconf.actions:
            self.record_d(cls, aconf, name, gname, sname)

    def record_l(self: API, cls: type[APIObject], aconf: AConf, name: str, gname: str, sname: str) -> None:
        def l(actx: ACtx) -> Tuple[int, Any]:
            result = cls.find(actx.qs).exec()
            return (200, result)
        self._records.append(APIRecord(f'l_{name}', 'L', 'GET', gname, l))

    def record_r(self: API, cls: type[APIObject], aconf: AConf, name: str, gname: str, sname: str) -> None:
        def r(actx: ACtx) -> Tuple[int, Any]:
            result = cls.id(actx.id, actx.qs).exec()
            return (200, result)
        self._records.append(APIRecord(f'r_{name}', 'R', 'GET', sname, r))

    def record_c(self: API, cls: type[APIObject], aconf: AConf, name: str, gname: str, sname: str) -> None:
        def c(actx: ACtx) -> Tuple[int, Any]:
            result = cls(**(actx.body or {})).opby(actx.operator).save()
            return (200, result)
        self._records.append(APIRecord(f'c_{name}', 'C', 'POST', gname, c))

    def record_u(self: API, cls: type[APIObject], aconf: AConf, name: str, gname: str, sname: str) -> None:
        def u(actx: ACtx) -> Tuple[int, Any]:
            result = cls.id(actx.id, actx.qs).exec().opby(actx.operator).set(**(actx.body or {})).save()
            return (200, result)
        self._records.append(APIRecord(f'u_{name}', 'U', 'PATCH', sname, u))

    def record_d(self: API, cls: type[APIObject], aconf: AConf, name: str, gname: str, sname: str) -> None:
        def d(actx: ACtx) -> Tuple[int, Any]:
            cls.id(actx.id).exec().opby(actx.operator).delete()
            return (204, None)
        self._records.append(APIRecord(f'd_{name}', 'D', 'DELETE', sname, d))

    def record_e(self: API, cls: type[APIObject], name: str, ename: str) -> None:
        def e(actx: ACtx) -> tuple[int, Any]:
            ufields = cls.cdef._unique_fields
            unames = [f.name for f in ufields]
            ujsonnames = [f.json_name for f in ufields]
            uvalidnames = set(unames + ujsonnames)
            matcher: dict[str, Any] = {}
            updater: dict[str, Any] = {}
            for k, v in actx.body.items():
                if k in uvalidnames:
                    if actx.body[k] is not None:
                        matcher[k] = v
                else:
                    updater[k] = v
            result = cls.one(matcher).optional.exec()
            if result:
                result.opby(actx.operator).set(**updater).save()
            else:
                result = cls(**actx.body).opby(actx.operator).save()
            return (200, result)
        self._records.append(APIRecord(f'e_{name}', 'E', 'POST', ename, e))

    @property
    def records(self) -> list[APIRecord]:
        return self._records

API.default = API('default')
