import pytest
from fastapi.testclient import TestClient

from app import create_app
from app.store import Store


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('AUTH_PASSWORD', 'password-per-test')
    monkeypatch.setenv('AUTH_SESSION_SECRET', 's' * 40)
    monkeypatch.setenv('AUTH_COOKIE_SECURE', 'false')
    return TestClient(create_app(Store(str(tmp_path / 'test.sqlite3')), lambda h, c: 'ok'))


def test_access_login_and_logout(client):
    assert client.get('/api/chats').status_code == 401
    assert client.get('/api/health').status_code == 200
    assert client.post('/api/auth/login', json={'password': 'wrong'}).status_code == 401
    response = client.post('/api/auth/login', json={'password': 'password-per-test'})
    assert response.status_code == 200
    assert 'httponly' in response.headers['set-cookie'].lower()
    assert client.get('/api/chats').json() == []
    assert client.post('/api/chats', json={}).status_code == 201
    assert client.post('/api/auth/logout', json={}).status_code == 200
    assert client.get('/api/chats').status_code == 401


def test_tampered_cookie_and_cross_origin_request_rejected(client):
    client.post('/api/auth/login', json={'password': 'password-per-test'})
    response = client.post('/api/chats', json={}, headers={'Origin': 'https://untrusted.example'})
    assert response.status_code == 403
    assert client.post('/api/chats', content='{}', headers={'Content-Type': 'text/plain'}).status_code == 415
    client.cookies.clear()
    client.cookies.set('tablet_agent_session', '9999999999.fake.fake')
    assert client.get('/api/chats').status_code == 401


def test_repeated_login_attempts_are_limited(client):
    for _ in range(8):
        assert client.post('/api/auth/login', json={'password': 'wrong'}).status_code == 401
    assert client.post('/api/auth/login', json={'password': 'password-per-test'}).status_code == 429


def test_auth_requires_session_secret(monkeypatch):
    monkeypatch.setenv('AUTH_PASSWORD', 'something')
    monkeypatch.setenv('AUTH_SESSION_SECRET', 'short')
    with pytest.raises(RuntimeError, match='AUTH_SESSION_SECRET'):
        create_app()
