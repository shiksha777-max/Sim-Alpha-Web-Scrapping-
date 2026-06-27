from __future__ import annotations
from typing import Any
from psycopg2.extras import execute_values
from db.connection import get_connection
from config import DatabaseConfig

_INSERT_SQL = """
INSERT INTO nepse_news (source, portal_tier, url, title, body, category, published_at)
VALUES %s
ON CONFLICT (url) DO NOTHING
"""

_INSERT_MARKET_SQL = """
INSERT INTO nepse_market_live
    (symbol, ltp, change_percent, open_price, high_price, low_price, volume, fetched_at)
VALUES %s
"""


def write_articles(articles: list[dict[str, Any]], db_config: DatabaseConfig) -> int:
    if not articles:
        return 0

    records = [
        (
            a["source"],
            a.get("portal_tier", "general"),
            a["url"],
            a.get("title"),
            a.get("body"),
            a.get("category"),
            a.get("published_at"),
        )
        for a in articles
    ]

    conn = get_connection(db_config)
    try:
        with conn:
            with conn.cursor() as cur:
                execute_values(cur, _INSERT_SQL, records)
                inserted = cur.rowcount
        print(f"[DB] Inserted {inserted} new articles.")
        return inserted
    finally:
        conn.close()


def write_market_snapshot(rows: list[dict[str, Any]], db_config: DatabaseConfig) -> int:
    """Stores one live-price row per symbol for this fetch cycle (append-only history)."""
    if not rows:
        return 0

    records = [
        (
            r["symbol"],
            r.get("ltp"),
            r.get("change_percent"),
            r.get("open_price"),
            r.get("high_price"),
            r.get("low_price"),
            r.get("volume"),
            r["fetched_at"],
        )
        for r in rows
    ]

    conn = get_connection(db_config)
    try:
        with conn:
            with conn.cursor() as cur:
                execute_values(cur, _INSERT_MARKET_SQL, records)
                inserted = cur.rowcount
        print(f"[DB] Inserted {inserted} live market rows.")
        return inserted
    finally:
        conn.close()
