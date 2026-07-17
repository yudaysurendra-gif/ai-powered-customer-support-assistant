from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, knowledge_base, tickets
from app.core.config import settings
from app.core.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered customer support assistant with intent classification, "
    "sentiment-aware escalation, and knowledge-base retrieval.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tickets.router)
app.include_router(knowledge_base.router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}


@app.get("/", tags=["health"])
def root():
    return {"message": f"{settings.APP_NAME} is running. See /docs for API documentation."}
