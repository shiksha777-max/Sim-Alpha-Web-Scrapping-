"""
FastAPI entry point.
Starts the 30-minute scrape+analyze scheduler as a background daemon thread.
"""
from __future__ import annotations

import os
import threading
from typing import Any

from fastapi import FastAPI, HTTPException, Query

from config import load_app_config
from db import ensure_table_exists, get_connection

app = FastAPI(title="Nepali News Sentiment API", version="1.0.0")

_scheduler_thread: threading.Thread | None = None
_scheduler_lock = threading.Lock()


def _start_scheduler_once() -> None:
    global _scheduler_thread
    with _scheduler_lock:
        if _scheduler_thread is not None and _scheduler_thread.is_alive():
            return

        from scraper.scheduler import start_scheduler
        config = load_app_config()

        def _run() -> None:
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


# ---------------------------------------------------------------------------
# GET /sentiment-summary
# ---------------------------------------------------------------------------

_SUMMARY_SQL = """
SELECT
    source,
    sentiment,
    COUNT(*)                            AS count,
    ROUND(AVG(sentiment_score)::numeric, 4) AS avg_score
FROM news_articles
WHERE analyzed = TRUE
  AND scraped_at >= NOW() - INTERVAL '%s hours'
GROUP BY source, sentiment
ORDER BY source, sentiment;
"""

_CATEGORY_SQL = """
SELECT
    category,
    sentiment,
    COUNT(*) AS count
FROM news_articles
WHERE analyzed = TRUE
  AND scraped_at >= NOW() - INTERVAL '%s hours'
  AND category IS NOT NULL
  AND category <> ''
GROUP BY category, sentiment
ORDER BY category, count DESC;
"""

_TOTAL_SQL = """
SELECT
    sentiment,
    COUNT(*) AS count
FROM news_articles
WHERE analyzed = TRUE
  AND scraped_at >= NOW() - INTERVAL '%s hours'
GROUP BY sentiment;
"""


@app.get("/sentiment-summary")
def get_sentiment_summary(
    hours: int = Query(default=24, ge=1, le=720, description="Look-back window in hours"),
) -> dict[str, Any]:
    """
    Returns sentiment breakdown (positive / neutral / negative) for the last N hours.
    Grouped by source portal and category.
    """
    config = load_app_config()
    try:
        conn = get_connection(config.database)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB connection failed: {e}") from e

    try:
        with conn.cursor() as cur:
            # Overall totals
            cur.execute(_TOTAL_SQL % hours)
            total_rows = cur.fetchall()
            overall = {row[0]: int(row[1]) for row in total_rows}

            # Per-source breakdown
            cur.execute(_SUMMARY_SQL % hours)
            source_rows = cur.fetchall()

            # Per-category breakdown
            cur.execute(_CATEGORY_SQL % hours)
            category_rows = cur.fetchall()
    finally:
        conn.close()

    # Build per-source dict
    by_source: dict[str, dict[str, Any]] = {}
    for source, sentiment, count, avg_score in source_rows:
        if source not in by_source:
            by_source[source] = {"source": source, "positive": 0, "neutral": 0, "negative": 0, "avg_scores": {}}
        by_source[source][sentiment] = int(count)
        by_source[source]["avg_scores"][sentiment] = float(avg_score or 0)

    # Build per-category dict
    by_category: dict[str, dict[str, Any]] = {}
    for category, sentiment, count in category_rows:
        if category not in by_category:
            by_category[category] = {"category": category, "positive": 0, "neutral": 0, "negative": 0}
        by_category[category][sentiment] = int(count)

    total_articles = sum(overall.values())

    return {
        "window_hours": hours,
        "total_articles_analyzed": total_articles,
        "overall": {
            "positive": overall.get("positive", 0),
            "neutral": overall.get("neutral", 0),
            "negative": overall.get("negative", 0),
        },
        "by_source": list(by_source.values()),
        "by_category": sorted(
            by_category.values(),
            key=lambda x: x["positive"] + x["neutral"] + x["negative"],
            reverse=True,
        )[:20],
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8001")), reload=False)
