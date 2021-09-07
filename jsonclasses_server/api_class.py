from __future__ import annotations
from typing import ClassVar
from jsonclasses.jobject import JObject
from .aconf import AConf
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
            name=None,
            enable='CRUDL',
            disable=None,
            cname_to_pname=cname_to_pname,
            fname_to_pname=fname_to_pname,
            pname_to_cname=pname_to_cname,
            pname_to_fname=pname_to_fname)
        self._starting_names: dict[str, type[JObject]] = {}
        self.__class__._initialized_map[graph_name] = True
        return None

    @property
    def aconf(self: API) -> AConf:
        """The default API configuration for all classes on this graph."""
        return self._default_aconf

    def record(self: API, cls: type[JObject], aconf: AConf) -> None:
        name = aconf.cname_to_pname(cls.__name__)
        self._starting_names[name] = cls

        pass

    default: ClassVar[API]


API.default = API('default')
