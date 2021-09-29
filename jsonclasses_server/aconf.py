"""This module defines `AConf`. This configuration object represents
JSONClasses object's API configurations.
"""
from __future__ import annotations
from typing import Optional, Callable, Union, cast, final
from .api_object import APIObject


@final
class AConf:
    """This configuration object represents JSONClasses object's API
    configurations.
    """

    def __init__(self: AConf,
                 cls: Union[type[APIObject], None],
                 name: Optional[str],
                 enable: Optional[str],
                 disable: Optional[str],
                 cname_to_pname: Optional[Callable[[str], str]],
                 fname_to_pname: Optional[Callable[[str], str]],
                 pname_to_cname: Optional[Callable[[str], str]],
                 pname_to_fname: Optional[Callable[[str], str]],
                 cname_to_srname: Optional[Callable[[str], str]]) -> None:
        """
        Initialize a new API configuration object.
        """
        self._cls = cls
        self._name = name
        self._enable = enable
        self._disable = disable
        self._actions: list[str] | None = None
        self._cname_to_pname = cname_to_pname
        self._fname_to_pname = fname_to_pname
        self._pname_to_cname = pname_to_cname
        self._pname_to_fname = pname_to_fname
        self._cname_to_srname = cname_to_srname

    @property
    def cls(self: AConf) -> type[APIObject]:
        """The JSON class on which this class config is defined.
        """
        return cast(type[APIObject], self._cls)

    @property
    def default_aconf(self: AConf) -> AConf:
        from .api_class import API
        gname = self.cls.cdef.jconf.cgraph.name
        return API(gname).aconf

    @property
    def name(self: AConf) -> str:
        if self._name is not None:
            return self._name
        self._name = self.cname_to_pname(self.cls.__name__)
        return self._name

    @property
    def actions(self: AConf) -> list[str]:
        if self._actions:
            return self._actions
        if self._disable is not None:
            enabled = self._enable or "CRUDL"
            self._actions = list(set(enabled) - set(self._disable))
            return self._actions
        if self._enable is not None:
            self._actions = list(set(self._enable))
            return self._actions
        return self.default_aconf.actions

    @property
    def cname_to_pname(self: AConf) -> Callable[[str], str]:
        if self._cname_to_pname is not None:
            return self._cname_to_pname
        return self.default_aconf.cname_to_pname

    @property
    def fname_to_pname(self: AConf) -> Callable[[str], str]:
        if self._fname_to_pname is not None:
            return self._fname_to_pname
        return self.default_aconf.fname_to_pname

    @property
    def pname_to_cname(self: AConf) -> Callable[[str], str]:
        if self._pname_to_cname is not None:
            return self._pname_to_cname
        return self.default_aconf.pname_to_cname

    @property
    def pname_to_fname(self: AConf) -> Callable[[str], str]:
        if self._pname_to_fname is not None:
            return self._pname_to_fname
        return self.default_aconf.pname_to_fname

    @property
    def cname_to_srname(self: AConf) -> Callable[[str], str]:
        if self._cname_to_srname is not None:
            return self._cname_to_srname
        return self.default_aconf.cname_to_srname
