from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QPlainTextEdit
)
from PyQt5.QtCore import Qt, QTimer

from styles import EDITOR_LIGHT, EDITOR_DARK


class EditorPanel(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.setObjectName("editor_panel")
        self.db     = db
        self.doc_id = None
        self._light = False
        self._build()
        self._apply_theme()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)

        tb = QWidget(); tb.setObjectName("editor_toolbar")
        tl = QHBoxLayout(tb); tl.setContentsMargins(10, 0, 8, 0); tl.setSpacing(4)

        lbl = QLabel("DOCUMENT"); lbl.setObjectName("editor_title_label")
        tl.addWidget(lbl)
        sep = QFrame(); sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("min-width:1px; max-width:1px; margin:10px 4px;")
        tl.addWidget(sep)

        self.title_inp = QLineEdit("Untitled Document"); self.title_inp.setObjectName("doc_title_input")
        tl.addWidget(self.title_inp); tl.addStretch()

        for t, tip in [("B","Bold"),("I","Italic"),("U","Underline"),("H1","Heading"),("≡","Align")]:
            b = QPushButton(t); b.setObjectName("fmt_btn")
            b.setToolTip(tip); b.setCursor(Qt.PointingHandCursor); tl.addWidget(b)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.VLine)
        sep2.setStyleSheet("min-width:1px; max-width:1px; margin:10px 6px;"); tl.addWidget(sep2)

        self.theme_btn = QPushButton("☀  Light"); self.theme_btn.setObjectName("theme_toggle_btn")
        self.theme_btn.setCursor(Qt.PointingHandCursor); self.theme_btn.clicked.connect(self._toggle)
        tl.addWidget(self.theme_btn)

        self.save_btn = QPushButton("Save"); self.save_btn.setObjectName("save_btn")
        self.save_btn.setCursor(Qt.PointingHandCursor); self.save_btn.clicked.connect(self._save)
        tl.addWidget(self.save_btn)
        lay.addWidget(tb)

        self.wc_bar = QWidget(); self.wc_bar.setObjectName("wc_bar")
        wl = QHBoxLayout(self.wc_bar); wl.setContentsMargins(42, 0, 42, 0)
        self.wc_lbl = QLabel("0 words  ·  0 characters"); self.wc_lbl.setObjectName("wc_label")
        wl.addStretch(); wl.addWidget(self.wc_lbl)
        lay.addWidget(self.wc_bar)

        self.editor = QPlainTextEdit(); self.editor.setObjectName("editor")
        self.editor.setPlaceholderText("Begin writing…\n\nThis is your distraction-free workspace.")
        self.editor.textChanged.connect(self._wc)
        lay.addWidget(self.editor)

        self.bot = QWidget(); self.bot.setObjectName("editor_statusbar")
        sl = QHBoxLayout(self.bot); sl.setContentsMargins(42, 0, 14, 0)
        self.cur_lbl = QLabel("Ln 1, Col 1"); self.cur_lbl.setObjectName("cursor_pos_label")
        self.editor.cursorPositionChanged.connect(self._cursor)
        sl.addStretch(); sl.addWidget(self.cur_lbl)
        lay.addWidget(self.bot)

    def _apply_theme(self):
        self.setStyleSheet(EDITOR_LIGHT if self._light else EDITOR_DARK)
        self.theme_btn.setText("🌙  Dark" if self._light else "☀  Light")

    def _toggle(self):
        self._light = not self._light; self._apply_theme()

    def _wc(self):
        t = self.editor.toPlainText()
        w = len(t.split()) if t.strip() else 0
        self.wc_lbl.setText(f"{w:,} words  ·  {len(t):,} characters")

    def _cursor(self):
        cur = self.editor.textCursor()
        self.cur_lbl.setText(f"Ln {cur.blockNumber()+1}, Col {cur.columnNumber()+1}")

    def _save(self):
        self.doc_id = self.db.save_document(
            self.doc_id, self.title_inp.text() or "Untitled", self.editor.toPlainText())
        self.save_btn.setText("Saved ✓")
        QTimer.singleShot(2000, lambda: self.save_btn.setText("Save"))

    def load_document(self, doc_id):
        row = self.db.get_document(doc_id)
        if row:
            self.doc_id, title, content = row
            self.title_inp.setText(title); self.editor.setPlainText(content)
