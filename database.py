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
        self.conn.row_factory = sqlite3.Row
        self._init()

    def _init(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT,
                url         TEXT DEFAULT '',
                created_at  TEXT
            );

            CREATE TABLE IF NOT EXISTS messages (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                role            TEXT,
                content         TEXT,
                timestamp       TEXT
            );

            CREATE TABLE IF NOT EXISTS documents (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT,
                content     TEXT,
                updated_at  TEXT
            );

            -- Ordered automation steps recorded during a first run
            CREATE TABLE IF NOT EXISTS test_steps (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                step_order      INTEGER,
                tool            TEXT,       -- click | type | scroll | select
                elem_idx        INTEGER,    -- DOM pool index at record time
                value           TEXT,       -- text to type / option to select / scroll px
                cx              INTEGER,    -- viewport centre-x of target element
                cy              INTEGER,    -- viewport centre-y of target element
                elem_text       TEXT,       -- element text label (for self-healing)
                elem_tag        TEXT,       -- tag  (for self-healing)
                elem_type       TEXT,       -- type attribute (for self-healing)
                thought         TEXT,       -- model thought at record time
                status          TEXT DEFAULT 'recorded',
                                            -- recorded | passed | failed | healed
                created_at      TEXT
            );

            -- Every error (inference, execution, self-heal) logged here
            CREATE TABLE IF NOT EXISTS error_logs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                step_id         INTEGER,    -- NULL if not step-specific
                error_text      TEXT,
                context         TEXT,       -- json snapshot of what was happening
                created_at      TEXT
            );

            CREATE TABLE IF NOT EXISTS emails (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                email_address TEXT,
                password      TEXT,
                created_on    DATETIME,
                expiry_date   DATETIME
            );

            CREATE TABLE IF NOT EXISTS inbox (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                email_address TEXT,
                send_to       TEXT,
                subject       TEXT,
                body          TEXT,
                received_at   DATETIME
            );

            CREATE TABLE IF NOT EXISTS sent (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                email_address TEXT,
                send_to       TEXT,
                diff          TEXT CHECK(diff IN ('REPLY','FORWARD','SENT')),
                subject       TEXT,
                body          TEXT,
                received_at   DATETIME
            );

            -- Migrate old conversations table if url column is missing
            PRAGMA user_version;
        """)
        # Safe migration: add url column if it doesn't exist yet
        try:
            self.conn.execute("ALTER TABLE conversations ADD COLUMN url TEXT DEFAULT ''")
            self.conn.commit()
        except Exception:
            pass   # column already exists
        self.conn.commit()

    # ── Conversations ─────────────────────────────────────────────────────────

    def new_conversation(self, title="New Test", url=""):
        ts = datetime.now().isoformat()
        c  = self.conn.cursor()
        c.execute(
            "INSERT INTO conversations (title, url, created_at) VALUES (?,?,?)",
            (title, url, ts)
        )
        self.conn.commit()
        return c.lastrowid

    def get_conversations(self):
        c = self.conn.cursor()
        c.execute("SELECT id, title, url, created_at FROM conversations ORDER BY id DESC")
        return c.fetchall()

    def rename_conversation(self, conv_id: int, title: str):
        self.conn.execute(
            "UPDATE conversations SET title=? WHERE id=?", (title, conv_id))
        self.conn.commit()

    def set_conversation_url(self, conv_id: int, url: str):
        self.conn.execute(
            "UPDATE conversations SET url=? WHERE id=?", (url, conv_id))
        self.conn.commit()

    def get_conversation(self, conv_id: int):
        c = self.conn.cursor()
        c.execute("SELECT id, title, url, created_at FROM conversations WHERE id=?",
                  (conv_id,))
        return c.fetchone()

    # ── Messages ──────────────────────────────────────────────────────────────

    def add_message(self, conv_id, role, content):
        ts = datetime.now().isoformat()
        c  = self.conn.cursor()
        c.execute(
            "INSERT INTO messages (conversation_id, role, content, timestamp)"
            " VALUES (?,?,?,?)",
            (conv_id, role, content, ts)
        )
        self.conn.commit()
        return c.lastrowid

    def get_messages(self, conv_id):
        c = self.conn.cursor()
        c.execute(
            "SELECT role, content, timestamp FROM messages"
            " WHERE conversation_id=? ORDER BY id",
            (conv_id,)
        )
        return c.fetchall()

    # ── Test Steps ────────────────────────────────────────────────────────────

    def add_step(self, conv_id, step_order, tool, elem_idx, value,
                 cx, cy, elem_text, elem_tag, elem_type, thought=""):
        ts = datetime.now().isoformat()
        c  = self.conn.cursor()
        c.execute(
            "INSERT INTO test_steps "
            "(conversation_id, step_order, tool, elem_idx, value,"
            " cx, cy, elem_text, elem_tag, elem_type, thought, status, created_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,'recorded',?)",
            (conv_id, step_order, tool, elem_idx, value,
             cx, cy, elem_text, elem_tag, elem_type, thought, ts)
        )
        self.conn.commit()
        return c.lastrowid

    def get_steps(self, conv_id):
        """Return steps ordered by step_order."""
        c = self.conn.cursor()
        c.execute(
            "SELECT id, step_order, tool, elem_idx, value,"
            "       cx, cy, elem_text, elem_tag, elem_type, thought, status"
            " FROM test_steps WHERE conversation_id=? ORDER BY step_order",
            (conv_id,)
        )
        return c.fetchall()

    def update_step(self, step_id, cx, cy, elem_text, elem_tag, elem_type,
                    value, thought, status):
        """Update a step after self-healing or execution."""
        self.conn.execute(
            "UPDATE test_steps SET cx=?, cy=?, elem_text=?, elem_tag=?,"
            " elem_type=?, value=?, thought=?, status=? WHERE id=?",
            (cx, cy, elem_text, elem_tag, elem_type, value, thought, status, step_id)
        )
        self.conn.commit()

    def set_step_status(self, step_id, status):
        self.conn.execute(
            "UPDATE test_steps SET status=? WHERE id=?", (status, step_id))
        self.conn.commit()

    def next_step_order(self, conv_id: int) -> int:
        c = self.conn.cursor()
        c.execute(
            "SELECT COALESCE(MAX(step_order), 0) + 1 FROM test_steps"
            " WHERE conversation_id=?",
            (conv_id,)
        )
        return c.fetchone()[0]

    # ── Error Logs ────────────────────────────────────────────────────────────

    def log_error(self, conv_id, error_text, context="", step_id=None):
        ts = datetime.now().isoformat()
        self.conn.execute(
            "INSERT INTO error_logs"
            " (conversation_id, step_id, error_text, context, created_at)"
            " VALUES (?,?,?,?,?)",
            (conv_id, step_id, error_text, context, ts)
        )
        self.conn.commit()

    def get_errors(self, conv_id):
        c = self.conn.cursor()
        c.execute(
            "SELECT id, step_id, error_text, context, created_at"
            " FROM error_logs WHERE conversation_id=? ORDER BY id DESC",
            (conv_id,)
        )
        return c.fetchall()

    # ── Documents ─────────────────────────────────────────────────────────────

    def save_document(self, doc_id, title, content):
        ts = datetime.now().isoformat()
        c  = self.conn.cursor()
        if doc_id:
            c.execute(
                "UPDATE documents SET title=?, content=?, updated_at=? WHERE id=?",
                (title, content, ts, doc_id)
            )
        else:
            c.execute(
                "INSERT INTO documents (title, content, updated_at) VALUES (?,?,?)",
                (title, content, ts)
            )
            doc_id = c.lastrowid
        self.conn.commit()
        return doc_id

    def get_document(self, doc_id):
        c = self.conn.cursor()
        c.execute("SELECT id, title, content FROM documents WHERE id=?", (doc_id,))
        return c.fetchone()