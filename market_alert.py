import os
import yfinance as yf
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

def get_price_and_change(ticker: str) -> tuple[float | None, float | None, float | None]:
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        price = info.last_price
        prev = info.previous_close
        if price is None or prev is None or prev == 0:
            return None, None, None
        change = price - prev
        pct = (change / prev) * 100
        return price, change, pct
    except Exception:
        return None, None, None


def format_line(name: str, ticker: str) -> tuple[str, float | None]:
    price, change, pct = get_price_and_change(ticker)
    if price is None:
        return f"{name}: data unavailable", None
    sign = "+" if change >= 0 else ""
    line = f"{name}: ${price:,.2f}  ({sign}{change:,.2f} / {sign}{pct:.2f}%)"
    return line, pct


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
    now_str = datetime.now(ZoneInfo("Europe/Amsterdam")).strftime("%a %d %b  %H:%M")

    lines.append(f"📊 Market Update — {now_str}")
    lines.append("")

    all_movers = []  # to find best/worst

    if is_weekend():
        lines.append("🪙 Crypto")
        for name, ticker in [
            ("Bitcoin", "BTC-USD"),
            ("Ethereum", "ETH-USD"),
            ("Hyperliquid", "HYPE32196-USD"),
            ("Venice (VVV)", "VVV35509-USD"),
        ]:
            line, pct = format_line(name, ticker)
            lines.append(line)
            if pct is not None:
                all_movers.append((name, pct))
    else:
        if is_us_market_open():
            lines.append("🇺🇸 Indices (Cash)")
            for name, ticker in [("SPX", "^GSPC"), ("NDX", "^NDX")]:
                line, pct = format_line(name, ticker)
                lines.append(line)
                if pct is not None:
                    all_movers.append((name, pct))
        else:
            lines.append("🇺🇸 Indices (Futures)")
            for name, ticker in [("ES (SPX fut)", "ES=F"), ("NQ (NDX fut)", "NQ=F")]:
                line, pct = format_line(name, ticker)
                lines.append(line)
                if pct is not None:
                    all_movers.append((name, pct))

        lines.append("")
        lines.append("📈 Stocks")
        for name, ticker in [("GOOGL", "GOOGL"), ("HOOD", "HOOD"), ("SOFI", "SOFI")]:
            line, pct = format_line(name, ticker)
            lines.append(line)
            if pct is not None:
                all_movers.append((name, pct))

        lines.append("")
        lines.append("🪙 Crypto")
        for name, ticker in [
            ("Bitcoin", "BTC-USD"),
            ("Ethereum", "ETH-USD"),
            ("Hyperliquid", "HYPE32196-USD"),
            ("Venice (VVV)", "VVV35509-USD"),
        ]:
            line, pct = format_line(name, ticker)
            lines.append(line)
            if pct is not None:
                all_movers.append((name, pct))

    # Add Best / Worst summary at the top (after the header)
    if all_movers:
        best = max(all_movers, key=lambda x: x[1])
        worst = min(all_movers, key=lambda x: x[1])
        summary = f"Best: {best[0]} {best[1]:+.2f}%   |   Worst: {worst[0]} {worst[1]:+.2f}%"
        lines.insert(1, summary)
        lines.insert(2, "")

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
