from decimal import Decimal, ROUND_HALF_UP
import re


def money(value) -> Decimal:
    """Parse UI currency strings (including Indian grouping) without float loss."""
    text = str(value).replace("−", "-")
    match = re.search(r"-?\d[\d,]*(?:\.\d+)?", text)
    if not match:
        return Decimal("0")
    return Decimal(match.group(0).replace(",", ""))


def line_total(quantity, rate, discount=0, tax=0) -> Decimal:
    base = Decimal(str(quantity)) * Decimal(str(rate))
    net = base - (base * Decimal(str(discount)) / Decimal("100"))
    return (net + net * Decimal(str(tax)) / Decimal("100")).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def ledger_closing(opening, debits=0, credits=0, adjustments=0) -> Decimal:
    return (Decimal(str(opening)) + Decimal(str(debits)) - Decimal(str(credits)) + Decimal(str(adjustments))).quantize(Decimal("0.001"))
