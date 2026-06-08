def test_revoked_key_returns_403(client):
    reg = client.post("/register", json={"email": "rev@example.com"})
    key = reg.json()["api_key"]
    client.post("/keys/revoke", headers={"x-api-key": key})
    response = client.get("/protected", headers={"x-api-key": key})
    assert response.status_code == 403