"""
Scrapers for Nepali news portals.
Each scraper returns a list of article dicts:
  { source, url, title, body, category, published_at }
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def _get(url: str, timeout: int = 15) -> BeautifulSoup | None:
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=timeout)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"[Scraper] Failed to fetch {url}: {e}")
        return None


def _clean(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# Onlinekhabar
# ---------------------------------------------------------------------------

def scrape_onlinekhabar(timeout: int = 15, max_articles: int = 50) -> list[dict[str, Any]]:
    base_url = "https://www.onlinekhabar.com"
    soup = _get(base_url, timeout)
    if soup is None:
        return []

    articles: list[dict[str, Any]] = []
    seen: set[str] = set()

    for a_tag in soup.select("a[href]"):
        href = a_tag["href"]
        if not href.startswith(base_url):
            href = base_url + href if href.startswith("/") else None
        if not href or href in seen:
            continue
        # Onlinekhabar article URLs contain a numeric ID
        if not re.search(r"/\d{6,}/", href):
            continue
        seen.add(href)

        detail = _get(href, timeout)
        if detail is None:
            continue

        title_tag = detail.select_one("h1.ok18-single-post-content-title, h1")
        body_parts = detail.select("div.ok18-single-post-content-section p")
        category_tag = detail.select_one("a.ok18-breadcrumb-link, .post-category a")
        time_tag = detail.select_one("time[datetime]")

        title = _clean(title_tag.get_text() if title_tag else "")
        body = _clean(" ".join(p.get_text() for p in body_parts))
        category = _clean(category_tag.get_text() if category_tag else "")
        published_at = None
        if time_tag and time_tag.get("datetime"):
            try:
                published_at = datetime.fromisoformat(time_tag["datetime"].replace("Z", "+00:00"))
            except Exception:
                pass

        if not title:
            continue

        articles.append({
            "source": "onlinekhabar",
            "url": href,
            "title": title,
            "body": body[:3000],
            "category": category,
            "published_at": published_at,
        })

        if len(articles) >= max_articles:
            break

    print(f"[Scraper] onlinekhabar: {len(articles)} articles")
    return articles


# ---------------------------------------------------------------------------
# Setopati
# ---------------------------------------------------------------------------

def scrape_setopati(timeout: int = 15, max_articles: int = 50) -> list[dict[str, Any]]:
    base_url = "https://www.setopati.com"
    soup = _get(base_url, timeout)
    if soup is None:
        return []

    articles: list[dict[str, Any]] = []
    seen: set[str] = set()

    for a_tag in soup.select("a[href]"):
        href = a_tag.get("href", "")
        if not href.startswith(base_url):
            href = base_url + href if href.startswith("/") else ""
        if not href or href in seen:
            continue
        # Setopati articles: /category/slug/id pattern
        if not re.search(r"/\d+$", href):
            continue
        seen.add(href)

        detail = _get(href, timeout)
        if detail is None:
            continue

        title_tag = detail.select_one("h1.news-title, h1")
        body_parts = detail.select("div.news-description p, div.content-description p")
        category_tag = detail.select_one("div.breadcrumb a:nth-child(2), .category-name")
        time_tag = detail.select_one("time[datetime], span.date-time")

        title = _clean(title_tag.get_text() if title_tag else "")
        body = _clean(" ".join(p.get_text() for p in body_parts))
        category = _clean(category_tag.get_text() if category_tag else "")
        published_at = None
        if time_tag and time_tag.get("datetime"):
            try:
                published_at = datetime.fromisoformat(time_tag["datetime"].replace("Z", "+00:00"))
            except Exception:
                pass

        if not title:
            continue

        articles.append({
            "source": "setopati",
            "url": href,
            "title": title,
            "body": body[:3000],
            "category": category,
            "published_at": published_at,
        })

        if len(articles) >= max_articles:
            break

    print(f"[Scraper] setopati: {len(articles)} articles")
    return articles


# ---------------------------------------------------------------------------
# Ratopati
# ---------------------------------------------------------------------------

def scrape_ratopati(timeout: int = 15, max_articles: int = 50) -> list[dict[str, Any]]:
    base_url = "https://ratopati.com"
    soup = _get(base_url, timeout)
    if soup is None:
        return []

    articles: list[dict[str, Any]] = []
    seen: set[str] = set()

    for a_tag in soup.select("a[href]"):
        href = a_tag.get("href", "")
        if not href.startswith(base_url):
            href = base_url + href if href.startswith("/") else ""
        if not href or href in seen:
            continue
        if not re.search(r"/story/\d+", href):
            continue
        seen.add(href)

        detail = _get(href, timeout)
        if detail is None:
            continue

        title_tag = detail.select_one("h1.news-title, h1")
        body_parts = detail.select("div.news-body p, div.story-content p")
        category_tag = detail.select_one("ul.breadcrumb li:nth-child(2) a, .category a")
        time_tag = detail.select_one("time[datetime], .published-time")

        title = _clean(title_tag.get_text() if title_tag else "")
        body = _clean(" ".join(p.get_text() for p in body_parts))
        category = _clean(category_tag.get_text() if category_tag else "")
        published_at = None
        if time_tag and time_tag.get("datetime"):
            try:
                published_at = datetime.fromisoformat(time_tag["datetime"].replace("Z", "+00:00"))
            except Exception:
                pass

        if not title:
            continue

        articles.append({
            "source": "ratopati",
            "url": href,
            "title": title,
            "body": body[:3000],
            "category": category,
            "published_at": published_at,
        })

        if len(articles) >= max_articles:
            break

    print(f"[Scraper] ratopati: {len(articles)} articles")
    return articles


# ---------------------------------------------------------------------------
# Ekantipur
# ---------------------------------------------------------------------------

def scrape_ekantipur(timeout: int = 15, max_articles: int = 50) -> list[dict[str, Any]]:
    base_url = "https://ekantipur.com"
    soup = _get(base_url, timeout)
    if soup is None:
        return []

    articles: list[dict[str, Any]] = []
    seen: set[str] = set()

    for a_tag in soup.select("a[href]"):
        href = a_tag.get("href", "")
        if not href.startswith(base_url):
            href = base_url + href if href.startswith("/") else ""
        if not href or href in seen:
            continue
        # Ekantipur: /np/news/ or /news/ in path
        if "/news/" not in href:
            continue
        seen.add(href)

        detail = _get(href, timeout)
        if detail is None:
            continue

        title_tag = detail.select_one("h1.heading, h1")
        body_parts = detail.select("div.current-news-block p, article p")
        category_tag = detail.select_one("ul.breadcrumb li:nth-child(2) a, .section-title")
        time_tag = detail.select_one("time[datetime]")

        title = _clean(title_tag.get_text() if title_tag else "")
        body = _clean(" ".join(p.get_text() for p in body_parts))
        category = _clean(category_tag.get_text() if category_tag else "")
        published_at = None
        if time_tag and time_tag.get("datetime"):
            try:
                published_at = datetime.fromisoformat(time_tag["datetime"].replace("Z", "+00:00"))
            except Exception:
                pass

        if not title:
            continue

        articles.append({
            "source": "ekantipur",
            "url": href,
            "title": title,
            "body": body[:3000],
            "category": category,
            "published_at": published_at,
        })

        if len(articles) >= max_articles:
            break

    print(f"[Scraper] ekantipur: {len(articles)} articles")
    return articles


# ---------------------------------------------------------------------------
# Registry — add more portals here
# ---------------------------------------------------------------------------

ALL_SCRAPERS = [
    scrape_onlinekhabar,
    scrape_setopati,
    scrape_ratopati,
    scrape_ekantipur,
]


def scrape_all(timeout: int = 15, max_articles: int = 50) -> list[dict]:
    results = []
    for scraper_fn in ALL_SCRAPERS:
        try:
            results.extend(scraper_fn(timeout=timeout, max_articles=max_articles))
        except Exception as e:
            print(f"[Scraper] {scraper_fn.__name__} failed: {e}")
    print(f"[Scraper] Total articles collected: {len(results)}")
    return results
