"""A slow test agent for measuring FastAPI concurrency with one worker."""
import os
import time
from app import create_app
from app.store import Store


def slow_reply(history, content):
    time.sleep(3)
    return 'Risposta di prova'


app = create_app(Store(os.environ['DATABASE_PATH']), slow_reply)
