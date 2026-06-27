from __future__ import annotations
import os
import threading
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from config import load_app_config
from db import ensure_table_exists, get_connection

app = FastAPI(title="NEPSE News Pipeline API", version="1.0.0")

_scheduler_thread: threading.Thread | None = None
_scheduler_lock = threading.Lock()


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


@app.get("/articles")
def get_articles(
    hours: int = Query(default=24, ge=1, le=720, description="Look-back window in hours"),
    tier: str = Query(default="all", description="Filter by portal tier: all / finance / general"),
    limit: int = Query(default=50, ge=1, le=500),
) -> dict[str, Any]:
    """
    Returns recently scraped articles from all 20 portals.
    """
    config = load_app_config()

    tier_filter = ""
    if tier in ("finance", "general"):
        tier_filter = f"AND portal_tier = '{tier}'"

    sql = f"""
        SELECT source, portal_tier, title, category, url, scraped_at
        FROM nepse_news
        WHERE scraped_at >= NOW() - INTERVAL '{hours} hours'
          {tier_filter}
        ORDER BY scraped_at DESC
        LIMIT {limit}
    """

    try:
        conn = get_connection(config.database)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}") from e

    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
    finally:
        conn.close()

    articles = [
        {
            "source": r[0],
            "portal_tier": r[1],
            "title": r[2],
            "category": r[3],
            "url": r[4],
            "scraped_at": str(r[5]),
        }
        for r in rows
    ]

    return {
        "window_hours": hours,
        "portal_tier_filter": tier,
        "total": len(articles),
        "articles": articles,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8001")), reload=False)
