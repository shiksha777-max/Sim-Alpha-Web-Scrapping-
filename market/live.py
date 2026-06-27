from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from nepse_scraper import NepseScraper

from config import MarketConfig


def is_trading_window(market_config: MarketConfig, now: datetime | None = None) -> bool:
    """
    True only inside the configured trading window
    (default: Mon-Fri, 11:00-15:00 Asia/Kathmandu).

    Keeps the scheduler from hitting NEPSE outside trading hours when
    there's nothing new to fetch.
    """
    tz = ZoneInfo(market_config.timezone)
    local_now = (now or datetime.now(tz)).astimezone(tz)

    if local_now.weekday() not in market_config.trading_days:
        return False
    if not (market_config.trading_start_hour <= local_now.hour < market_config.trading_end_hour):
        return False
    return True


def fetch_live_market(verify_ssl: bool = False) -> dict[str, Any]:
    """
    Pulls a live NEPSE market snapshot: market-open flag + per-symbol prices.

    verify_ssl=False is required - NEPSE's own SSL certificate chain is
    incomplete, so a strict TLS check will raise SSLCertVerificationError.
    """
    scraper = NepseScraper(verify_ssl=verify_ssl)

    market_open = scraper.is_market_open()
    today_prices = scraper.get_today_price()  # list of per-symbol dicts

    fetched_at = datetime.utcnow()
    rows: list[dict[str, Any]] = []
    for item in today_prices:
        rows.append({
            "symbol": item.get("symbol"),
            "ltp": item.get("lastTradedPrice"),
            "change_percent": item.get("percentageChange"),
            "open_price": item.get("openPrice"),
            "high_price": item.get("highPrice"),
            "low_price": item.get("lowPrice"),
            "volume": item.get("totalTradedQuantity"),
            "fetched_at": fetched_at,
        })

    return {"market_open": market_open, "fetched_at": fetched_at, "rows": rows}
