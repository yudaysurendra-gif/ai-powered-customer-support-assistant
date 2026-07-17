from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_agent, get_current_user
from app.core.database import get_db
from app.models.knowledge_base import KnowledgeBaseArticle
from app.models.user import User
from app.services.knowledge_base import get_knowledge_base_service

router = APIRouter(prefix="/api/v1/knowledge-base", tags=["knowledge-base"])
kb_service = get_knowledge_base_service()


class ArticleCreate(BaseModel):
    title: str
    category: str = "general"
    content: str
    keywords: str = ""


class ArticleOut(BaseModel):
    id: str
    title: str
    category: str
    content: str
    keywords: str

    class Config:
        from_attributes = True


@router.get("", response_model=list[ArticleOut])
def list_articles(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(KnowledgeBaseArticle).all()


@router.get("/search", response_model=list[ArticleOut])
def search_articles(q: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    results = kb_service.search(db, q)
    ids = [r.article_id for r in results]
    if not ids:
        return []
    articles = db.query(KnowledgeBaseArticle).filter(KnowledgeBaseArticle.id.in_(ids)).all()
    order = {aid: i for i, aid in enumerate(ids)}
    return sorted(articles, key=lambda a: order[a.id])


@router.post("", response_model=ArticleOut, status_code=status.HTTP_201_CREATED)
def create_article(payload: ArticleCreate, db: Session = Depends(get_db), agent: User = Depends(get_current_agent)):
    article = KnowledgeBaseArticle(**payload.model_dump())
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(article_id: str, db: Session = Depends(get_db), agent: User = Depends(get_current_agent)):
    article = db.query(KnowledgeBaseArticle).filter(KnowledgeBaseArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    db.delete(article)
    db.commit()
