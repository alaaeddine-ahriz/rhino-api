from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_register_user():
    response = client.post("/users/register", json={
        "username": "testuser",
        "email": "testuser@example.com",
        "role": "student",
        "subscriptions": ["SYD", "TCP"]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "user_id" in data["data"]
    assert data["message"] == "Utilisateur enregistré"


def test_update_and_get_subscriptions():
    # Register a user first
    reg = client.post("/users/register", json={
        "username": "subuser",
        "email": "subuser@example.com",
        "role": "student",
        "subscriptions": ["SYD"]
    })
    user_id = reg.json()["data"]["user_id"]

    # Update subscriptions
    response = client.put("/users/subscriptions", json={
        "user_id": user_id,
        "subscriptions": ["SYD", "TCP"]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["subscriptions"] == ["SYD", "TCP"]
    assert data["message"] == "Abonnements mis à jour"

    # Get subscriptions
    response = client.put("/users/subscriptions", json={
        "user_id": user_id
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["subscriptions"] == ["SYD", "TCP"]
    assert data["message"] == "Abonnements récupérés" 