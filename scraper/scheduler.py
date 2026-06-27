from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, time as dtime  # ← ADD THIS
import pytz                                    # ← ADD THIS

from config import load_app_config
from db import write_articles, write_nepse_index
from scraper.scrapers import scrape_all
from scraper.nepse_scraper import scrape_all_nepse_data


def _is_market_open() -> bool:
    nst = pytz.timezone("Asia/Kathmandu")
    now = datetime.now(nst)
    if now.weekday() > 4:
        return False
    return dtime(11, 0) <= now.time() <= dtime(15, 0)


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

    # Step 3 — NEPSE index only during market hours  ← CHANGED
    if _is_market_open():
        nepse_data = scrape_all_nepse_data(timeout=config.scraper.request_timeout)
        write_nepse_index(nepse_data, config.database)
    else:
        print("[Pipeline] Market closed — skipping NEPSE index scrape.")

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
