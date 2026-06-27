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
    max_articles_per_portal: int


@dataclass(frozen=True)
class MLConfig:
    model_name: str
    batch_size: int


@dataclass(frozen=True)
class MarketConfig:
    interval_minutes: int
    trading_start_hour: int
    trading_end_hour: int
    trading_days: tuple[int, ...]   # Python weekday(): 0=Monday ... 6=Sunday
    timezone: str
    verify_ssl: bool


@dataclass(frozen=True)
class AppConfig:
    database: DatabaseConfig
    scraper: ScraperConfig
    ml: MLConfig
    market: MarketConfig


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
            max_articles_per_portal=int(os.getenv("SCRAPER_MAX_ARTICLES_PER_PORTAL", "20")),
        ),
        ml=MLConfig(
            model_name=os.getenv(
                "SENTIMENT_MODEL",
                "cardiffnlp/twitter-xlm-roberta-base-sentiment",
            ),
            batch_size=int(os.getenv("SENTIMENT_BATCH_SIZE", "16")),
        ),
        market=MarketConfig(
            interval_minutes=int(os.getenv("MARKET_FETCH_INTERVAL_MINUTES", "2")),
            trading_start_hour=int(os.getenv("MARKET_TRADING_START_HOUR", "11")),
            trading_end_hour=int(os.getenv("MARKET_TRADING_END_HOUR", "15")),
            # 0=Mon,1=Tue,2=Wed,3=Thu,4=Fri,5=Sat,6=Sun
            # NEPSE moved to a Mon-Fri trading week (closed Sat/Sun) after
            # Nepal's government adopted a two-day weekend - this matches
            # the current schedule.
            trading_days=tuple(
                int(d) for d in os.getenv("MARKET_TRADING_DAYS", "0,1,2,3,4").split(",")
            ),
            timezone=os.getenv("MARKET_TIMEZONE", "Asia/Kathmandu"),
            verify_ssl=os.getenv("MARKET_VERIFY_SSL", "false").lower() == "true",
        ),
    )
