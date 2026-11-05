from app import create_app
from app.store import Store
from fastapi.testclient import TestClient


def test_chat_persists_conversation_and_passes_history(tmp_path):
    received = []
    def agent(history, content):
        received.append((history, content))
        return 'Risposta'
    path = str(tmp_path / 'chats.sqlite3')
    client = TestClient(create_app(Store(path), agent))
    chat_id = client.post('/api/chats').json()['id']
    assert client.post('/api/chats/%s/messages' % chat_id, json={'content': 'Ciao'}).status_code == 200
    assert client.post('/api/chats/%s/messages' % chat_id, json={'content': 'Ancora'}).status_code == 200
    assert received[1][0] == [{'role': 'user', 'content': 'Ciao'}, {'role': 'assistant', 'content': 'Risposta'}]
    assert len(Store(path).messages(chat_id)) == 4
    assert client.get('/api/chats').json()[0]['title'] == 'Ciao'


def test_failed_agent_does_not_save_partial_exchange(tmp_path):
    def fail(history, content):
        raise RuntimeError('failed')
    store = Store(str(tmp_path / 'db.sqlite3'))
    client = TestClient(create_app(store, fail))
    chat_id = client.post('/api/chats').json()['id']
    assert client.post('/api/chats/%s/messages' % chat_id, json={'content': 'Ciao'}).status_code == 502
    assert store.messages(chat_id) == []


def test_missing_chat_and_invalid_message(tmp_path):
    client = TestClient(create_app(Store(str(tmp_path / 'db.sqlite3')), lambda h, c: 'ok'))
    assert client.get('/api/chats/999/messages').status_code == 404
    chat_id = client.post('/api/chats').json()['id']
    assert client.post('/api/chats/%s/messages' % chat_id, json={'content': '  '}).status_code == 400


def test_delete_chat_removes_messages(tmp_path):
    store = Store(str(tmp_path / 'db.sqlite3'))
    client = TestClient(create_app(store, lambda h, c: 'ok'))
    chat_id = client.post('/api/chats').json()['id']
    client.post('/api/chats/%s/messages' % chat_id, json={'content': 'Ciao'})
    assert client.delete('/api/chats/%s' % chat_id).status_code == 204
    assert store.messages(chat_id) == []
    assert client.delete('/api/chats/%s' % chat_id).status_code == 404


def test_stream_saves_only_complete_exchange(tmp_path):
    store = Store(str(tmp_path / 'db.sqlite3'))
    client = TestClient(create_app(store, lambda h, c: 'Risposta'))
    chat_id = client.post('/api/chats').json()['id']
    result = client.post('/api/chats/%s/stream' % chat_id, json={'content': 'Ciao'})
    import json
    events = [json.loads(line) for line in result.text.splitlines()]
    assert events == [{'text': 'Risposta'}, {'done': True}]
    assert store.messages(chat_id)[-1]['content'] == 'Risposta'


def test_stream_error_does_not_save(tmp_path):
    def fail(history, content):
        raise RuntimeError('failed')
    store = Store(str(tmp_path / 'db.sqlite3'))
    client = TestClient(create_app(store, fail))
    chat_id = client.post('/api/chats').json()['id']
    assert 'error' in client.post('/api/chats/%s/stream' % chat_id, json={'content': 'Ciao'}).text
    assert store.messages(chat_id) == []
