from __future__ import annotations
import os
import threading
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from config import load_app_config
from db import ensure_table_exists, get_connection

app = FastAPI(title="NEPSE News Sentiment API", version="1.0.0")

_scheduler_thread: threading.Thread | None = None
_scheduler_lock = threading.Lock()
_analyzer = None


def _start_scheduler_once() -> None:
    global _scheduler_thread
    with _scheduler_lock:
        if _scheduler_thread is not None and _scheduler_thread.is_alive():
            return

        from scraper.scheduler import start_scheduler
        config = load_app_config()

        def _run():
            try:
                start_scheduler(config.scraper.interval_minutes)
            except Exception as e:
                print(f"[Scheduler] Crashed: {e}")

        _scheduler_thread = threading.Thread(target=_run, name="news-scheduler", daemon=True)
        _scheduler_thread.start()


@app.on_event("startup")
def on_startup() -> None:
    config = load_app_config()
    ensure_table_exists(config.database)
    _start_scheduler_once()


# ── /sentiment-summary ──────────────────────────────────────────────────────

@app.get("/sentiment-summary")
def get_sentiment_summary(
    hours: int = Query(default=24, ge=1, le=720, description="Look-back window in hours"),
    tier: str = Query(default="all", description="Filter by portal tier: all / finance / general"),
) -> dict[str, Any]:
    """
    Returns sentiment breakdown for the last N hours.
    Optional ?tier=finance to see only NEPSE-focused portals.
    Optional ?tier=general to see only general news portals.
    """
    config = load_app_config()

    tier_filter = ""
    if tier in ("finance", "general"):
        tier_filter = f"AND portal_tier = '{tier}'"

    sql_overall = f"""
        SELECT sentiment, COUNT(*) AS count
        FROM nepse_news
        WHERE analyzed = TRUE
          AND scraped_at >= NOW() - INTERVAL '{hours} hours'
          {tier_filter}
        GROUP BY sentiment
    """

    sql_by_source = f"""
        SELECT source, portal_tier, sentiment, COUNT(*) AS count,
               ROUND(AVG(sentiment_score)::numeric, 4) AS avg_score
        FROM nepse_news
        WHERE analyzed = TRUE
          AND scraped_at >= NOW() - INTERVAL '{hours} hours'
          {tier_filter}
        GROUP BY source, portal_tier, sentiment
        ORDER BY source, sentiment
    """

    sql_by_category = f"""
        SELECT category, sentiment, COUNT(*) AS count
        FROM nepse_news
        WHERE analyzed = TRUE
          AND scraped_at >= NOW() - INTERVAL '{hours} hours'
          AND category IS NOT NULL AND category <> ''
          {tier_filter}
        GROUP BY category, sentiment
        ORDER BY count DESC
        LIMIT 20
    """

    try:
        conn = get_connection(config.database)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}") from e

    try:
        with conn.cursor() as cur:
            cur.execute(sql_overall)
            overall_rows = cur.fetchall()

            cur.execute(sql_by_source)
            source_rows = cur.fetchall()

            cur.execute(sql_by_category)
            cat_rows = cur.fetchall()
    finally:
        conn.close()

    overall = {row[0]: int(row[1]) for row in overall_rows}

    by_source: dict[str, dict] = {}
    for source, ptier, sentiment, count, avg_score in source_rows:
        if source not in by_source:
            by_source[source] = {
                "source": source,
                "portal_tier": ptier,
                "positive": 0, "neutral": 0, "negative": 0,
            }
        by_source[source][sentiment] = int(count)

    by_category: dict[str, dict] = {}
    for category, sentiment, count in cat_rows:
        if category not in by_category:
            by_category[category] = {"category": category, "positive": 0, "neutral": 0, "negative": 0}
        by_category[category][sentiment] = int(count)

    return {
        "window_hours": hours,
        "portal_tier_filter": tier,
        "total_articles_analyzed": sum(overall.values()),
        "overall": {
            "positive": overall.get("positive", 0),
            "neutral":  overall.get("neutral", 0),
            "negative": overall.get("negative", 0),
        },
        "by_source": sorted(by_source.values(), key=lambda x: x["source"]),
        "by_category": list(by_category.values()),
    }


# ── /market-live ─────────────────────────────────────────────────────────────

@app.get("/market-live")
def get_market_live() -> dict[str, Any]:
    """
    Returns the most recently stored live price per symbol.

    Only refreshed Mon-Fri 11:00-15:00 Asia/Kathmandu (configurable via
    MARKET_* vars in .env); outside that window this reflects the last
    trading session's final snapshot.
    """
    config = load_app_config()

    try:
        conn = get_connection(config.database)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}") from e

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT ON (symbol)
                       symbol, ltp, change_percent, open_price, high_price, low_price, volume, fetched_at
                FROM nepse_market_live
                ORDER BY symbol, fetched_at DESC
            """)
            rows = cur.fetchall()
    finally:
        conn.close()

    symbols = [
        {
            "symbol": r[0],
            "ltp": r[1],
            "change_percent": r[2],
            "open_price": r[3],
            "high_price": r[4],
            "low_price": r[5],
            "volume": r[6],
            "fetched_at": str(r[7]),
        }
        for r in rows
    ]

    return {
        "as_of": max((s["fetched_at"] for s in symbols), default=None),
        "symbol_count": len(symbols),
        "symbols": sorted(symbols, key=lambda x: x["symbol"]),
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8001")), reload=False)
