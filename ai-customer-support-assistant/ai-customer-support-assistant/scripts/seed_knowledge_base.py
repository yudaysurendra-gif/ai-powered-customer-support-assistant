"""
Seed the knowledge base with a starter set of support articles.

Usage:
    python -m scripts.seed_knowledge_base
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models.knowledge_base import KnowledgeBaseArticle  # noqa: E402

SEED_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_base_seed.json")


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing_count = db.query(KnowledgeBaseArticle).count()
        if existing_count > 0:
            print(f"Knowledge base already has {existing_count} articles. Skipping seed.")
            return

        with open(SEED_PATH, encoding="utf-8") as f:
            articles = json.load(f)

        for item in articles:
            db.add(KnowledgeBaseArticle(**item))

        db.commit()
        print(f"Seeded {len(articles)} knowledge base articles.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
