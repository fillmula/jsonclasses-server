from __future__ import annotations
from typing import ClassVar
from .api_object import APIObject
from .aconf import AConf
from .api_record import APIRecord
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
            def l() -> None:
                return None
            self._records.append(APIRecord('GET', gname, l))
        if 'R' in aconf.actions:
            def r() -> None:
                return None
            self._records.append(APIRecord('GET', sname, r))
        if 'C' in aconf.actions:
            def c() -> None:
                return None
            self._records.append(APIRecord('POST', gname, c))
        if 'U' in aconf.actions:
            def u() -> None:
                return None
            self._records.append(APIRecord('PATCH', sname, u))
        if 'D' in aconf.actions:
            def d() -> None:
                return None
            self._records.append(APIRecord('DELETE', sname, d))




API.default = API('default')
