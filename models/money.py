"""Centralized money handling. All amounts are stored as integer minor
currency units (cents) and only formatted here."""


def format_money(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    whole, minor = divmod(abs(cents), 100)
    grouped = f"{whole:,}".replace(",", ".")  # Brazilian thousands separator
    return f"{sign}R$ {grouped},{minor:02d}"
