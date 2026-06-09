def test_correlation_id_generated(client):
    reg = client.post("/register", json={"email": "mid@example.com"})
    key = reg.json()["api_key"]
    response = client.get("/protected", headers={"x-api-key": key})
    assert "x-correlation-id" in response.headers

def test_correlation_id_propagated(client):
    reg = client.post("/register", json={"email": "mid2@example.com"})
    key = reg.json()["api_key"]
    response = client.get("/protected", headers={
        "x-api-key": key,
        "X-Correlation-ID": "test-id-123"
    })
    assert response.headers["x-correlation-id"] == "test-id-123"