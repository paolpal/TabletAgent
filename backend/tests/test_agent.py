import json

import httpx
from langchain_openai import ChatOpenAI

from app.agent import reply


def test_mock_response(monkeypatch):
    monkeypatch.setenv('AGENT_MODE', 'mock')
    assert 'prova' in reply([], 'Ciao')


def test_openrouter_agent_sends_history_with_tools(monkeypatch):
    requests = []
    def handle(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, headers={'content-type': 'text/event-stream'}, text='data: ' + json.dumps({'id': 'test', 'object': 'chat.completion.chunk', 'choices': [{'index': 0, 'delta': {'role': 'assistant', 'content': 'Ciao!'}, 'finish_reason': None}]}) + '\n\ndata: [DONE]\n\n')
    client = httpx.Client(transport=httpx.MockTransport(handle))
    def model(**kwargs):
        return ChatOpenAI(http_client=client, max_retries=0, **kwargs)
    monkeypatch.setenv('AGENT_MODE', 'openrouter')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'test')
    monkeypatch.setattr('app.agent.ChatOpenAI', model)
    assert reply([{'role': 'user', 'content': 'Prima'}, {'role': 'assistant', 'content': 'Risposta'}], 'Ciao') == 'Ciao!'
    assert {item['function']['name'] for item in requests[0]['tools']} == {'current_date', 'search_web', 'read_web_page'}
    assert [m['content'] for m in requests[0]['messages'][-3:]] == ['Prima', 'Risposta', 'Ciao']


def test_stream_reports_tool_activity_without_exposing_tool_output(monkeypatch):
    from langchain_core.messages import AIMessageChunk, ToolMessage
    from app.agent import stream_events

    class FakeAgent:
        def stream(self, data, stream_mode):
            yield AIMessageChunk(content='', tool_call_chunks=[{'name': 'search_web', 'args': '', 'id': 'call1', 'index': 0}]), {}
            yield ToolMessage(content='risultato interno', tool_call_id='call1'), {}
            yield AIMessageChunk(content='Risposta'), {}

    monkeypatch.setenv('AGENT_MODE', 'openrouter')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'test')
    monkeypatch.setattr('app.agent.create_deep_agent', lambda **kwargs: FakeAgent())
    events = list(stream_events([], 'Cerca'))
    assert events == [{'status': 'Cerco informazioni sul web…'}, {'text': 'Risposta'}]
