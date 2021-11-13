"""This module defines `AuthConf`. This configuration object represents
JSONClasses object's authorization configurations.
"""
from __future__ import annotations
from typing import final
from datetime import timedelta


@final
class AuthInfo:
    """This class records the information used to do authentication.
    """

    def __init__(self) -> None:
        self._identities: list[str] = []
        self._bys: list[str] = []
        self._srname: str = ''

    @property
    def identities(self) -> list[str]:
        return self._identities

    @property
    def bys(self) -> list[str]:
        return self._bys

    @property
    def srname(self) -> str:
        return self._srname


@final
class AuthConf:
    """This configuration object represents JSONClasses object's authorization
    configurations.
    """

    def __init__(self: AuthConf, expires_in: timedelta | None = None) -> None:
        """
        Initialize a new AuthConf configuration object.
        """
        self._expires_in = expires_in
        self._info = AuthInfo()

    @property
    def expires_in(self: AuthConf) -> timedelta:
        return self._expires_in or timedelta(365)

    @property
    def info(self: AuthConf) -> AuthInfo:
        return self._info
