from __future__ import annotations
from typing import Union, Callable, Optional, overload
from jsonclasses.jobject import JObject
from jsonclasses.isjsonclass import isjsonclass
from .aconf import AConf


@overload
def api(cls: type[JObject]) -> type: ...


@overload
def api(
    cls: None,
    name: Optional[str] = None,
    enable: Optional[str] = None,
    disable: Optional[str] = None,
    class_name_to_pathname: Optional[Callable[[str], str]] = None,
    field_name_to_pathname: Optional[Callable[[str], str]] = None,
    pathname_to_class_name: Optional[Callable[[str], str]] = None,
    pathname_to_field_name: Optional[Callable[[str], str]] = None
) -> Callable[[type[JObject]], type[JObject]]: ...


@overload
def api(
    cls: type[JObject],
    name: Optional[str] = None,
    enable: Optional[str] = None,
    disable: Optional[str] = None,
    class_name_to_pathname: Optional[Callable[[str], str]] = None,
    field_name_to_pathname: Optional[Callable[[str], str]] = None,
    pathname_to_class_name: Optional[Callable[[str], str]] = None,
    pathname_to_field_name: Optional[Callable[[str], str]] = None
) -> type[JObject]: ...


def api(
    cls: type[JObject],
    name: Optional[str] = None,
    enable: Optional[str] = None,
    disable: Optional[str] = None,
    class_name_to_pathname: Optional[Callable[[str], str]] = None,
    field_name_to_pathname: Optional[Callable[[str], str]] = None,
    pathname_to_class_name: Optional[Callable[[str], str]] = None,
    pathname_to_field_name: Optional[Callable[[str], str]] = None
) -> Union[Callable[[type[JObject]], type[JObject]], type[JObject]]:
    from .api_class import API
    if cls is not None:
        if not isjsonclass(cls):
            raise ValueError('@api should be used to decorate a JSONClass class.')
        aconf = AConf(
            cls=cls,
            name=name,
            enable=enable,
            disable=disable,
            cname_to_pname=class_name_to_pathname,
            fname_to_pname=field_name_to_pathname,
            pname_to_cname=pathname_to_class_name,
            pname_to_fname=pathname_to_field_name)
        cls.aconf = aconf
        API(cls.cdef.jconf.cgraph.name).record(cls)
        return cls
    else:
        def parametered_api(cls):
            return api(
                cls,
                name=name,
                enable=enable,
                disable=disable,
                cname_to_pname=class_name_to_pathname,
                fname_to_pname=field_name_to_pathname,
                pname_to_cname=pathname_to_class_name,
                pname_to_fname=pathname_to_field_name)
        return parametered_api
