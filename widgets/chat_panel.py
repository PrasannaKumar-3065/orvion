from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QSizePolicy, QTextEdit, QPushButton, QProgressBar,
    QStackedWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QEvent
from PyQt5.QtGui import QFont

from .message_widget import MessageWidget, TypingIndicator


class ChatBubble(QWidget):
    def __init__(self, text, role="assistant", is_log=False, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        self.frame = QFrame()
        self.frame.setObjectName("bubble_frame")
        inner = QVBoxLayout(self.frame)
        inner.setContentsMargins(12, 8, 12, 8)

        self.lbl = QLabel(text)
        self.lbl.setWordWrap(True)
        self.lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl.setTextFormat(Qt.MarkdownText)
        inner.addWidget(self.lbl)

        if is_log:
            self.lbl.setFont(QFont("Consolas", 9))
            self.frame.setStyleSheet("""
                #bubble_frame { background-color: rgba(60,60,60,150); border: 1px solid #444; border-radius: 4px; }
                QLabel { color: #aaaaaa; }
            """)
            layout.addStretch(); layout.addWidget(self.frame); layout.addStretch()
        elif role == "user":
            self.frame.setStyleSheet("""
                #bubble_frame { background-color: #2b5ff4; border-radius: 12px; border-bottom-right-radius: 2px; }
                QLabel { color: white; font-size: 13px; }
            """)
            layout.addStretch(); layout.addWidget(self.frame)
        else:
            self.frame.setStyleSheet("""
                #bubble_frame { background-color: #2d2d2d; border: 1px solid #3d3d3d; border-radius: 12px; border-bottom-left-radius: 2px; }
                QLabel { color: #e0e0e0; font-size: 13px; }
            """)
            layout.addWidget(self.frame); layout.addStretch()

    def setText(self, text):
        self.lbl.setText(text)


class ChatPanel(QWidget):
    message_sent = pyqtSignal(str)

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.setObjectName("chat_panel")
        self.db            = db
        self.agent         = None
        self.current_conv  = None
        self._chat_history = []
        self._build()

    def append_agent_log(self, text: str):
        bubble = ChatBubble(text, role="assistant", is_log=True)
        self.msgs_lay.insertWidget(self.msgs_lay.count() - 1, bubble)
        QTimer.singleShot(40, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()))

    def set_agent(self, agent):
        self.agent = agent
        self.agent.chat_reply.connect(self._on_agent_reply)
        self.agent.phase_changed.connect(self._on_phase_changed)
        self.agent.download_progress.connect(self._on_download_progress)
        self.agent.hw_info.connect(self._on_hw_info)
        self.agent.model_ready.connect(self._on_model_ready_chat)

    def _on_hw_info(self, has_gpu, vram_gb, ram_gb, hw_line):
        self._ov_hw.setText(hw_line)

    def _on_phase_changed(self, phase, detail):
        icons  = {"checking": "🔍", "downloading": "⬇", "loading": "⚙", "ready": "✅", "error": "❌"}
        labels = {"checking": "Checking…", "downloading": "Downloading model",
                  "loading": "Loading model", "ready": "Model ready", "error": "Load error"}
        self._ov_icon.setText(icons.get(phase, "⏳"))
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

    def _retry_model_load(self):
        if self.agent is None:
            return
        self._retry_btn.hide()
        self._ov_phase.setText("Restarting…")
        self._ov_detail.setText("")
        self._ov_icon.setText("⏳")
        self._ov_bar.setRange(0, 0)
        old = self.agent
        old.running = False; old.quit(); old.wait(3000)
        new_agent = type(old)()
        new_agent.chat_reply.connect(self._on_agent_reply)
        new_agent.phase_changed.connect(self._on_phase_changed)
        new_agent.download_progress.connect(self._on_download_progress)
        new_agent.hw_info.connect(self._on_hw_info)
        new_agent.model_ready.connect(self._on_model_ready_chat)
        self.agent = new_agent
        new_agent.start()

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
        self.badge.setText("Orvion AI  ✓")
        self.inp.setFocus()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Header
        hdr = QWidget(); hdr.setObjectName("chat_header"); hdr.setFixedHeight(48)
        hl  = QHBoxLayout(hdr); hl.setContentsMargins(18, 0, 18, 0)
        self.hdr_title = QLabel("New Conversation"); self.hdr_title.setObjectName("chat_header_title")
        self.badge     = QLabel("Loading model…");   self.badge.setObjectName("model_badge")
        hl.addWidget(self.hdr_title); hl.addStretch(); hl.addWidget(self.badge)
        lay.addWidget(hdr)

        # Scroll area
        self.scroll   = QScrollArea(); self.scroll.setObjectName("chat_scroll")
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

        # Stacked bottom (0=loading overlay, 1=input)
        self.bottom_stack = QStackedWidget()
        self.bottom_stack.setFixedHeight(240)

        # Page 0: loading overlay
        overlay = QWidget(); overlay.setObjectName("loading_overlay")
        ov_lay  = QVBoxLayout(overlay); ov_lay.setContentsMargins(24, 14, 24, 14); ov_lay.setSpacing(5)
        top_row = QHBoxLayout()
        self._ov_icon  = QLabel("⏳"); self._ov_icon.setObjectName("loading_phase_icon")
        self._ov_phase = QLabel("Initialising…"); self._ov_phase.setObjectName("loading_phase_label")
        top_row.addWidget(self._ov_icon); top_row.addSpacing(10); top_row.addWidget(self._ov_phase)
        top_row.addStretch()
        self._ov_pct = QLabel(""); self._ov_pct.setObjectName("loading_pct_label")
        top_row.addWidget(self._ov_pct)
        ov_lay.addLayout(top_row)
        self._ov_detail = QLabel(""); self._ov_detail.setObjectName("loading_detail_label")
        self._ov_detail.setAlignment(Qt.AlignLeft); self._ov_detail.setWordWrap(True)
        self._ov_detail.setTextInteractionFlags(Qt.TextSelectableByMouse)
        ov_lay.addWidget(self._ov_detail)
        self._ov_bar = QProgressBar(); self._ov_bar.setObjectName("model_progress")
        self._ov_bar.setRange(0, 100); self._ov_bar.setValue(0); self._ov_bar.setTextVisible(False)
        ov_lay.addWidget(self._ov_bar)
        meta = QHBoxLayout(); meta.setContentsMargins(0, 0, 0, 0)
        self._ov_hw    = QLabel(""); self._ov_hw.setObjectName("loading_hw_label")
        self._ov_speed = QLabel(""); self._ov_speed.setObjectName("loading_speed_label")
        meta.addWidget(self._ov_hw); meta.addStretch(); meta.addWidget(self._ov_speed)
        ov_lay.addLayout(meta)
        self._retry_btn = QPushButton("↺  Retry"); self._retry_btn.setObjectName("save_btn")
        self._retry_btn.setCursor(Qt.PointingHandCursor); self._retry_btn.hide()
        self._retry_btn.clicked.connect(self._retry_model_load)
        ov_lay.addWidget(self._retry_btn, alignment=Qt.AlignLeft)
        ov_lay.addStretch()
        self.bottom_stack.addWidget(overlay)   # index 0

        # Page 1: real input
        ic = QWidget(); ic.setObjectName("input_container")
        il = QHBoxLayout(ic); il.setContentsMargins(12, 14, 12, 14); il.setSpacing(9)
        self.inp = QTextEdit(); self.inp.setObjectName("chat_input")
        self.inp.setPlaceholderText("Message Orvion…"); self.inp.setFixedHeight(48)
        self.inp.setAcceptRichText(False); self.inp.installEventFilter(self)
        self.send = QPushButton("↑"); self.send.setObjectName("send_btn")
        self.send.setCursor(Qt.PointingHandCursor); self.send.clicked.connect(self._send)
        il.addWidget(self.inp); il.addWidget(self.send, alignment=Qt.AlignBottom)
        self.bottom_stack.addWidget(ic)        # index 1
        self.bottom_stack.setCurrentIndex(0)   # always start on loading overlay

        lay.addWidget(self.bottom_stack)

    def eventFilter(self, obj, ev):
        if obj == self.inp and ev.type() == QEvent.KeyPress:
            if ev.key() == Qt.Key_Return and not (ev.modifiers() & Qt.ShiftModifier):
                self._send(); return True
        return super().eventFilter(obj, ev)

    def _send(self):
        text = self.inp.toPlainText().strip()
        if not text:
            return
        if not self.current_conv:
            self.current_conv = self.db.new_conversation(
                text[:42] + ("…" if len(text) > 42 else ""))
            self.hdr_title.setText(text[:42])
        self.db.add_message(self.current_conv, "user", text)
        self._add("user", text)
        self.inp.clear()
        self.message_sent.emit(text)
        self._chat_history.append({"role": "user", "content": text})
        self.typing.start()
        # Always route to agent if it exists — never fall back for API mode
        if self.agent is not None:
            self.agent.enqueue_chat(text, list(self._chat_history[:-1]))
        else:
            QTimer.singleShot(600, self._fallback_reply)

    def _fallback_reply(self):
        """Only called when there is genuinely no agent at all."""
        self.typing.stop()
        msg = "No AI agent is running. Please restart Orvion."
        self.db.add_message(self.current_conv, "assistant", msg)
        self._add("assistant", msg)
        self._chat_history.append({"role": "assistant", "content": msg})

    def _on_agent_reply(self, reply_text: str):
        self.typing.stop()
        if not reply_text:
            reply_text = "(No response)"
        self.db.add_message(self.current_conv, "assistant", reply_text)
        self._add("assistant", reply_text)
        self._chat_history.append({"role": "assistant", "content": reply_text})

    def _add(self, role, content, ts=""):
        ts = ts or datetime.now().isoformat()
        w  = MessageWidget(role, content, ts)
        self.msgs_lay.insertWidget(self.msgs_lay.count() - 1, w)
        QTimer.singleShot(40, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()))

    def load_conversation(self, conv_id):
        self.current_conv = conv_id
        while self.msgs_lay.count() > 1:
            item = self.msgs_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for role, content, ts in self.db.get_messages(conv_id):
            self._add(role, content, ts)