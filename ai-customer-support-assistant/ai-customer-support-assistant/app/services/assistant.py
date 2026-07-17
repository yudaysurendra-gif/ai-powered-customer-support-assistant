"""
Core orchestration service for the AI customer support assistant.

Combines intent classification, sentiment analysis, and knowledge-base
retrieval to produce a response, and decides whether the ticket should
be auto-resolved, kept open for auto-reply, or escalated to a human
agent based on confidence, sentiment, and repeated-contact heuristics.
"""
import json
import os
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.message import Message, SenderType
from app.models.ticket import Ticket, TicketPriority, TicketStatus
from app.services.intent_classifier import IntentPrediction, get_intent_classifier
from app.services.knowledge_base import KBSearchResult, get_knowledge_base_service
from app.services.sentiment_analyzer import SentimentResult, get_sentiment_analyzer

TEMPLATES_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "response_templates.json")


@dataclass
class AssistantResult:
    reply: str
    intent: str
    confidence: float
    sentiment: float
    escalated: bool
    status: TicketStatus
    kb_matches: list[KBSearchResult]


class SupportAssistantService:
    def __init__(self):
        self.classifier = get_intent_classifier()
        self.sentiment_analyzer = get_sentiment_analyzer()
        self.kb_service = get_knowledge_base_service()
        with open(TEMPLATES_PATH, encoding="utf-8") as f:
            self.templates: dict[str, str] = json.load(f)

    def _build_reply(self, intent_pred: IntentPrediction, kb_matches: list[KBSearchResult]) -> str:
        base = self.templates.get(intent_pred.intent, self.templates["unknown"])
        if kb_matches:
            top = kb_matches[0]
            base += f"\n\nRelevant help article — \"{top.title}\":\n{top.content}"
        return base

    def _decide_escalation(
        self,
        intent_pred: IntentPrediction,
        sentiment: SentimentResult,
        ticket: Ticket,
    ) -> tuple[bool, TicketStatus, TicketPriority]:
        low_confidence = intent_pred.confidence < settings.INTENT_CONFIDENCE_THRESHOLD
        very_negative = sentiment.compound <= settings.ESCALATION_SENTIMENT_THRESHOLD
        is_complaint = intent_pred.intent == "complaint"
        repeated_contact = ticket.auto_reply_count + 1 >= settings.MAX_AUTO_REPLIES_PER_TICKET

        escalate = low_confidence or very_negative or is_complaint or repeated_contact

        if escalate:
            if very_negative or is_complaint:
                priority = TicketPriority.URGENT if sentiment.compound <= -0.6 else TicketPriority.HIGH
            else:
                priority = TicketPriority.MEDIUM
            return True, TicketStatus.ESCALATED, priority

        if intent_pred.intent in {"greeting", "gratitude"}:
            return False, TicketStatus.AUTO_RESOLVED, TicketPriority.LOW

        return False, TicketStatus.OPEN, TicketPriority.LOW

    def handle_message(self, db: Session, ticket: Ticket, message_text: str) -> AssistantResult:
        intent_pred = self.classifier.predict(message_text)
        sentiment = self.sentiment_analyzer.analyze(message_text)
        kb_matches = self.kb_service.search(db, message_text)

        escalated, status, priority = self._decide_escalation(intent_pred, sentiment, ticket)
        reply = (
            "I'm connecting you with a member of our support team who can give this the attention it needs. "
            "In the meantime, here's what I found that might help:"
            if escalated and intent_pred.intent != "complaint"
            else self._build_reply(intent_pred, kb_matches)
        )
        if escalated and intent_pred.intent == "complaint":
            reply = self._build_reply(intent_pred, kb_matches)
        elif escalated and kb_matches:
            reply += f"\n\n\"{kb_matches[0].title}\":\n{kb_matches[0].content}"

        ticket.detected_intent = intent_pred.intent
        ticket.intent_confidence = intent_pred.confidence
        ticket.sentiment_score = sentiment.compound
        ticket.status = status
        ticket.priority = priority
        if not escalated:
            ticket.auto_reply_count += 1

        return AssistantResult(
            reply=reply,
            intent=intent_pred.intent,
            confidence=intent_pred.confidence,
            sentiment=sentiment.compound,
            escalated=escalated,
            status=status,
            kb_matches=kb_matches,
        )


def get_support_assistant_service() -> SupportAssistantService:
    return SupportAssistantService()
