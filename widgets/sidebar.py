from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QListWidget, QListWidgetItem, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal


class Sidebar(QWidget):
    new_chat_requested    = pyqtSignal()
    conversation_selected = pyqtSignal(int)

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.db = db
        self.setFixedWidth(220)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addSpacing(6)

        btn = QPushButton("  ＋  New Conversation")
        btn.setObjectName("new_chat_btn")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self.new_chat_requested)
        lay.addWidget(btn)

        for label, active in [("  💬  Chats", True), ("  📄  Documents", False)]:
            b = QPushButton(label); b.setObjectName("nav_btn")
            if active:
                b.setProperty("active", "true")
            b.setCursor(Qt.PointingHandCursor)
            lay.addWidget(b)

        sec = QLabel("RECENT"); sec.setObjectName("section_label")
        lay.addWidget(sec)

        self.conv_list = QListWidget()
        self.conv_list.setObjectName("conv_list")
        self.conv_list.setFrameShape(QFrame.NoFrame)
        self.conv_list.itemClicked.connect(
            lambda item: self.conversation_selected.emit(item.data(Qt.UserRole))
        )
        lay.addWidget(self.conv_list)
        lay.addStretch()

        foot = QLabel("v1.0  ·  SQLite")
        foot.setStyleSheet("color:#1E1C38; font-size:10px; padding:10px 16px;")
        lay.addWidget(foot)
        self.refresh()

    def refresh(self):
        self.conv_list.clear()
        for cid, title, _ in self.db.get_conversations():
            item = QListWidgetItem(f"  {title}")
            item.setData(Qt.UserRole, cid)
            self.conv_list.addItem(item)
