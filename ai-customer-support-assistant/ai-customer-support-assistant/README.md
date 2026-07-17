# AI-Powered Customer Support Assistant

A production-style backend for an AI customer support assistant. It classifies
customer intent, analyzes sentiment, retrieves relevant knowledge-base
articles, drafts a response, and automatically escalates tickets to human
agents when confidence is low, sentiment is very negative, or the issue is a
complaint.

## Features

- **Intent classification** — TF-IDF + Naive Bayes model trained on a bundled
  labeled dataset (9 intents: billing, technical support, account management,
  order status, product info, complaints, greetings, gratitude, cancellation).
- **Sentiment analysis** — VADER lexicon-based scoring tuned for short,
  informal support messages.
- **Knowledge-base retrieval** — TF-IDF cosine-similarity search over a
  seeded article set, auto-attached to assistant replies.
- **Escalation logic** — configurable thresholds decide whether a ticket is
  auto-resolved, kept open for further auto-replies, or escalated to a human
  agent with a computed priority (low/medium/high/urgent).
- **Ticketing system** — full ticket + threaded-message model with
  customer/agent roles, claim/resolve workflow.
- **JWT authentication** — registration, login, role-based access
  (customer vs. support agent).
- **REST API** — FastAPI with auto-generated OpenAPI docs at `/docs`.

## Architecture

```
app/
├── api/                # FastAPI routers (auth, tickets, knowledge base)
├── core/                # config, database, security
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic request/response schemas
├── services/            # AI services: intent classifier, sentiment, KB, orchestrator
└── main.py              # application entrypoint
data/                    # bundled training data, response templates, KB seed
scripts/                 # seed_knowledge_base.py
tests/                   # pytest suite
```

## Getting Started

### Option 1: Docker Compose (recommended)

```bash
cp .env.example .env
docker compose up --build
```

The API will be available at `http://localhost:8000`, with interactive docs
at `http://localhost:8000/docs`. The knowledge base is seeded automatically
on startup.

### Option 2: Local Python environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env

python -m scripts.seed_knowledge_base
uvicorn app.main:app --reload
```

## Usage Walkthrough

1. **Register a customer:**
   `POST /api/v1/auth/register` with `email`, `full_name`, `password`.
2. **Log in:**
   `POST /api/v1/auth/login` (OAuth2 password form: `username` = email) to
   get a JWT `access_token`.
3. **Open a ticket:**
   `POST /api/v1/tickets` with `subject` and `message`. The assistant
   classifies intent, scores sentiment, retrieves a relevant KB article, and
   returns a reply plus escalation decision — all in one call.
4. **Continue the conversation:**
   `POST /api/v1/tickets/{ticket_id}/messages` with `content`.
5. **Agent workflow:** register a user with `is_agent: true`, then use
   `POST /api/v1/tickets/{ticket_id}/claim` and `.../resolve` to work escalated
   tickets. Agents can view all tickets via `GET /api/v1/tickets`.

## Configuration

All tunables live in `.env` (see `.env.example`):

| Variable | Purpose |
|---|---|
| `INTENT_CONFIDENCE_THRESHOLD` | Below this, tickets escalate regardless of intent |
| `ESCALATION_SENTIMENT_THRESHOLD` | VADER compound score below this escalates |
| `MAX_AUTO_REPLIES_PER_TICKET` | Forces escalation after repeated auto-replies |
| `ENABLE_LLM_FALLBACK` | Reserved flag for wiring in a hosted LLM for out-of-scope intents |

## Running Tests

```bash
pip install -r requirements.txt
pytest
```

Tests cover authentication, ticket creation/escalation flows, role-based
access control, and the intent/sentiment services directly.

## Extending

- **Swap the intent model**: replace `data/intents.json` with a larger
  labeled dataset, or swap `IntentClassifier` for an embeddings-based or
  hosted-LLM classifier — the rest of the pipeline is decoupled behind
  `SupportAssistantService`.
- **Add channels**: the message model already supports `SYSTEM` and `AGENT`
  sender types, so Slack/email/chat-widget integrations can post into the
  same ticket thread.
- **LLM fallback**: `ENABLE_LLM_FALLBACK` is scaffolded in config for routing
  low-confidence intents to a hosted LLM instead of immediate escalation.

## Tech Stack

FastAPI · SQLAlchemy · SQLite (swappable via `DATABASE_URL`) · scikit-learn ·
VADER Sentiment · JWT (python-jose) · bcrypt (passlib) · pytest · Docker
