import os
import sys
import sqlite3
import pathlib
from datetime import datetime


def _db_path():
    app_data = os.environ.get("ORVION_APP_DATA", "")
    if app_data:
        p = pathlib.Path(app_data)
        p.mkdir(parents=True, exist_ok=True)
        return str(p / "orvion.db")
    if sys.platform == "win32":
        base = pathlib.Path(os.environ.get("APPDATA", str(pathlib.Path.home()))) / "Orvion"
    elif sys.platform == "darwin":
        base = pathlib.Path.home() / "Library" / "Application Support" / "Orvion"
    else:
        base = pathlib.Path.home() / ".local" / "share" / "orvion"
    base.mkdir(parents=True, exist_ok=True)
    return str(base / "orvion.db")


class Database:
    def __init__(self, path=None):
        if path is None:
            path = _db_path()
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self._init()

    def _init(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                role TEXT,
                content TEXT,
                timestamp TEXT
            );

            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_address TEXT,
                password TEXT,
                created_on DATETIME,
                expiry_date DATETIME
            );

            CREATE TABLE IF NOT EXISTS inbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_address TEXT,
                send_to TEXT,
                subject TEXT,
                body TEXT,
                received_at DATETIME
            );

            CREATE TABLE IF NOT EXISTS sent (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_address TEXT,
                send_to TEXT,
                diff TEXT CHECK(diff IN ("REPLY", "FORWARD", "SENT")),
                subject TEXT,
                body TEXT,
                received_at DATETIME
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
    
    def email_auth(self, email, password):
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) FROM emails WHERE email_address=? and password=?",(email, password))
        return c.fetchone()
    
    def get_inbox(self, email):
        c = self.conn.cursor()
        c.execute("SELECT * FROM inbox where email_address=?", (email))
        return c.fetchall()
    
    def get_sent(self, email):
        c = self.conn.cursor()
        c.execute("SELECT * FROM sent where email_address=?", (email))
        return c.fetchall()
    
    def send_insert(self, **kwargs):
        mfrom = kwargs.get('from')
        email = kwargs.get('email')
        body = kwargs.get('body')
        subject = kwargs.get('subject')
        table = kwargs.get('table')
        diff = kwargs.get('diff')
        c = self.conn.cursor()
        if table == 'inbox':
            c.execute("INSERT INTO ? (email_address,send_to,subject,body,received_at) values(?,?,?,?)", (table, email,mfrom,subject,body,datetime.now()))
        else:
            c.execute("INSERT INTO ? (email_address,send_to,subject,body,received_at, diff) values(?,?,?,?,?)", (table, email,mfrom,subject,body,datetime.now(),diff))
        return c.execute().fetchone()