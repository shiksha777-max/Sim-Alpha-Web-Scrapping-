import time
import psycopg2
from config import DatabaseConfig

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS news_articles (
    id              SERIAL PRIMARY KEY,
    source          TEXT NOT NULL,
    url             TEXT UNIQUE NOT NULL,
    title           TEXT,
    body            TEXT,
    category        TEXT,
    published_at    TIMESTAMP,
    scraped_at      TIMESTAMP DEFAULT NOW(),
    sentiment       TEXT,
    sentiment_score DOUBLE PRECISION,
    analyzed        BOOLEAN DEFAULT FALSE
);
"""


def get_connection(db_config: DatabaseConfig) -> psycopg2.extensions.connection:
    return psycopg2.connect(
        host=db_config.host,
        port=db_config.port,
        dbname=db_config.dbname,
        user=db_config.user,
        password=db_config.password,
    )


def ensure_table_exists(db_config: DatabaseConfig, max_retries: int = 12, retry_delay: int = 5) -> None:
    for attempt in range(1, max_retries + 1):
        try:
            conn = get_connection(db_config)
            with conn:
                with conn.cursor() as cur:
                    cur.execute(_CREATE_TABLE_SQL)
            conn.close()
            print("[DB] news_articles table ready.")
            return
        except Exception as e:
            if attempt == max_retries:
                raise
            print(f"[DB] Connection attempt {attempt}/{max_retries} failed: {e}. Retrying in {retry_delay}s...")
            time.sleep(retry_delay)
