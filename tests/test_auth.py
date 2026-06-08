def test_register_success(client):
    response = client.post("/register", json={"email": "test@example.com"})
    assert response.status_code == 201
    data = response.json()
    assert "api_key" in data
    assert "message" in data

def test_register_duplicate_email(client):
    client.post("/register", json={"email": "test@example.com"})
    response = client.post("/register", json={"email": "test@example.com"})
    assert response.status_code == 409

def test_register_returns_key_once(client):
    response = client.post("/register", json={"email": "test@example.com"})
    assert response.status_code == 201
    assert len(response.json()["api_key"]) == 64