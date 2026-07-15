"""Errors raised by domain services (recoverable, user-presentable)."""

from repositories.errors import AppError


class PackConfigError(AppError):
    """A pack definition is invalid (bad selector, empty pool, ...)."""


class ApplyError(AppError):
    """A sticker placement was rejected (unowned sticker/style, ...)."""
