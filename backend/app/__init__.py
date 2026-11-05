import json
import logging
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from .agent import reply, stream_events
from .store import Store

logger = logging.getLogger(__name__)


def create_app(store=None, agent=None):
    app = FastAPI(title='Tablet Agent')
    store = store or Store(os.environ.get('DATABASE_PATH', '/data/chats.sqlite3'))
    streaming_agent = stream_events if agent is None else lambda history, content: iter([{'text': agent(history, content)}])
    agent = agent or reply

    @app.get('/api/health')
    def health():
        return {'status': 'ok'}

    @app.get('/api/chats')
    def chats():
        return store.list_chats()

    @app.post('/api/chats', status_code=201)
    def create_chat():
        return store.create_chat()

    @app.delete('/api/chats/{chat_id}', status_code=204)
    def delete_chat(chat_id: int):
        if not store.delete_chat(chat_id):
            return JSONResponse({'error': 'Conversazione non trovata'}, status_code=404)
        from fastapi import Response
        return Response(status_code=204)

    @app.get('/api/chats/{chat_id}/messages')
    def messages(chat_id: int):
        if not store.chat_exists(chat_id):
            return JSONResponse({'error': 'Conversazione non trovata'}, status_code=404)
        return store.messages(chat_id)

    @app.post('/api/chats/{chat_id}/messages')
    async def send_message(chat_id: int, request: Request):
        if not store.chat_exists(chat_id):
            return JSONResponse({'error': 'Conversazione non trovata'}, status_code=404)
        try:
            data = await request.json()
        except ValueError:
            data = {}
        content = data.get('content') if isinstance(data, dict) else None
        if not isinstance(content, str) or not content.strip() or len(content) > 20000:
            return JSONResponse({'error': 'Inserisci un messaggio valido (massimo 20.000 caratteri).'}, status_code=400)
        from starlette.concurrency import run_in_threadpool
        content = content.strip()
        history = store.messages(chat_id)
        try:
            answer = await run_in_threadpool(agent, history, content)
        except Exception:
            logger.exception('Agent request failed')
            return JSONResponse({'error': 'Impossibile ottenere una risposta. Controlla modello, chiave e log del backend.'}, status_code=502)
        store.add_exchange(chat_id, content, answer)
        return store.messages(chat_id)

    @app.post('/api/chats/{chat_id}/stream')
    async def stream_message(chat_id: int, request: Request):
        if not store.chat_exists(chat_id):
            return JSONResponse({'error': 'Conversazione non trovata'}, status_code=404)
        try:
            data = await request.json()
        except ValueError:
            data = {}
        content = data.get('content') if isinstance(data, dict) else None
        if not isinstance(content, str) or not content.strip() or len(content) > 20000:
            return JSONResponse({'error': 'Inserisci un messaggio valido (massimo 20.000 caratteri).'}, status_code=400)
        content = content.strip()
        history = store.messages(chat_id)

        def events():
            parts = []
            try:
                for event in streaming_agent(history, content):
                    if 'text' in event:
                        parts.append(event['text'])
                    yield json.dumps(event, ensure_ascii=True) + '\n'
                answer = ''.join(parts)
                if not answer.strip():
                    raise ValueError('Empty response')
                store.add_exchange(chat_id, content, answer)
                yield json.dumps({'done': True}) + '\n'
            except Exception:
                logger.exception('Agent stream failed')
                yield json.dumps({'error': 'Impossibile ottenere una risposta. Controlla modello, chiave e log del backend.'}) + '\n'

        return StreamingResponse(events(), media_type='application/x-ndjson', headers={'X-Accel-Buffering': 'no', 'Cache-Control': 'no-cache'})

    return app
