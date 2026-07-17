from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_agent, get_current_user
from app.core.database import get_db
from app.models.message import Message, SenderType
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User
from app.schemas.ticket import (
    AssistantReply,
    MessageCreate,
    MessageOut,
    TicketCreate,
    TicketDetailOut,
    TicketOut,
)
from app.services.assistant import get_support_assistant_service

router = APIRouter(prefix="/api/v1/tickets", tags=["tickets"])
assistant_service = get_support_assistant_service()


def _get_owned_ticket(db: Session, ticket_id: str, user: User) -> Ticket:
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    if not user.is_agent and ticket.customer_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this ticket")
    return ticket


@router.post("", response_model=AssistantReply, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ticket = Ticket(subject=payload.subject, customer_id=user.id)
    db.add(ticket)
    db.flush()  # assign ticket.id before referencing it

    customer_message = Message(ticket_id=ticket.id, sender_type=SenderType.CUSTOMER, content=payload.message)
    db.add(customer_message)

    result = assistant_service.handle_message(db, ticket, payload.message)
    customer_message.intent = result.intent
    customer_message.confidence = result.confidence
    customer_message.sentiment = result.sentiment

    assistant_message = Message(
        ticket_id=ticket.id,
        sender_type=SenderType.ASSISTANT,
        content=result.reply,
        intent=result.intent,
        confidence=result.confidence,
        sentiment=result.sentiment,
    )
    db.add(assistant_message)

    db.commit()
    db.refresh(ticket)

    return AssistantReply(
        ticket_id=ticket.id,
        reply=result.reply,
        intent=result.intent,
        confidence=result.confidence,
        sentiment=result.sentiment,
        escalated=result.escalated,
        status=ticket.status,
    )


@router.post("/{ticket_id}/messages", response_model=AssistantReply)
def send_message(
    ticket_id: str,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket = _get_owned_ticket(db, ticket_id, user)
    if ticket.status in {TicketStatus.RESOLVED, TicketStatus.CLOSED}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket is already closed")

    customer_message = Message(ticket_id=ticket.id, sender_type=SenderType.CUSTOMER, content=payload.content)
    db.add(customer_message)

    result = assistant_service.handle_message(db, ticket, payload.content)
    customer_message.intent = result.intent
    customer_message.confidence = result.confidence
    customer_message.sentiment = result.sentiment

    assistant_message = Message(
        ticket_id=ticket.id,
        sender_type=SenderType.ASSISTANT,
        content=result.reply,
        intent=result.intent,
        confidence=result.confidence,
        sentiment=result.sentiment,
    )
    db.add(assistant_message)

    db.commit()
    db.refresh(ticket)

    return AssistantReply(
        ticket_id=ticket.id,
        reply=result.reply,
        intent=result.intent,
        confidence=result.confidence,
        sentiment=result.sentiment,
        escalated=result.escalated,
        status=ticket.status,
    )


@router.get("", response_model=list[TicketOut])
def list_tickets(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Ticket)
    if not user.is_agent:
        query = query.filter(Ticket.customer_id == user.id)
    return query.order_by(Ticket.created_at.desc()).all()


@router.get("/{ticket_id}", response_model=TicketDetailOut)
def get_ticket(ticket_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _get_owned_ticket(db, ticket_id, user)


@router.post("/{ticket_id}/claim", response_model=TicketOut)
def claim_ticket(ticket_id: str, db: Session = Depends(get_db), agent: User = Depends(get_current_agent)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    ticket.assigned_agent_id = agent.id
    ticket.status = TicketStatus.IN_PROGRESS
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/resolve", response_model=TicketOut)
def resolve_ticket(ticket_id: str, db: Session = Depends(get_db), agent: User = Depends(get_current_agent)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    ticket.status = TicketStatus.RESOLVED
    db.commit()
    db.refresh(ticket)
    return ticket
