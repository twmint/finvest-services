def normalize_quotes(quotes: list[dict], include_volume: bool = False) -> list[dict]:
    return [
        {
            "symbol": q["symbol"],
            "name": q.get("shortName") or q.get("longName"),
            "price": q["regularMarketPrice"],
            "percentChange": f"{round(q['regularMarketChangePercent'], 2):+.2f}%",
            **({"volume": q["regularMarketVolume"]} if include_volume else {})
        }
        for q in quotes
    ]


def safe_quotes(data: dict, key: str) -> list:
    result = data.get(key, {})
    return result.get("quotes", []) if isinstance(result, dict) else []