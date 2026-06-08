def test_authenticated_request_succeeds(client):
    reg = client.post("/register", json={"email": "gw@example.com"})
    key = reg.json()["api_key"]
    response = client.get("/gateway/users", headers={"x-api-key": key})
    assert response.status_code == 200

def test_unauthenticated_request_blocked(client):
    response = client.get("/gateway/users", headers={"x-api-key": "fakekey"})
    assert response.status_code == 401