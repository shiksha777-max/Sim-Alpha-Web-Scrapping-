from apscheduler.schedulers.blocking import BlockingScheduler

from config import load_app_config
from db import write_articles, write_market_snapshot
from market import fetch_live_market, is_trading_window
from scraper.scrapers import scrape_all


def run_pipeline() -> None:
    config = load_app_config()

    print("\n" + "=" * 60)
    print("[Pipeline] Starting scrape run...")
    print("=" * 60)

    articles = scrape_all(
        timeout=config.scraper.request_timeout,
        max_articles_per_portal=config.scraper.max_articles_per_portal,
    )

    inserted = write_articles(articles, config.database)
    print(f"[Pipeline] Run complete. Scraped {len(articles)} articles, stored {inserted} new.")


def run_market_pipeline() -> None:
    """
    Pulls a live NEPSE price snapshot.

    Only fetches inside the configured trading window (default: Mon-Fri,
    11:00-15:00 Asia/Kathmandu - see MARKET_* vars in .env) so we don't
    hit NEPSE outside trading hours for nothing.
    """
    config = load_app_config()

    if not is_trading_window(config.market):
        print("[Market] Outside trading window, skipping fetch.")
        return

    try:
        snapshot = fetch_live_market(verify_ssl=config.market.verify_ssl)
    except Exception as e:
        print(f"[Market] Fetch failed: {e}")
        return

    if not snapshot["market_open"]:
        print("[Market] NEPSE reports market closed, skipping write.")
        return

    inserted = write_market_snapshot(snapshot["rows"], config.database)
    print(f"[Market] Stored {inserted} live price rows.")


def start_scheduler(interval_minutes: int) -> None:
    config = load_app_config()
    scheduler = BlockingScheduler()

    scheduler.add_job(
        run_pipeline,
        trigger="interval",
        minutes=interval_minutes,
        id="nepse_news_pipeline",
        max_instances=1,
    )

    scheduler.add_job(
        run_market_pipeline,
        trigger="interval",
        minutes=config.market.interval_minutes,
        id="nepse_market_pipeline",
        max_instances=1,
    )

    print(f"[Scheduler] News pipeline will run every {interval_minutes} minutes.")
    print(
        f"[Scheduler] Market pipeline will run every {config.market.interval_minutes} minutes "
        f"(active days={config.market.trading_days}, "
        f"{config.market.trading_start_hour}:00-{config.market.trading_end_hour}:00 "
        f"{config.market.timezone})."
    )
    print("[Scheduler] Running first news pass now...")
    run_pipeline()
    run_market_pipeline()
    scheduler.start()
