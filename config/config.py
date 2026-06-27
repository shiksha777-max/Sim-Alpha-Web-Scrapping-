import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    dbname: str
    user: str
    password: str


@dataclass(frozen=True)
class ScraperConfig:
    interval_minutes: int
    request_timeout: int
    max_articles_per_run: int


@dataclass(frozen=True)
class MLConfig:
    model_name: str
    batch_size: int


@dataclass(frozen=True)
class AppConfig:
    database: DatabaseConfig
    scraper: ScraperConfig
    ml: MLConfig


def load_app_config() -> AppConfig:
    return AppConfig(
        database=DatabaseConfig(
            host=os.getenv("POSTGRES_HOST", "db"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            dbname=os.getenv("POSTGRES_DB", "wikipedia"),
            user=os.getenv("POSTGRES_USER", "superset"),
            password=os.getenv("POSTGRES_PASSWORD", "superset_pass"),
        ),
        scraper=ScraperConfig(
            interval_minutes=int(os.getenv("SCRAPER_INTERVAL_MINUTES", "30")),
            request_timeout=int(os.getenv("SCRAPER_REQUEST_TIMEOUT", "15")),
            max_articles_per_run=int(os.getenv("SCRAPER_MAX_ARTICLES", "50")),
        ),
        ml=MLConfig(
            model_name=os.getenv(
                "SENTIMENT_MODEL",
                "cardiffnlp/twitter-xlm-roberta-base-sentiment",
            ),
            batch_size=int(os.getenv("SENTIMENT_BATCH_SIZE", "16")),
        ),
    )
