from __future__ import annotations
from typing import ClassVar, Tuple, Any
from .api_object import APIObject
from .aconf import AConf
from .api_record import APIRecord
from .actx import ACtx
from .nameutils import (
    cname_to_pname, fname_to_pname, pname_to_cname, pname_to_fname
)


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
            pname_to_fname=pname_to_fname)
        self._records: list[APIRecord] = []
        self.__class__._initialized_map[graph_name] = True
        return None

    default: ClassVar[API]

    @property
    def aconf(self: API) -> AConf:
        """The default API configuration for all classes on this graph."""
        return self._default_aconf

    def record(self: API, cls: type[APIObject], aconf: AConf) -> None:
        name = aconf.name or aconf.cname_to_pname(cls.__name__)
        gname = f'/{name}'
        sname = f'{gname}/:id'
        if 'L' in aconf.actions:
            self.record_l(cls, aconf, name, gname, sname)
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
            result = cls.id(actx.id).exec()
            return (200, result)
        self._records.append(APIRecord(f'r_{name}', 'R', 'GET', sname, r))

    def record_c(self: API, cls: type[APIObject], aconf: AConf, name: str, gname: str, sname: str) -> None:
        def c(actx: ACtx) -> Tuple[int, Any]:
            result = cls(**(actx.body or {})).save()
            return (200, result)
        self._records.append(APIRecord(f'c_{name}', 'C', 'POST', gname, c))

    def record_u(self: API, cls: type[APIObject], aconf: AConf, name: str, gname: str, sname: str) -> None:
        def u(actx: ACtx) -> Tuple[int, Any]:
            result = cls.id(actx.id).exec().set(**(actx.body or {})).save()
            return (200, result)
        self._records.append(APIRecord(f'u_{name}', 'U', 'PATCH', sname, u))

    def record_d(self: API, cls: type[APIObject], aconf: AConf, name: str, gname: str, sname: str) -> None:
        def d(actx: ACtx) -> Tuple[int, Any]:
            cls.id(actx.id).exec().delete()
            return (204, None)
        self._records.append(APIRecord(f'd_{name}', 'D', 'DELETE', sname, d))

    @property
    def records(self) -> list[APIRecord]:
        return self._records

API.default = API('default')
