def test_create_ticket_requires_auth(client):
    response = client.post("/api/v1/tickets", json={"subject": "Help", "message": "I need help"})
    assert response.status_code == 401


def test_create_ticket_returns_assistant_reply(client, registered_customer):
    response = client.post(
        "/api/v1/tickets",
        json={"subject": "Billing question", "message": "why was I charged twice this month"},
        headers=registered_customer["headers"],
    )
    assert response.status_code == 201
    data = response.json()
    assert data["intent"] == "billing_inquiry"
    assert 0.0 <= data["confidence"] <= 1.0
    assert "reply" in data and len(data["reply"]) > 0


def test_complaint_ticket_gets_escalated(client, registered_customer):
    response = client.post(
        "/api/v1/tickets",
        json={
            "subject": "Very unhappy",
            "message": "this is the worst service I have ever used and I am extremely frustrated",
        },
        headers=registered_customer["headers"],
    )
    data = response.json()
    assert data["escalated"] is True
    assert data["status"] == "escalated"


def test_customer_can_list_own_tickets(client, registered_customer):
    client.post(
        "/api/v1/tickets",
        json={"subject": "Order status", "message": "where is my order"},
        headers=registered_customer["headers"],
    )
    response = client.get("/api/v1/tickets", headers=registered_customer["headers"])
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_customer_cannot_view_others_ticket(client, registered_customer, registered_agent):
    create_resp = client.post(
        "/api/v1/tickets",
        json={"subject": "Password reset", "message": "I can't log into my account"},
        headers=registered_customer["headers"],
    )
    ticket_id = create_resp.json()["ticket_id"]

    other_customer_payload = {
        "email": "other@example.com",
        "full_name": "Other Customer",
        "password": "SecurePass123!",
    }
    client.post("/api/v1/auth/register", json=other_customer_payload)
    login = client.post(
        "/api/v1/auth/login",
        data={"username": other_customer_payload["email"], "password": other_customer_payload["password"]},
    )
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = client.get(f"/api/v1/tickets/{ticket_id}", headers=other_headers)
    assert response.status_code == 403


def test_agent_can_claim_and_resolve_ticket(client, registered_customer, registered_agent):
    create_resp = client.post(
        "/api/v1/tickets",
        json={"subject": "App crash", "message": "the app keeps crashing when I open it"},
        headers=registered_customer["headers"],
    )
    ticket_id = create_resp.json()["ticket_id"]

    claim_resp = client.post(f"/api/v1/tickets/{ticket_id}/claim", headers=registered_agent["headers"])
    assert claim_resp.status_code == 200
    assert claim_resp.json()["status"] == "in_progress"

    resolve_resp = client.post(f"/api/v1/tickets/{ticket_id}/resolve", headers=registered_agent["headers"])
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["status"] == "resolved"


def test_non_agent_cannot_claim_ticket(client, registered_customer):
    create_resp = client.post(
        "/api/v1/tickets",
        json={"subject": "Question", "message": "do you offer a free trial"},
        headers=registered_customer["headers"],
    )
    ticket_id = create_resp.json()["ticket_id"]
    response = client.post(f"/api/v1/tickets/{ticket_id}/claim", headers=registered_customer["headers"])
    assert response.status_code == 403
