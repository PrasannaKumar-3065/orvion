"""
chat_panel.py — Orvion Test Recorder UI
─────────────────────────────────────────
• Editable test name (click the title to rename)
• URL bar per test — browser auto-navigates on load
• Re-run button — replays recorded steps
• Thought / Action logs are hidden; only the final Answer is shown
• Self-healing announcements shown as a special amber bubble
"""

from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QSizePolicy, QTextEdit, QPushButton, QProgressBar,
    QStackedWidget, QLineEdit, QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QEvent
from PyQt5.QtGui import QFont, QCursor

from .message_widget import MessageWidget, TypingIndicator


# ── Chat bubble ───────────────────────────────────────────────────────────────

class ChatBubble(QWidget):
    STYLES = {
        "user": (
            "#bubble_frame { background:#2b5ff4; border-radius:12px;"
            " border-bottom-right-radius:2px; }"
            " QLabel { color:white; font-size:13px; }"
        ),
        "assistant": (
            "#bubble_frame { background:#2d2d2d; border:1px solid #3d3d3d;"
            " border-radius:12px; border-bottom-left-radius:2px; }"
            " QLabel { color:#e0e0e0; font-size:13px; }"
        ),
        "heal": (
            "#bubble_frame { background:#3a2a00; border:1px solid #7a5500;"
            " border-radius:8px; }"
            " QLabel { color:#ffcc44; font-size:12px; font-style:italic; }"
        ),
        "status": (
            "#bubble_frame { background:rgba(50,50,50,160);"
            " border:1px solid #444; border-radius:4px; }"
            " QLabel { color:#888; font-size:11px; font-family:Consolas; }"
        ),
    }

    def __init__(self, text, kind="assistant", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)

        self.frame = QFrame(); self.frame.setObjectName("bubble_frame")
        inner = QVBoxLayout(self.frame)
        inner.setContentsMargins(12, 8, 12, 8)

        self.lbl = QLabel(text)
        self.lbl.setWordWrap(True)
        self.lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl.setTextFormat(Qt.MarkdownText)
        inner.addWidget(self.lbl)

        self.frame.setStyleSheet(self.STYLES.get(kind, self.STYLES["assistant"]))

        if kind == "user":
            layout.addStretch(); layout.addWidget(self.frame)
        elif kind in ("status", "heal"):
            layout.addStretch(); layout.addWidget(self.frame); layout.addStretch()
        else:
            layout.addWidget(self.frame); layout.addStretch()

    def setText(self, text):
        self.lbl.setText(text)


# ── Chat Panel ────────────────────────────────────────────────────────────────

class ChatPanel(QWidget):
    message_sent    = pyqtSignal(str)
    rerun_requested = pyqtSignal(int)   # emits conv_id
    url_changed     = pyqtSignal(int, str)  # conv_id, new_url

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.setObjectName("chat_panel")
        self.db            = db
        self.agent         = None
        self.current_conv  = None
        self._chat_history = []
        self._build()

    # ── Public ────────────────────────────────────────────────────────────────

    def set_agent(self, agent):
        self.agent = agent
        agent.chat_reply.connect(self._on_agent_reply)
        agent.phase_changed.connect(self._on_phase_changed)
        agent.download_progress.connect(self._on_download_progress)
        agent.hw_info.connect(self._on_hw_info)
        agent.model_ready.connect(self._on_model_ready_chat)
        agent.rerun_status.connect(self._on_rerun_status)
        agent.self_healing.connect(self._on_self_healing)
        # step_log intentionally NOT connected to chat — stays silent

    def append_agent_log(self, text: str):
        """Kept for compatibility; step_log messages are NOT displayed."""
        pass

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        hdr = QWidget(); hdr.setObjectName("chat_header"); hdr.setFixedHeight(48)
        hl  = QHBoxLayout(hdr); hl.setContentsMargins(14, 0, 14, 0); hl.setSpacing(8)

        # Editable title
        self.title_edit = QLineEdit("New Test")
        self.title_edit.setObjectName("chat_title_edit")
        self.title_edit.setFrame(False)
        self.title_edit.setStyleSheet(
            "QLineEdit { background:transparent; color:#e0e0e0;"
            " font-size:14px; font-weight:600; border:none;"
            " border-bottom:1px solid transparent; }"
            "QLineEdit:focus { border-bottom:1px solid #7C5CFC; }"
        )
        self.title_edit.editingFinished.connect(self._on_title_edited)
        hl.addWidget(self.title_edit, stretch=1)

        # Re-run button
        self.rerun_btn = QPushButton("▶  Re-run")
        self.rerun_btn.setObjectName("save_btn")
        self.rerun_btn.setCursor(Qt.PointingHandCursor)
        self.rerun_btn.setFixedHeight(28)
        self.rerun_btn.setToolTip("Replay recorded steps in the browser")
        self.rerun_btn.clicked.connect(self._on_rerun_clicked)
        self.rerun_btn.hide()   # shown only when a conversation with steps exists
        hl.addWidget(self.rerun_btn)

        self.badge = QLabel("Loading model\u2026"); self.badge.setObjectName("model_badge")
        hl.addWidget(self.badge)
        lay.addWidget(hdr)

        # ── URL bar ───────────────────────────────────────────────────────────
        url_bar = QWidget(); url_bar.setObjectName("url_bar_widget")
        url_bar.setFixedHeight(36)
        url_bar.setStyleSheet(
            "#url_bar_widget { background:#1a1a2e; border-bottom:1px solid #2e2e4a; }")
        ul = QHBoxLayout(url_bar); ul.setContentsMargins(14, 4, 14, 4); ul.setSpacing(6)

        url_icon = QLabel("🌐"); url_icon.setFixedWidth(20)
        ul.addWidget(url_icon)

        self.url_edit = QLineEdit()
        self.url_edit.setObjectName("url_bar_input")
        self.url_edit.setPlaceholderText("Test URL  (e.g. https://example.com/login)")
        self.url_edit.setStyleSheet(
            "QLineEdit { background:transparent; color:#aaaacc;"
            " font-size:12px; border:none; }"
            "QLineEdit:focus { color:#e0e0ff; }"
        )
        self.url_edit.editingFinished.connect(self._on_url_edited)
        ul.addWidget(self.url_edit, stretch=1)

        url_hint = QLabel("Browser auto-navigates on Re-run")
        url_hint.setStyleSheet("color:#555; font-size:10px;")
        ul.addWidget(url_hint)
        lay.addWidget(url_bar)

        # ── Scroll area ───────────────────────────────────────────────────────
        self.scroll = QScrollArea(); self.scroll.setObjectName("chat_scroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.msgs_w   = QWidget(); self.msgs_w.setObjectName("chat_messages")
        self.msgs_lay = QVBoxLayout(self.msgs_w)
        self.msgs_lay.setContentsMargins(0, 14, 0, 6); self.msgs_lay.setSpacing(0)
        self.msgs_lay.addStretch()
        self.scroll.setWidget(self.msgs_w)
        lay.addWidget(self.scroll, stretch=1)

        self.typing = TypingIndicator(); self.typing.hide()
        lay.addWidget(self.typing)

        # ── Stacked bottom (0=loading overlay, 1=input) ───────────────────────
        self.bottom_stack = QStackedWidget()
        self.bottom_stack.setFixedHeight(240)

        # Page 0: loading overlay
        overlay = QWidget(); overlay.setObjectName("loading_overlay")
        ov_lay  = QVBoxLayout(overlay)
        ov_lay.setContentsMargins(24, 14, 24, 14); ov_lay.setSpacing(5)
        top_row = QHBoxLayout()
        self._ov_icon  = QLabel("\u23f3"); self._ov_icon.setObjectName("loading_phase_icon")
        self._ov_phase = QLabel("Initialising\u2026")
        self._ov_phase.setObjectName("loading_phase_label")
        top_row.addWidget(self._ov_icon); top_row.addSpacing(10)
        top_row.addWidget(self._ov_phase); top_row.addStretch()
        self._ov_pct = QLabel(""); self._ov_pct.setObjectName("loading_pct_label")
        top_row.addWidget(self._ov_pct)
        ov_lay.addLayout(top_row)
        self._ov_detail = QLabel("")
        self._ov_detail.setObjectName("loading_detail_label")
        self._ov_detail.setAlignment(Qt.AlignLeft); self._ov_detail.setWordWrap(True)
        self._ov_detail.setTextInteractionFlags(Qt.TextSelectableByMouse)
        ov_lay.addWidget(self._ov_detail)
        self._ov_bar = QProgressBar(); self._ov_bar.setObjectName("model_progress")
        self._ov_bar.setRange(0, 100); self._ov_bar.setValue(0)
        self._ov_bar.setTextVisible(False)
        ov_lay.addWidget(self._ov_bar)
        meta = QHBoxLayout()
        self._ov_hw    = QLabel(""); self._ov_hw.setObjectName("loading_hw_label")
        self._ov_speed = QLabel(""); self._ov_speed.setObjectName("loading_speed_label")
        meta.addWidget(self._ov_hw); meta.addStretch(); meta.addWidget(self._ov_speed)
        ov_lay.addLayout(meta)
        self._retry_btn = QPushButton("\u21ba  Retry")
        self._retry_btn.setObjectName("save_btn")
        self._retry_btn.setCursor(Qt.PointingHandCursor); self._retry_btn.hide()
        self._retry_btn.clicked.connect(self._retry_model_load)
        ov_lay.addWidget(self._retry_btn, alignment=Qt.AlignLeft)
        ov_lay.addStretch()
        self.bottom_stack.addWidget(overlay)    # index 0

        # Page 1: real input
        ic = QWidget(); ic.setObjectName("input_container")
        il = QHBoxLayout(ic); il.setContentsMargins(12, 14, 12, 14); il.setSpacing(9)
        self.inp = QTextEdit(); self.inp.setObjectName("chat_input")
        self.inp.setPlaceholderText("Message Orvion\u2026")
        self.inp.setFixedHeight(48)
        self.inp.setAcceptRichText(False); self.inp.installEventFilter(self)
        self.send = QPushButton("\u2191"); self.send.setObjectName("send_btn")
        self.send.setCursor(Qt.PointingHandCursor); self.send.clicked.connect(self._send)
        il.addWidget(self.inp); il.addWidget(self.send, alignment=Qt.AlignBottom)
        self.bottom_stack.addWidget(ic)         # index 1
        self.bottom_stack.setCurrentIndex(0)

        lay.addWidget(self.bottom_stack)

    # ── Event handlers ────────────────────────────────────────────────────────

    def eventFilter(self, obj, ev):
        if obj == self.inp and ev.type() == QEvent.KeyPress:
            if ev.key() == Qt.Key_Return and not (ev.modifiers() & Qt.ShiftModifier):
                self._send(); return True
        return super().eventFilter(obj, ev)

    def _on_title_edited(self):
        new_title = self.title_edit.text().strip() or "New Test"
        self.title_edit.setText(new_title)
        if self.current_conv and self.db:
            self.db.rename_conversation(self.current_conv, new_title)

    def _on_url_edited(self):
        url = self.url_edit.text().strip()
        if self.current_conv and self.db:
            self.db.set_conversation_url(self.current_conv, url)
            self.url_changed.emit(self.current_conv, url)

    def _on_rerun_clicked(self):
        if self.current_conv:
            self._add_bubble("▶  Re-running test\u2026", kind="status")
            self.rerun_requested.emit(self.current_conv)

    # ── Sending ───────────────────────────────────────────────────────────────

    def _send(self):
        text = self.inp.toPlainText().strip()
        if not text:
            return

        # Create conversation if needed — ask for URL on first message
        if not self.current_conv:
            url, ok = QInputDialog.getText(
                self, "Test URL",
                "Enter the URL for this test\n(leave blank to skip):",
            )
            url = url.strip() if ok else ""
            title = text[:42] + ("\u2026" if len(text) > 42 else "")
            self.current_conv = self.db.new_conversation(title, url)
            self.title_edit.setText(title)
            self.url_edit.setText(url)

        self.db.add_message(self.current_conv, "user", text)
        self._add_bubble(text, kind="user")
        self.inp.clear()
        self.message_sent.emit(text)
        self._chat_history.append({"role": "user", "content": text})
        self.typing.start()

        if self.agent is not None:
            self.agent.enqueue_chat(text, list(self._chat_history[:-1]),
                                    conv_id=self.current_conv)
        else:
            QTimer.singleShot(600, self._fallback_reply)

    # ── Agent signal handlers ─────────────────────────────────────────────────

    def _on_agent_reply(self, reply_text: str):
        self.typing.stop()
        if not reply_text:
            reply_text = "(No response)"
        self.db.add_message(self.current_conv, "assistant", reply_text)
        self._add_bubble(reply_text, kind="assistant")
        self._chat_history.append({"role": "assistant", "content": reply_text})
        # Show re-run button now that steps might exist
        self.rerun_btn.show()

    def _on_rerun_status(self, msg: str):
        self._add_bubble(msg, kind="status")

    def _on_self_healing(self, msg: str):
        self._add_bubble(msg, kind="heal")

    def _fallback_reply(self):
        self.typing.stop()
        msg = "No AI agent is running. Please restart Orvion."
        self.db.add_message(self.current_conv, "assistant", msg)
        self._add_bubble(msg, kind="assistant")
        self._chat_history.append({"role": "assistant", "content": msg})

    def _on_hw_info(self, has_gpu, vram_gb, ram_gb, hw_line):
        self._ov_hw.setText(hw_line)

    def _on_phase_changed(self, phase, detail):
        icons  = {"checking": "🔍", "downloading": "⬇",
                  "loading": "⚙", "ready": "✅", "error": "❌"}
        labels = {"checking": "Checking\u2026", "downloading": "Downloading model",
                  "loading": "Loading model", "ready": "Model ready", "error": "Load error"}
        self._ov_icon.setText(icons.get(phase, "\u23f3"))
        self._ov_phase.setText(labels.get(phase, phase))
        self._ov_detail.setText(detail)
        self._retry_btn.setVisible(phase == "error")
        if phase == "downloading":
            self._ov_bar.setRange(0, 100)
        elif phase in ("loading", "checking"):
            self._ov_bar.setRange(0, 0)
        elif phase == "ready":
            self._ov_bar.setRange(0, 100); self._ov_bar.setValue(100)
        elif phase == "error":
            self._ov_bar.setRange(0, 100); self._ov_bar.setValue(0)

    def _on_download_progress(self, pct, speed, log):
        self._ov_bar.setRange(0, 100); self._ov_bar.setValue(int(pct))
        self._ov_pct.setText(f"{pct:.0f}%")
        if speed > 0:
            self._ov_speed.setText(f"{speed:.1f} MB/s")
        self._ov_detail.setText(log[-80:] if len(log) > 80 else log)
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()

    def _on_model_ready_chat(self):
        self.bottom_stack.setFixedHeight(84)
        self.bottom_stack.setCurrentIndex(1)
        self.badge.setText("Orvion AI  \u2713")
        self.inp.setFocus()

    def _retry_model_load(self):
        if self.agent is None:
            return
        self._retry_btn.hide()
        self._ov_phase.setText("Restarting\u2026")
        self._ov_detail.setText("")
        self._ov_icon.setText("\u23f3")
        self._ov_bar.setRange(0, 0)
        old = self.agent
        old.running = False; old.quit(); old.wait(3000)
        new_agent = type(old)(db=old.db)
        new_agent.chat_reply.connect(self._on_agent_reply)
        new_agent.phase_changed.connect(self._on_phase_changed)
        new_agent.download_progress.connect(self._on_download_progress)
        new_agent.hw_info.connect(self._on_hw_info)
        new_agent.model_ready.connect(self._on_model_ready_chat)
        new_agent.rerun_status.connect(self._on_rerun_status)
        new_agent.self_healing.connect(self._on_self_healing)
        self.agent = new_agent
        new_agent.start()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _add_bubble(self, text: str, kind: str = "assistant"):
        bubble = ChatBubble(text, kind=kind)
        self.msgs_lay.insertWidget(self.msgs_lay.count() - 1, bubble)
        QTimer.singleShot(40, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()))

    def load_conversation(self, conv_id: int):
        self.current_conv = conv_id
        # Clear messages
        while self.msgs_lay.count() > 1:
            item = self.msgs_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        # Load title + URL
        if self.db:
            row = self.db.get_conversation(conv_id)
            if row:
                self.title_edit.setText(row["title"] or "New Test")
                self.url_edit.setText(row["url"] or "")
        # Load messages
        for role, content, ts in self.db.get_messages(conv_id):
            kind = "user" if role == "user" else "assistant"
            bubble = ChatBubble(content, kind=kind)
            self.msgs_lay.insertWidget(self.msgs_lay.count() - 1, bubble)
        # Show re-run if steps exist
        if self.db:
            steps = self.db.get_steps(conv_id)
            self.rerun_btn.setVisible(len(steps) > 0)
        QTimer.singleShot(40, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()))