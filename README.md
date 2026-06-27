# Nepali News Sentiment Pipeline

A real-time news sentiment analysis pipeline that scrapes 20 Nepali news portals every 30 minutes and automatically classifies each article as **positive**, **neutral**, or **negative** using a multilingual AI model. Built for analyzing news that impacts the Nepal Stock Exchange (NEPSE).

---

## What This Project Does

1. Every 30 minutes, the system visits 20 Nepali news websites
2. It collects the title, body, category, and publish time of each article
3. It saves everything into a PostgreSQL database
4. An AI model reads each article and labels it as positive, neutral, or negative
5. Results are available through a simple web API

---

## News Portals Scraped

### Tier 1 — Finance and NEPSE Focused
| Portal | Website |
|---|---|
| Merolagani | merolagani.com |
| Sharesansar | sharesansar.com |
| Nepsealpha | nepsealpha.com |
| NepseKhabar | nepsekhabar.com |
| Nepali Paisa | nepalipaisa.com |
| Karobar Daily | karobardaily.com |
| Arthik Abhiyan | arthikabhiyan.com |
| Biznews Nepal | biznessnews.com |
| Stock Nepali | stocknepali.com |
| NEPSE Trading | nepsetrading.com |

### Tier 2 — General News (Politics, Economy, Policy)
| Portal | Website |
|---|---|
| Onlinekhabar | onlinekhabar.com |
| Setopati | setopati.com |
| Ratopati | ratopati.com |
| Ekantipur | ekantipur.com |
| Nagarik News | nagariknews.nagariknetwork.com |
| The Himalayan Times | thehimalayantimes.com |
| MyRepublica | myrepublica.nagariknetwork.com |
| Republica | republica.com |
| Annapurna Post | annapurnapost.com |
| Nepal Live | nepallive.com |

---

## Technology Used

| Technology | Purpose |
|---|---|
| Python 3.11 | Main programming language |
| BeautifulSoup4 | Web scraping — reads and extracts content from news websites |
| XLM-RoBERTa | AI model for sentiment analysis — supports Nepali and English |
| PostgreSQL | Database — stores all articles and sentiment results |
| FastAPI | Web API — exposes sentiment results as an endpoint |
| APScheduler | Scheduler — runs the pipeline automatically every 30 minutes |
| Docker | Deployment — runs the full system on any server with one command |

---

## Project Structure

```
nepali-news-pipeline/
│
├── config/
│   ├── __init__.py
│   └── config.py              # All settings loaded from environment variables
│                              # (database password, scraping interval, model name)
│
├── db/
│   ├── __init__.py
│   ├── connection.py          # Opens and closes PostgreSQL connection
│   │                          # Also creates the news_articles table on first run
│   └── writer.py              # Saves articles to DB, fetches unanalyzed articles,
│                              # updates sentiment results back to DB
│
├── scraper/
│   ├── __init__.py
│   ├── scrapers.py            # 20 individual portal scrapers using BeautifulSoup
│   │                          # Each scraper visits a news site, finds article links,
│   │                          # and extracts title, body, category, published time
│   └── scheduler.py          # Runs the full pipeline every 30 minutes using APScheduler
│
├── ml/
│   ├── __init__.py
│   └── sentiment.py           # Loads XLM-RoBERTa model and analyzes each article
│                              # Labels: positive / neutral / negative
│                              # Works on CPU — no GPU needed
│
├── main.py                    # FastAPI entry point
│                              # Starts the scheduler as background thread on startup
│                              # Exposes GET /sentiment-summary API endpoint
│
├── Dockerfile                 # Instructions to set up the project on any server
│                              # Pre-downloads the AI model at build time
│
├── docker-compose.yml         # Starts the pipeline + PostgreSQL database together
│                              # Sir runs: docker-compose up --build
│
├── requirements.txt           # List of all Python libraries needed
│
├── .env.example               # Template for environment variables
│                              # Copy to .env and fill in database credentials
│
├── .gitignore                 # Files not uploaded to GitHub (passwords, cache, models)
│
└── README.md                  # This file
```

---

## How to Deploy (For Server Setup)

**Step 1 — Clone the repository**
```bash
git clone https://github.com/shiksha777-max/Sim-Alpha-Web-Scrapping-
cd Sim-Alpha-Web-Scrapping-
```

**Step 2 — Create environment file**
```bash
cp .env.example .env
```
Open `.env` and fill in the database credentials for your server.

**Step 3 — Run**
```bash
docker-compose up --build
```

The pipeline starts immediately. It will:
- Create the database table automatically
- Run the first scrape right away
- Then repeat every 30 minutes automatically

---

## API

Once running, the API is available at `http://your-server-ip:8001`

### GET /sentiment-summary
```
GET /sentiment-summary?hours=24&tier=finance
```

Parameters:
- `hours` — how many hours of data to show (default: 24, max: 720)
- `tier` — filter by portal type: `all` / `finance` / `general` (default: all)

Example response:
```json
{
  "window_hours": 24,
  "total_articles_analyzed": 312,
  "overall": {
    "positive": 140,
    "neutral": 98,
    "negative": 74
  },
  "by_source": [
    { "source": "merolagani", "portal_tier": "finance", "positive": 45, "neutral": 20, "negative": 15 },
    { "source": "onlinekhabar", "portal_tier": "general", "positive": 30, "neutral": 25, "negative": 20 }
  ],
  "by_category": [
    { "category": "share market", "positive": 60, "neutral": 30, "negative": 20 }
  ]
}
```

### GET /health
```
GET /health
```
Returns `{"status": "ok"}` if the pipeline is running.

---

## Data Collection Plan

- Scraping interval: every 30 minutes
- Target collection period: minimum 2 weeks
- Expected articles per run: up to 400 (20 portals x 20 articles each)
- Expected total dataset: 20,000 to 30,000 articles over 2 weeks

---

## Authors

Shiksha Bhattarai
Kathmandu University
