import os
import sqlite3


class Store:
    def __init__(self, path):
        self.path = path
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY, title TEXT NOT NULL DEFAULT 'Nuova chat',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY, chat_id INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
                    role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS messages_chat_id ON messages(chat_id, id);
            ''')

    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        return db

    def create_chat(self):
        with self.connect() as db:
            cursor = db.execute('INSERT INTO chats DEFAULT VALUES')
            return dict(db.execute('SELECT * FROM chats WHERE id=?', (cursor.lastrowid,)).fetchone())

    def delete_chat(self, chat_id):
        with self.connect() as db:
            return db.execute('DELETE FROM chats WHERE id=?', (chat_id,)).rowcount > 0

    def chat_exists(self, chat_id):
        with self.connect() as db:
            return db.execute('SELECT 1 FROM chats WHERE id=?', (chat_id,)).fetchone() is not None

    def list_chats(self):
        with self.connect() as db:
            return [dict(row) for row in db.execute('SELECT * FROM chats ORDER BY id DESC')]

    def messages(self, chat_id):
        with self.connect() as db:
            return [dict(row) for row in db.execute(
                'SELECT role, content FROM messages WHERE chat_id=? ORDER BY id', (chat_id,))]

    def add_exchange(self, chat_id, question, answer):
        with self.connect() as db:
            db.executemany('INSERT INTO messages(chat_id, role, content) VALUES (?, ?, ?)',
                           [(chat_id, 'user', question), (chat_id, 'assistant', answer)])
            db.execute("UPDATE chats SET title=? WHERE id=? AND title='Nuova chat'",
                       (question[:60], chat_id))
