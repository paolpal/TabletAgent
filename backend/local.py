"""Local development entry point: serve the API and frontend on one port."""
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles

root = Path(__file__).resolve().parent.parent
load_dotenv(root / '.env')
os.environ.setdefault('AGENT_MODE', 'openrouter' if os.environ.get('OPEN_ROUTER_KEY') or os.environ.get('OPENROUTER_API_KEY') else 'mock')
os.environ.setdefault('DATABASE_PATH', str(root / 'backend' / 'local-chats.sqlite3'))

from app import create_app

app = create_app()
app.mount('/', StaticFiles(directory=str(root / 'frontend'), html=True), name='frontend')
