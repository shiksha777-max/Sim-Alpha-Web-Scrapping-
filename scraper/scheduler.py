"""
Runs scrape + sentiment analysis on a fixed interval using APScheduler.
"""
from __future__ import annotations

from apscheduler.schedulers.blocking import BlockingScheduler

from config import load_app_config
from db import ensure_table_exists, fetch_unanalyzed, update_sentiments, write_articles
from ml.sentiment import SentimentAnalyzer
from scraper.scrapers import scrape_all


def run_pipeline() -> None:
    config = load_app_config()
    db_config = config.database
    scraper_config = config.scraper
    ml_config = config.ml

    print("[Pipeline] Starting scrape run...")

    # 1. Scrape
    articles = scrape_all(
        timeout=scraper_config.request_timeout,
        max_articles=scraper_config.max_articles_per_run,
    )

    # 2. Persist raw articles
    write_articles(articles, db_config)

    # 3. Sentiment analysis on unanalyzed rows
    unanalyzed = fetch_unanalyzed(db_config, limit=200)
    if not unanalyzed:
        print("[Pipeline] No new articles to analyze.")
        return

    analyzer = SentimentAnalyzer(ml_config.model_name, batch_size=ml_config.batch_size)
    results = analyzer.analyze(unanalyzed)
    update_sentiments(results, db_config)

    print(f"[Pipeline] Done. Analyzed {len(results)} articles.")


def start_scheduler(interval_minutes: int) -> None:
    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_pipeline,
        trigger="interval",
        minutes=interval_minutes,
        id="news_pipeline",
        max_instances=1,  # Never overlap runs
    )
    print(f"[Scheduler] Running every {interval_minutes} minutes. First run now...")
    run_pipeline()  # Run immediately on startup
    scheduler.start()
