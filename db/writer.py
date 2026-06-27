from __future__ import annotations
from typing import Any
from psycopg2.extras import execute_values
from db.connection import get_connection
from config import DatabaseConfig

_INSERT_SQL = """
INSERT INTO news_articles (source, url, title, body, category, published_at)
VALUES %s
ON CONFLICT (url) DO NOTHING
"""

_UPDATE_SENTIMENT_SQL = """
UPDATE news_articles
SET sentiment = %s, sentiment_score = %s, analyzed = TRUE
WHERE id = %s
"""


def write_articles(articles: list[dict[str, Any]], db_config: DatabaseConfig) -> int:
    """Bulk insert scraped articles. Returns count of newly inserted rows."""
    if not articles:
        return 0

    records = [
        (
            a["source"],
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


def fetch_unanalyzed(db_config: DatabaseConfig, limit: int = 200) -> list[dict[str, Any]]:
    """Fetch articles not yet sentiment-analyzed."""
    conn = get_connection(db_config)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, title, body FROM news_articles WHERE analyzed = FALSE LIMIT %s",
                (limit,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return [{"id": r[0], "title": r[1] or "", "body": r[2] or ""} for r in rows]


def update_sentiments(results: list[dict[str, Any]], db_config: DatabaseConfig) -> None:
    """Batch update sentiment labels and scores."""
    if not results:
        return

    conn = get_connection(db_config)
    try:
        with conn:
            with conn.cursor() as cur:
                for r in results:
                    cur.execute(_UPDATE_SENTIMENT_SQL, (r["sentiment"], r["score"], r["id"]))
        print(f"[DB] Updated sentiment for {len(results)} articles.")
    finally:
        conn.close()
