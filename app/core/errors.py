"""Core error definitions."""


class AppError(Exception):
    """Base application error."""

    pass


class InvalidStateError(AppError):
    """Raised when an invalid state transition is attempted."""

    pass


class ConfigError(AppError):
    """Raised when there is a configuration error."""

    pass
