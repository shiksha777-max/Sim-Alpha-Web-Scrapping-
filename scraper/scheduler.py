from apscheduler.schedulers.blocking import BlockingScheduler

from config import load_app_config
from db import write_articles, write_nepse_index
from scraper.scrapers import scrape_all
from scraper.nepse_scraper import scrape_all_nepse_data


def run_pipeline() -> None:
    config = load_app_config()

    print("\n" + "=" * 60)
    print("[Pipeline] Starting scrape run...")
    print("=" * 60)

    # Step 1 — Scrape 20 news portals
    articles = scrape_all(
        timeout=config.scraper.request_timeout,
        max_articles_per_portal=config.scraper.max_articles_per_portal,
    )

    # Step 2 — Save articles to DB
    write_articles(articles, config.database)

    # Step 3 — Scrape NEPSE index + sector indices
    nepse_data = scrape_all_nepse_data(timeout=config.scraper.request_timeout)

    # Step 4 — Save NEPSE index to DB
    write_nepse_index(nepse_data, config.database)

    print("[Pipeline] Run complete.")


def start_scheduler(interval_minutes: int) -> None:
    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_pipeline,
        trigger="interval",
        minutes=interval_minutes,
        id="nepse_pipeline",
        max_instances=1,
    )
    print(f"[Scheduler] Pipeline will run every {interval_minutes} minutes.")
    print("[Scheduler] Running first pass now...")
    run_pipeline()
    scheduler.start()
