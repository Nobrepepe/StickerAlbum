"""Errors raised by domain services (recoverable, user-presentable)."""

from repositories.errors import AppError


class PackConfigError(AppError):
    """A pack definition is invalid (bad selector, empty pool, ...)."""


class ViceError(AppError):
    """A vice conversion or shop action cannot be completed."""


class ApplyError(AppError):
    """A sticker placement was rejected (unowned sticker/style, ...)."""
