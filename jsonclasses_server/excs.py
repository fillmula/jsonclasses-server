from __future__ import annotations


class AuthenticationException(Exception):
    """Authentication exception is throwed when user is not authorized.
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)
