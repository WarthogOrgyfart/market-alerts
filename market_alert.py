import os
import yfinance as yf
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

def get_price_and_change(ticker: str) -> tuple[float | None, float | None]:
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        price = info.last_price
        prev = info.previous_close
        if price is None or prev is None or prev == 0:
            return None, None
        pct = (price - prev) / prev * 100
        return price, pct
    except Exception:
        return None, None


def format_line(name: str, ticker: str) -> str:
    price, pct = get_price_and_change(ticker)
    if price is None:
        return f"{name}: data unavailable"
    sign = "+" if pct >= 0 else ""
    return f"{name}: ${price:,.2f}  ({sign}{pct:.2f}%)"


def is_weekend() -> bool:
    now = datetime.now(ZoneInfo("Europe/Amsterdam"))
    return now.weekday() >= 5


def is_us_market_open() -> bool:
    now = datetime.now(ZoneInfo("America/New_York"))
    if now.weekday() >= 5:
        return False
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return market_open <= now <= market_close


def build_message() -> str:
    lines = []
    now_str = datetime.now(ZoneInfo("Europe/Amsterdam")).strftime("%a %d %b  %H:%M Amsterdam")

    lines.append(f"📊 Market Update — {now_str}")
    lines.append("")

    if is_weekend():
        lines.append("🪙 Crypto")
        lines.append(format_line("Bitcoin", "BTC-USD"))
        lines.append(format_line("Ethereum", "ETH-USD"))
        lines.append(format_line("Hyperliquid", "HYPE32196-USD"))
        lines.append(format_line("Venice (VVV)", "VVV35509-USD"))
    else:
        if is_us_market_open():
            lines.append("🇺🇸 Indices (Cash)")
            lines.append(format_line("SPX", "^GSPC"))
            lines.append(format_line("NDX", "^NDX"))
        else:
            lines.append("🇺🇸 Indices (Futures)")
            lines.append(format_line("ES (SPX fut)", "ES=F"))
            lines.append(format_line("NQ (NDX fut)", "NQ=F"))

        lines.append("")
        lines.append("📈 Stocks")
        lines.append(format_line("GOOGL", "GOOGL"))
        lines.append(format_line("HOOD", "HOOD"))
        lines.append(format_line("SOFI", "SOFI"))

        lines.append("")
        lines.append("🪙 Crypto")
        lines.append(format_line("Bitcoin", "BTC-USD"))
        lines.append(format_line("Ethereum", "ETH-USD"))
        lines.append(format_line("Hyperliquid", "HYPE32196-USD"))
        lines.append(format_line("Venice (VVV)", "VVV35509-USD"))

    return "\n".join(lines)


def send_ntfy(message: str, topic: str):
    requests.post(
        f"https://ntfy.sh/{topic}",
        data=message.encode("utf-8"),
        headers={
            "Title": "Market Alert",
            "Priority": "default",
            "Tags": "chart_with_upwards_trend"
        },
        timeout=15
    )


if __name__ == "__main__":
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        raise ValueError("NTFY_TOPIC environment variable is missing")

    msg = build_message()
    print(msg)
    send_ntfy(msg, topic)
    print("✅ Sent to ntfy")
