from decimal import Decimal, ROUND_HALF_UP

def round_half_up(value: str) -> str:
    fVal = Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return str(fVal)

def format_large_num(value: int) -> str:
    if value >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:.2f}T"
    elif value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"{value / 1_000:.2f}K"
    else:
        return str(value)