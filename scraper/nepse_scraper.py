"""
NEPSE Live Market Index Scraper
Scrapes from merolagani.com:
  - Main NEPSE index
  - Selected sector indices (Banking, Hydropower, Finance, etc.)


 Market hours: Monday to Friday, 11:00 AM to 3:00 PM NST
"""
from __future__ import annotations

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

SELECTED_SECTORS = {
    "banking",
    "development bank",
    "finance",
    "hydropower",
    "insurance",
    "microfinance",
    "manufacturing",
    "investment",
    "hotel",
    "trading",
}


def _get(url: str, timeout: int = 15) -> BeautifulSoup | None:
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=timeout)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"[NEPSE Scraper] Failed to fetch {url}: {e}")
        return None


def _to_float(text: str) -> float | None:
    try:
        return float(text.strip().replace(",", "").replace("%", ""))
    except Exception:
        return None


def scrape_nepse_main_index(timeout: int = 15) -> dict[str, Any] | None:
    """Scrapes the main NEPSE index value from merolagani."""
    soup = _get("https://merolagani.com/LatestMarket.aspx", timeout)
    if soup is None:
        return None

    try:
        # Try multiple possible selectors
        index_tag = (
            soup.select_one("#ctl00_ContentPlaceHolder1_LiveMarket1_lblIndex") or
            soup.select_one(".nepse-index") or
            soup.select_one("[id*='lblIndex']")
        )
        change_tag = (
            soup.select_one("#ctl00_ContentPlaceHolder1_LiveMarket1_lblChange") or
            soup.select_one("[id*='lblChange']")
        )
        pct_tag = (
            soup.select_one("#ctl00_ContentPlaceHolder1_LiveMarket1_lblPercentChange") or
            soup.select_one("[id*='lblPercentChange']")
        )

        result = {
            "index": "NEPSE",
            "value": _to_float(index_tag.get_text()) if index_tag else None,
            "change": _to_float(change_tag.get_text()) if change_tag else None,
            "percent_change": _to_float(pct_tag.get_text()) if pct_tag else None,
            "scraped_at": datetime.now().isoformat(),
        }
        print(f"[NEPSE Scraper] Main index: {result['value']}")
        return result
    except Exception as e:
        print(f"[NEPSE Scraper] Error parsing main index: {e}")
        return None


def scrape_sector_indices(timeout: int = 15) -> list[dict[str, Any]]:
    """Scrapes sector-wise sub-indices from merolagani."""
    soup = _get("https://merolagani.com/Indices.aspx", timeout)
    if soup is None:
        return []

    results: list[dict[str, Any]] = []
    scraped_at = datetime.now().isoformat()

    try:
        # Find all tables and look for the indices table
        tables = soup.select("table")
        for table in tables:
            rows = table.select("tr")
            for row in rows[1:]:
                cols = row.select("td")
                if len(cols) < 2:
                    continue

                sector_name = cols[0].get_text().strip()
                if not sector_name:
                    continue

                # Only collect selected sectors
                matched = any(s in sector_name.lower() for s in SELECTED_SECTORS)
                if not matched:
                    continue

                value = _to_float(cols[1].get_text()) if len(cols) > 1 else None
                change = _to_float(cols[2].get_text()) if len(cols) > 2 else None
                pct = _to_float(cols[3].get_text()) if len(cols) > 3 else None

                results.append({
                    "index": sector_name,
                    "value": value,
                    "change": change,
                    "percent_change": pct,
                    "scraped_at": scraped_at,
                })

        print(f"[NEPSE Scraper] Sector indices: {len(results)} sectors scraped.")
        return results

    except Exception as e:
        print(f"[NEPSE Scraper] Error parsing sector indices: {e}")
        return []


def scrape_all_nepse_data(timeout: int = 15) -> dict[str, Any]:
    """Scrapes both NEPSE main index and selected sector indices."""
    main_index = scrape_nepse_main_index(timeout)
    sector_indices = scrape_sector_indices(timeout)

    return {
        "scraped_at": datetime.now().isoformat(),
        "nepse_index": main_index,
        "sector_indices": sector_indices,
    }
