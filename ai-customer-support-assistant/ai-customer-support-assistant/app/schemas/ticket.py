from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.ticket import TicketPriority, TicketStatus
from app.models.message import SenderType


class MessageCreate(BaseModel):
    content: str


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    sender_type: SenderType
    content: str
    intent: str | None = None
    confidence: float | None = None
    sentiment: float | None = None
    created_at: datetime


class TicketCreate(BaseModel):
    subject: str
    message: str


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    subject: str
    status: TicketStatus
    priority: TicketPriority
    detected_intent: str | None = None
    intent_confidence: float | None = None
    sentiment_score: float | None = None
    summary: str | None = None
    created_at: datetime
    updated_at: datetime


class TicketDetailOut(TicketOut):
    messages: list[MessageOut] = []


class AssistantReply(BaseModel):
    ticket_id: str
    reply: str
    intent: str
    confidence: float
    sentiment: float
    escalated: bool
    status: TicketStatus
