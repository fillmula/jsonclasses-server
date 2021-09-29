from __future__ import annotations
from typing import Union, Callable, Optional, overload, cast
from datetime import timedelta
from jsonclasses.isjsonclass import isjsonclass
from .aconf import AConf
from .api_object import APIObject
from .auth_conf import AuthConf


@overload
def authorized(cls: type[APIObject]) -> type[APIObject]: ...


@overload
def authorized(
    cls: None,
    expires_in: Optional[timedelta] = None,
) -> Callable[[type[APIObject]], type[APIObject]]: ...


@overload
def authorized(
    cls: type[APIObject],
    expires_in: Optional[timedelta] = None,
) -> type[APIObject]: ...


def authorized(
    cls: Union[type[APIObject], None],
    expires_in: Optional[timedelta] = None,
) -> Union[Callable[[type[APIObject]], type[APIObject]], type[APIObject]]:
    from .api_class import API
    if cls is not None:
        if not isjsonclass(cls):
            raise ValueError('@authorized should be used to decorate a '
                             'JSONClass class.')
        cls = cast(type[APIObject], cls)
        auth_conf = AuthConf(expires_in=expires_in)
        API(cls.cdef.jconf.cgraph.name).record_auth(cls, auth_conf)
        return cls
    else:
        def parametered_api(cls):
            return authorized(cls, expires_in=expires_in)
        return parametered_api
