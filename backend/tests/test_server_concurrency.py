import concurrent.futures
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx


def test_health_remains_responsive_during_slow_chat(tmp_path):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, DATABASE_PATH=str(tmp_path / 'concurrency.sqlite3'), PYTHONPATH=str(root))
    process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'slow_server:app', '--host', '127.0.0.1', '--port', str(port), '--workers', '1'], cwd=root / 'tests' / 'fixtures', env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = 'http://127.0.0.1:%s' % port
    try:
        for _ in range(100):
            if process.poll() is not None:
                raise AssertionError('Server exited')
            try:
                if httpx.get(base + '/api/health', timeout=.2).status_code == 200:
                    break
            except httpx.RequestError:
                time.sleep(.05)
        else:
            raise AssertionError('Server did not start')
        chat_id = httpx.post(base + '/api/chats', timeout=2).json()['id']
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(httpx.post, base + '/api/chats/%s/stream' % chat_id, json={'content': 'ciao'}, timeout=10)
            time.sleep(.5)
            start = time.monotonic()
            response = httpx.get(base + '/api/health', timeout=2)
            elapsed = time.monotonic() - start
            assert response.status_code == 200
            assert elapsed < 1.5
            assert not future.done()
            assert future.result().status_code == 200
            print('Health durante risposta di 3 secondi: %.3f secondi' % elapsed)
    finally:
        process.terminate()
        process.wait(timeout=10)
