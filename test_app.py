import pytest
from app import app, options


@pytest.fixture
def client():
    app.config["TESTING"] = True
    options.clear()
    with app.test_client() as client:
        yield client
    options.clear()


def test_index_empty(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"No options yet" in resp.data


def test_add_option(client):
    resp = client.post("/add", data={"name": "Pizza", "username": "Alice"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Pizza" in resp.data
    assert b"Alice" in resp.data
    assert b"No options yet" not in resp.data


def test_add_without_username_defaults_to_anonymous(client):
    client.post("/add", data={"name": "Pizza"})
    assert options[0]["added_by"] == "Anonymous"


def test_add_duplicate_is_ignored(client):
    client.post("/add", data={"name": "Pizza", "username": "Alice"})
    client.post("/add", data={"name": "pizza", "username": "Bob"})
    assert len(options) == 1


def test_add_blank_is_ignored(client):
    client.post("/add", data={"name": "  "})
    assert len(options) == 0


def test_vote_increments(client):
    client.post("/add", data={"name": "Tacos", "username": "Alice"})
    client.post("/vote/Tacos")
    client.post("/vote/Tacos")
    assert options[0]["votes"] == 2


def test_vote_nonexistent_does_not_crash(client):
    resp = client.post("/vote/Ghost", follow_redirects=True)
    assert resp.status_code == 200


def test_reset_clears_everything(client):
    client.post("/add", data={"name": "A"})
    client.post("/add", data={"name": "B"})
    client.post("/vote/A")
    client.post("/reset")
    assert len(options) == 0


def test_options_sorted_by_votes(client):
    client.post("/add", data={"name": "Low"})
    client.post("/add", data={"name": "High"})
    client.post("/vote/High")
    client.post("/vote/High")
    client.post("/vote/Low")
    resp = client.get("/")
    html = resp.data.decode()
    assert html.index("High") < html.index("Low")
