"""Errors raised by the data layer."""


class AppError(Exception):
    """Base for errors that carry a user-presentable message."""


class CatalogError(AppError):
    """A catalog file is missing or malformed."""


class UnknownIdError(AppError):
    """Lookup for an ID that does not exist in the catalog."""


class StateSaveError(AppError):
    """User state could not be written to disk."""
