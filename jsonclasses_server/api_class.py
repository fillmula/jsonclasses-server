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
            def l(actx: ACtx) -> Tuple[int, Any]:
                result = cls.find(actx.qs).exec()
                return (200, result)
            self._records.append(APIRecord('L', 'GET', gname, l))
        if 'R' in aconf.actions:
            def r(actx: ACtx) -> Tuple[int, Any]:
                result = cls.id(actx.id).exec()
                return (200, result)
            self._records.append(APIRecord('R', 'GET', sname, r))
        if 'C' in aconf.actions:
            def c(actx: ACtx) -> Tuple[int, Any]:
                result = cls(**(actx.body or {})).save()
                return (200, result)
            self._records.append(APIRecord('C', 'POST', gname, c))
        if 'U' in aconf.actions:
            def u(actx: ACtx) -> Tuple[int, Any]:
                result = cls.id(actx.id).exec().set(**(actx.body or {})).save()
                return (200, result)
            self._records.append(APIRecord('U', 'PATCH', sname, u))
        if 'D' in aconf.actions:
            def d(actx: ACtx) -> Tuple[int, Any]:
                cls.id(actx.id).exec().delete()
                return (204, None)
            self._records.append(APIRecord('D', 'DELETE', sname, d))

    @property
    def records(self) -> list[APIRecord]:
        return self._records

API.default = API('default')
