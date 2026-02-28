import sqlite3
from datetime import datetime


class Database:
    def __init__(self, path="orvion.db"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self._init()

    def _init(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT, created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER, role TEXT,
                content TEXT, timestamp TEXT
            );
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT, content TEXT, updated_at TEXT
            );
        """)
        self.conn.commit()

    def new_conversation(self, title="New Chat"):
        ts = datetime.now().isoformat()
        c  = self.conn.cursor()
        c.execute("INSERT INTO conversations (title,created_at) VALUES (?,?)", (title, ts))
        self.conn.commit()
        return c.lastrowid

    def get_conversations(self):
        c = self.conn.cursor()
        c.execute("SELECT id,title,created_at FROM conversations ORDER BY id DESC")
        return c.fetchall()

    def add_message(self, conv_id, role, content):
        ts = datetime.now().isoformat()
        c  = self.conn.cursor()
        c.execute(
            "INSERT INTO messages (conversation_id,role,content,timestamp) VALUES (?,?,?,?)",
            (conv_id, role, content, ts)
        )
        self.conn.commit()

    def get_messages(self, conv_id):
        c = self.conn.cursor()
        c.execute(
            "SELECT role,content,timestamp FROM messages WHERE conversation_id=? ORDER BY id",
            (conv_id,)
        )
        return c.fetchall()

    def save_document(self, doc_id, title, content):
        ts = datetime.now().isoformat()
        c  = self.conn.cursor()
        if doc_id:
            c.execute(
                "UPDATE documents SET title=?,content=?,updated_at=? WHERE id=?",
                (title, content, ts, doc_id)
            )
        else:
            c.execute(
                "INSERT INTO documents (title,content,updated_at) VALUES (?,?,?)",
                (title, content, ts)
            )
            doc_id = c.lastrowid
        self.conn.commit()
        return doc_id

    def get_document(self, doc_id):
        c = self.conn.cursor()
        c.execute("SELECT id,title,content FROM documents WHERE id=?", (doc_id,))
        return c.fetchone()
