"""
Monetary and Financial Math Utilities
Guarantees exact Decimal calculations with zero floating-point arithmetic.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple


def to_decimal(value: any) -> Decimal:
    """Safely converts any input into a quantified Decimal."""
    if value is None:
        return Decimal("0.0000")
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    return Decimal(str(value)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def calculate_difference_and_percentage(
    current: Decimal, previous: Decimal
) -> Tuple[Decimal, Decimal, str]:
    """
    Computes (difference, percentage_change, direction).
    direction is 'UP', 'DOWN', or 'FLAT'.
    """
    curr = to_decimal(current)
    prev = to_decimal(previous)
    diff = curr - prev

    # Quantize to 2 decimal places to match user-facing currency thresholds
    curr_2dec = curr.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    prev_2dec = prev.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    diff_2dec = curr_2dec - prev_2dec

    if prev_2dec == Decimal("0.00"):
        if curr_2dec == Decimal("0.00"):
            pct = Decimal("0.00")
            direction = "FLAT"
            diff = Decimal("0.0000")
        else:
            pct = Decimal("100.00")
            direction = "UP"
    else:
        raw_pct = (diff / abs(prev)) * Decimal("100")
        pct = raw_pct.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if diff_2dec > Decimal("0.00"):
            direction = "UP"
        elif diff_2dec < Decimal("0.00"):
            direction = "DOWN"
        else:
            direction = "FLAT"

    return diff, pct, direction


def format_currency(amount: Decimal, symbol: str = "$") -> str:
    """Formats a decimal amount as standard currency, e.g. $1,234.56."""
    d = to_decimal(amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{symbol}{d:,.2f}"

