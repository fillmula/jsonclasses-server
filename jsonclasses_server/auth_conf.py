"""This module defines `AuthConf`. This configuration object represents
JSONClasses object's authorization configurations.
"""
from __future__ import annotations
from typing import final
from datetime import timedelta


@final
class AuthConf:
    """This configuration object represents JSONClasses object's authorization
    configurations.
    """

    def __init__(self: AuthConf, expires_in: timedelta) -> None:
        """
        Initialize a new AuthConf configuration object.
        """
        self._expires_in = expires_in

    @property
    def expires_in(self: AuthConf) -> timedelta:
        return self._expires_in or timedelta(365)
