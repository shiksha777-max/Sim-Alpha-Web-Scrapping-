"""
Sentiment analysis using cardiffnlp/twitter-xlm-roberta-base-sentiment.
Handles Nepali (Devanagari) + English mixed text.
Runs on CPU — fits comfortably in 4 GB RAM.
"""
from __future__ import annotations

from typing import Any

from transformers import pipeline


_LABEL_MAP = {
    "LABEL_0": "negative",
    "LABEL_1": "neutral",
    "LABEL_2": "positive",
    # Some versions of the model expose these directly
    "negative": "negative",
    "neutral": "neutral",
    "positive": "positive",
}


class SentimentAnalyzer:
    def __init__(self, model_name: str, batch_size: int = 16) -> None:
        print(f"[ML] Loading sentiment model: {model_name}")
        self._pipe = pipeline(
            "text-classification",
            model=model_name,
            tokenizer=model_name,
            device=-1,          # CPU
            batch_size=batch_size,
            truncation=True,
            max_length=512,
        )
        self._batch_size = batch_size
        print("[ML] Sentiment model ready.")

    def analyze(self, articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        articles: list of { id, title, body }
        Returns: list of { id, sentiment, score }
        """
        if not articles:
            return []

        # Combine title + first 400 chars of body for inference
        texts = [
            (a.get("title") or "") + " " + (a.get("body") or "")[:400]
            for a in articles
        ]

        raw_outputs = self._pipe(texts, batch_size=self._batch_size)

        results: list[dict[str, Any]] = []
        for article, output in zip(articles, raw_outputs):
            raw_label = output.get("label", "neutral")
            sentiment = _LABEL_MAP.get(raw_label, "neutral")
            score = round(float(output.get("score", 0.0)), 6)
            results.append({
                "id": article["id"],
                "sentiment": sentiment,
                "score": score,
            })

        return results
