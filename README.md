# Nepali News Sentiment Pipeline

A real-time news sentiment analysis pipeline that scrapes 20 Nepali news portals every 30 minutes and classifies each article as positive, neutral, or negative using a multilingual AI model.

## How to Deploy

1. Clone the repo
2. Copy .env.example to .env and fill in database credentials
3. Run: docker-compose up --build

## API

GET /sentiment-summary?hours=24&tier=finance

## Portals Scraped

Merolagani, Sharesansar, Nepsealpha, NepseKhabar, Nepali Paisa, Karobar Daily, Arthik Abhiyan, Biznews Nepal, Stock Nepali, NEPSE Trading, Onlinekhabar, Setopati, Ratopati, Ekantipur, Nagarik News, Himalayan Times, MyRepublica, Republica, Annapurna Post, Nepal Live
