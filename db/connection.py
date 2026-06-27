import time
import psycopg2
from config import DatabaseConfig

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS nepse_news (
    id              SERIAL PRIMARY KEY,
    source          TEXT NOT NULL,
    portal_tier     TEXT NOT NULL,           -- 'finance' or 'general'
    url             TEXT UNIQUE NOT NULL,
    title           TEXT,
    body            TEXT,
    category        TEXT,
    published_at    TIMESTAMP,
    scraped_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_nepse_news_scraped_at  ON nepse_news (scraped_at);
CREATE INDEX IF NOT EXISTS idx_nepse_news_source       ON nepse_news (source);
"""

_CREATE_MARKET_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS nepse_market_live (
    id              SERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    ltp             DOUBLE PRECISION,        -- last traded price
    change_percent  DOUBLE PRECISION,
    open_price      DOUBLE PRECISION,
    high_price      DOUBLE PRECISION,
    low_price       DOUBLE PRECISION,
    volume          BIGINT,
    fetched_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_market_live_symbol      ON nepse_market_live (symbol);
CREATE INDEX IF NOT EXISTS idx_market_live_fetched_at  ON nepse_market_live (fetched_at);
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
                    cur.execute(_CREATE_MARKET_TABLE_SQL)
            conn.close()
            print("[DB] nepse_news + nepse_market_live tables ready.")
            return
        except Exception as e:
            if attempt == max_retries:
                raise
            print(f"[DB] Connection attempt {attempt}/{max_retries} failed: {e}. Retrying in {retry_delay}s...")
            time.sleep(retry_delay)
