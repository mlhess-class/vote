from unittest.mock import patch, MagicMock
import pytest
import app as voting_app


@pytest.fixture
def mock_db():
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    with patch("app.get_db", return_value=mock_conn):
        yield mock_conn, mock_cur


@pytest.fixture
def client(mock_db):
    voting_app.app.config["TESTING"] = True
    with voting_app.app.test_client() as c:
        yield c


def test_index_empty(client, mock_db):
    _, mock_cur = mock_db
    mock_cur.fetchall.return_value = []
    mock_cur.fetchone.return_value = (0,)

    resp = client.get("/")
    assert resp.status_code == 200
    assert b"No options yet" in resp.data


def test_index_with_options(client, mock_db):
    _, mock_cur = mock_db
    mock_cur.fetchall.return_value = [
        ("Pizza", 5, "Alice"),
        ("Tacos", 3, "Bob"),
    ]
    mock_cur.fetchone.return_value = (8,)

    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Pizza" in resp.data
    assert b"Tacos" in resp.data
    assert b"Alice" in resp.data


def test_add_option(client, mock_db):
    mock_conn, mock_cur = mock_db

    resp = client.post("/add", data={"name": "Sushi", "username": "Carol"})
    assert resp.status_code == 302
    mock_cur.execute.assert_any_call(
        "INSERT INTO options (name, added_by) VALUES (%s, %s) ON CONFLICT (name) DO NOTHING",
        ("Sushi", "Carol"),
    )
    mock_conn.commit.assert_called()


def test_add_option_blank_name(client, mock_db):
    mock_conn, _ = mock_db

    resp = client.post("/add", data={"name": "  ", "username": "Carol"})
    assert resp.status_code == 302
    mock_conn.commit.assert_not_called()


def test_add_option_anonymous(client, mock_db):
    _, mock_cur = mock_db

    client.post("/add", data={"name": "Burgers", "username": ""})
    mock_cur.execute.assert_any_call(
        "INSERT INTO options (name, added_by) VALUES (%s, %s) ON CONFLICT (name) DO NOTHING",
        ("Burgers", "Anonymous"),
    )


def test_vote(client, mock_db):
    mock_conn, mock_cur = mock_db

    resp = client.post("/vote/Pizza")
    assert resp.status_code == 302
    mock_cur.execute.assert_any_call(
        "UPDATE options SET votes = votes + 1 WHERE name = %s", ("Pizza",)
    )
    mock_conn.commit.assert_called()


