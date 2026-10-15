"""Exact money handling.

Amounts are stored internally as whole pesewas (integers; 100 pesewas = 1 GHS),
so no floating point is ever involved and addition/subtraction is exact.
Floats are rejected on input because 0.1 + 0.2 != 0.3 in binary floating point.
"""
import re
from decimal import Decimal

from .errors import InvalidAmountError

# Optional sign, up to 12 whole digits, optional fractional part. No exponents,
# no "nan"/"inf", no thousands separators.
_PATTERN = re.compile(r"^[+-]?[0-9]{1,12}(\.[0-9]{1,2})?$")


def parse_amount(value) -> int:
    """Parse a positive GHS amount with at most 2 decimals into pesewas.

    Accepts str, Decimal or int. Rejects float, bool, zero and negatives.
    """
    if isinstance(value, bool) or isinstance(value, float):
        raise InvalidAmountError(
            "amount must be text like '50.00' (floats are not allowed: they are inexact)"
        )
    if isinstance(value, (int, Decimal)):
        value = str(value)
    if not isinstance(value, str):
        raise InvalidAmountError(f"unsupported amount type: {type(value).__name__}")

    text = value.strip()
    if not _PATTERN.fullmatch(text):
        raise InvalidAmountError(f"'{value}' is not a valid amount (example: 50.00)")

    whole, _, fraction = text.lstrip("+-").partition(".")
    amount = int(whole) * 100 + int(fraction.ljust(2, "0"))
    if text.startswith("-") or amount == 0:
        raise InvalidAmountError("amount must be greater than zero")
    return amount


def to_decimal(pesewas: int) -> Decimal:
    """Convert pesewas to an exact Decimal with 2 places, e.g. 2000 -> Decimal('20.00')."""
    return Decimal(format_amount(pesewas))


def format_amount(pesewas: int) -> str:
    """Format pesewas as a plain string with 2 decimals, e.g. 15000 -> '150.00'."""
    sign = "-" if pesewas < 0 else ""
    whole, frac = divmod(abs(pesewas), 100)
    return f"{sign}{whole}.{frac:02d}"
