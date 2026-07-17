"""
Lightweight intent classification service.

Trains a TF-IDF + Multinomial Naive Bayes pipeline on a small bundled
labeled dataset (data/intents.json) at process startup. This keeps the
service fully self-contained and offline-capable, while remaining easy
to swap out for a larger dataset or a hosted LLM classifier later.
"""
import json
import os
from dataclasses import dataclass
from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

INTENTS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "intents.json")


@dataclass
class IntentPrediction:
    intent: str
    confidence: float
    all_scores: dict[str, float]


class IntentClassifier:
    def __init__(self, dataset_path: str = INTENTS_PATH):
        self.dataset_path = dataset_path
        self.pipeline: Pipeline | None = None
        self.labels: list[str] = []
        self._train()

    def _load_dataset(self) -> tuple[list[str], list[str]]:
        with open(self.dataset_path, encoding="utf-8") as f:
            data = json.load(f)
        texts: list[str] = []
        labels: list[str] = []
        for intent, examples in data.items():
            for example in examples:
                texts.append(example)
                labels.append(intent)
        return texts, labels

    def _train(self) -> None:
        texts, labels = self._load_dataset()
        self.labels = sorted(set(labels))
        self.pipeline = Pipeline(
            [
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, stop_words="english")),
                ("clf", MultinomialNB(alpha=0.3)),
            ]
        )
        self.pipeline.fit(texts, labels)

    def predict(self, text: str) -> IntentPrediction:
        if not self.pipeline:
            raise RuntimeError("Classifier has not been trained")

        probs = self.pipeline.predict_proba([text])[0]
        classes = self.pipeline.classes_
        scores = dict(zip(classes, (float(p) for p in probs)))
        best_intent = max(scores, key=scores.get)
        return IntentPrediction(intent=best_intent, confidence=scores[best_intent], all_scores=scores)

    def retrain(self, dataset_path: str | None = None) -> None:
        if dataset_path:
            self.dataset_path = dataset_path
        self._train()


@lru_cache
def get_intent_classifier() -> IntentClassifier:
    return IntentClassifier()
