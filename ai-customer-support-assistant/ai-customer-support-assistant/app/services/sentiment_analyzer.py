"""
Sentiment analysis service using VADER (Valence Aware Dictionary and
sEntiment Reasoner) — a lexicon/rule-based model well suited to short,
informal customer support text and fully offline after install.
"""
from dataclasses import dataclass
from functools import lru_cache

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


@dataclass
class SentimentResult:
    compound: float  # -1 (very negative) to +1 (very positive)
    label: str  # negative | neutral | positive


class SentimentAnalyzer:
    def __init__(self):
        self._analyzer = SentimentIntensityAnalyzer()

    def analyze(self, text: str) -> SentimentResult:
        scores = self._analyzer.polarity_scores(text)
        compound = scores["compound"]
        if compound <= -0.05:
            label = "negative"
        elif compound >= 0.05:
            label = "positive"
        else:
            label = "neutral"
        return SentimentResult(compound=compound, label=label)


@lru_cache
def get_sentiment_analyzer() -> SentimentAnalyzer:
    return SentimentAnalyzer()
