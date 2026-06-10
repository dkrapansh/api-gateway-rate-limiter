def test_analytics_returns_usage(client):
    reg = client.post("/register", json={"email": "analytics@example.com"})
    key = reg.json()["api_key"]
    client.get("/protected", headers={"x-api-key": key})
    client.get("/gateway/users", headers={"x-api-key": key})
    response = client.get("/analytics/usage", headers={"x-api-key": key})
    assert response.status_code == 200
    data = response.json()
    assert data["total_requests"] >= 2
    assert "/protected" in data["requests_per_endpoint"]

def test_analytics_requires_auth(client):
    response = client.get("/analytics/usage", headers={"x-api-key": "fakekey"})
    assert response.status_code == 401