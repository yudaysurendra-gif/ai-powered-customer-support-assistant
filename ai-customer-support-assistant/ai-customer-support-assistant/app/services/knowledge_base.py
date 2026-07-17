"""
Knowledge base retrieval using TF-IDF cosine similarity over article
titles + content + keywords. Falls back gracefully to an empty result
set if the knowledge base is empty.
"""
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from app.models.knowledge_base import KnowledgeBaseArticle


@dataclass
class KBSearchResult:
    article_id: str
    title: str
    content: str
    category: str
    score: float


class KnowledgeBaseService:
    def search(self, db: Session, query: str, top_k: int = 3, min_score: float = 0.08) -> list[KBSearchResult]:
        articles = db.query(KnowledgeBaseArticle).all()
        if not articles:
            return []

        corpus = [f"{a.title} {a.content} {a.keywords}" for a in articles]
        vectorizer = TfidfVectorizer(stop_words="english")
        try:
            tfidf_matrix = vectorizer.fit_transform(corpus + [query])
        except ValueError:
            # Empty vocabulary (e.g. query is all stopwords) — no matches.
            return []

        query_vec = tfidf_matrix[-1]
        doc_vecs = tfidf_matrix[:-1]
        similarities = cosine_similarity(query_vec, doc_vecs)[0]

        ranked = sorted(zip(articles, similarities), key=lambda pair: pair[1], reverse=True)
        results = [
            KBSearchResult(
                article_id=article.id,
                title=article.title,
                content=article.content,
                category=article.category,
                score=float(score),
            )
            for article, score in ranked[:top_k]
            if score >= min_score
        ]
        return results


def get_knowledge_base_service() -> KnowledgeBaseService:
    return KnowledgeBaseService()
