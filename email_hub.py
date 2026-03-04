import smtplib
import os

from dotenv import load_dotenv
load_dotenv()

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QTabWidget, QWidget

class GenInbox(QWidget):
    inbox = []
    sent = []
    def __init__(self, email, database, parent=None):
        super().__init__(parent)
        self.master = email
        self.database = database
        self.setObjectName("editor_panel")
        self._load_message()
        self._build()

    def _load_message(self):
        self.inbox = []
        self.sent = []

    def _build(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Inbox for {self.master}"))
    

class EmailHub(QWidget):
    IMAP_HOST = os.getenv("IMAP_HOST", "")
    IMAP_USERNAME = os.getenv("IMAP_USERNAME", "")
    IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", "")
    IMAP_PORT = os.getenv("IMAP_PORT", "")
    email = ['1@gmail.com', '2@gmail.com']
    active = pyqtSignal(str)
    def __init__(self, database, parent=None):
        super().__init__(parent)
        self.database = database
        self.conn = smtplib.SMTP_SSL(self.IMAP_HOST, self.IMAP_PORT)
        self.mail = self.conn.login(self.IMAP_USERNAME, self.IMAP_PASSWORD)
        # self.inbox = self.mail.select('inbox')
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)

        self.tabs = QTabWidget()
        for _ in self.email:
            self.tabs.addTab(GenInbox(_, self.database), _)
        
        layout.addWidget(self.tabs)