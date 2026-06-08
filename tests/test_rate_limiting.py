def test_rate_limit_allows_under_limit(client):
    reg = client.post("/register", json={"email": "r1@example.com"})
    key = reg.json()["api_key"]
    for _ in range(5):
        response = client.get("/protected", headers={"x-api-key": key})
        assert response.status_code == 200

def test_rate_limit_blocks_over_limit(client):
    reg = client.post("/register", json={"email": "r12@example.com"})
    key = reg.json()["api_key"]
    for _ in range(5):
        client.get("/protected", headers={"x-api-key": key})
    response = client.get("/protected", headers={"x-api-key": key})
    assert response.status_code == 429

def test_rate_limit_headers_present(client):
    reg = client.post("/register", json={"email": "r13@example.com"})
    key = reg.json()["api_key"]
    response = client.get("/protected", headers = {"x-api-key": key})
    assert "x-ratelimit-limit" in response.headers
    assert "x-ratelimit-remaining" in response.headers
