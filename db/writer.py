from __future__ import annotations
from typing import Any
from psycopg2.extras import execute_values
from db.connection import get_connection
from config import DatabaseConfig

_INSERT_NEWS_SQL = """
INSERT INTO nepse_news (source, portal_tier, url, title, body, category, published_at)
VALUES %s
ON CONFLICT (url) DO NOTHING
"""

_INSERT_INDEX_SQL = """
INSERT INTO nepse_index (index_name, value, change, percent_change)
VALUES %s
"""


def write_articles(articles: list[dict[str, Any]], db_config: DatabaseConfig) -> int:
    """Save scraped news articles to DB. Skips duplicates by URL."""
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
                execute_values(cur, _INSERT_NEWS_SQL, records)
                inserted = cur.rowcount
        print(f"[DB] Inserted {inserted} new articles.")
        return inserted
    finally:
        conn.close()


def write_nepse_index(index_data: dict[str, Any], db_config: DatabaseConfig) -> None:
    """Save NEPSE main index + sector indices to DB."""
    records = []

    # Main NEPSE index
    main = index_data.get("nepse_index")
    if main and main.get("value"):
        records.append((
            main.get("index", "NEPSE"),
            main.get("value"),
            main.get("change"),
            main.get("percent_change"),
        ))

    # Sector indices
    for sector in index_data.get("sector_indices", []):
        if sector.get("value"):
            records.append((
                sector.get("index"),
                sector.get("value"),
                sector.get("change"),
                sector.get("percent_change"),
            ))

    if not records:
        print("[DB] No NEPSE index data to save.")
        return

    conn = get_connection(db_config)
    try:
        with conn:
            with conn.cursor() as cur:
                execute_values(cur, _INSERT_INDEX_SQL, records)
        print(f"[DB] Saved {len(records)} NEPSE index records.")
    finally:
        conn.close()
