import json
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QTabWidget, QStatusBar, QSizeGrip,
    QLabel, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt, QEvent

from database import Database
from styles import QSS_BASE
from constants import AI_AVAILABLE
from agent_worker import AgentWorker
from widgets import (
    EdgeHandle, TitleBar, Sidebar, ChatPanel, WebEngine, EditorPanel
)


class OrvionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db     = Database()
        self.agent  = None
        self.setWindowTitle("Orvion")
        self.setMinimumSize(1060, 680)
        self.resize(1380, 840)
        self.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint |
            Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint   | Qt.WindowSystemMenuHint
        )
        self._build()
        self.setStyleSheet(QSS_BASE)

    def _build(self):
        root = QWidget(); root.setObjectName("root")
        self.setCentralWidget(root)
        rl = QVBoxLayout(root); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(0)

        self.titlebar = TitleBar(self)
        rl.addWidget(self.titlebar)

        body = QWidget()
        bl   = QHBoxLayout(body); bl.setContentsMargins(0, 0, 0, 0); bl.setSpacing(0)

        self.sidebar = Sidebar(self.db)
        self.sidebar.new_chat_requested.connect(self._new_chat)
        self.sidebar.conversation_selected.connect(self._load_conv)
        bl.addWidget(self.sidebar)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(1); self.splitter.setChildrenCollapsible(False)

        self.chat     = ChatPanel(self.db)
        self.chat.message_sent.connect(self._on_msg)

        self.tabs     = QTabWidget()
        self.web_page = WebEngine()
        self.editor   = EditorPanel(self.db)
        self.tabs.addTab(self.editor,   "Editor")
        self.tabs.addTab(self.web_page, "Browser")

        self.splitter.addWidget(self.chat)
        self.splitter.addWidget(self.tabs)
        self.splitter.setSizes([500, 500])
        bl.addWidget(self.splitter)
        rl.addWidget(body)

        sb = QStatusBar(); self.setStatusBar(sb)
        self._status = QLabel("Ready  ·  SQLite connected")
        sb.addPermanentWidget(self._status)
        sb.addPermanentWidget(QSizeGrip(self))

        self._eh_l = EdgeHandle(self, EdgeHandle.L, root)
        self._eh_r = EdgeHandle(self, EdgeHandle.R, root)
        self._eh_t = EdgeHandle(self, EdgeHandle.T, root)
        root.installEventFilter(self)

        # Start AI worker
        if AI_AVAILABLE:
            self.agent = AgentWorker()
            self.agent.webengine = self.web_page
            # Browser-state bridge
            self.agent.request_browser_state.connect(self._provide_browser_state)
            self.agent.browser_state_ready.connect(self.agent._on_browser_state_ready)

            # Screenshot bridge
            self.agent.request_screenshot.connect(self._provide_screenshot)
            self.agent.screenshot_ready.connect(self.agent._on_screenshot_ready)

            # Setup dialog bridge
            self.agent.setup_requested.connect(self._show_setup_dialog)
            self.agent.setup_result_ready.connect(self.agent._on_setup_result)

            # Tool execution bridge
            self.agent.tool_request.connect(self._execute_tool)
            self.agent.tool_result_ready.connect(self.agent._on_tool_result)

            # UI updates
            self.agent.step_log.connect(self.chat.append_agent_log)
            self.agent.log_signal.connect(self._on_agent_log)
            self.agent.model_ready.connect(self._on_model_ready)
            self.agent.download_progress.connect(self._on_download_progress)
            self.agent.phase_changed.connect(self._on_phase_changed)

            self.chat.set_agent(self.agent)
            self.agent.start()
        else:
            self._status.setText("⚠  AI unavailable — install transformers + torch + qwen-vl-utils")
            self.chat.bottom_stack.setFixedHeight(84)
            self.chat.bottom_stack.setCurrentIndex(1)

    def _execute_tool(self, tool_name: str, args: dict):
        """Runs on the main thread. Executes browser action and emits result back."""
        result = "ERROR: Unknown"
        try:
            if tool_name == "click":
                result = self.web_page.click_selector(args["selector"])
            elif tool_name == "type":
                result = self.web_page.type_selector(args["selector"], args["text"])
            elif tool_name == "open_url":
                self.web_page.open_url(args["url"])
                result = "NAVIGATED"
        except Exception as e:
            result = f"ERROR: {e}"

        # Emit the result back to the sleeping AgentWorker
        self.agent.tool_result_ready.emit(result)

    def _provide_browser_state(self):
        """Runs on the main thread. Grabs UI state and sends to worker."""
        screenshot_bytes = self.web_page.get_screenshot()
        dom = self.web_page.get_dom()
        self.agent._on_browser_state_ready(screenshot_bytes, json.dumps(dom))

    def _provide_screenshot(self):
        self.agent.screenshot_ready.emit(self.web_page.get_screenshot())

    def _show_setup_dialog(self):
        choice = QMessageBox.question(
            self, "Model Setup",
            "No local model found. Download it locally?",
            QMessageBox.Yes | QMessageBox.No
        )
        if choice == QMessageBox.Yes:
            self.agent.setup_result_ready.emit("local", "")
        else:
            url, ok = QInputDialog.getText(
                self, "Hugging Face Space API",
                "Enter your Space base URL:"
            )
            if ok and url.strip():
                clean = url.strip().rstrip("/")
                for suffix in ("/gradio_api/call/generate", "/api/predict", "/run/predict", "/predict"):
                    if clean.endswith(suffix):
                        clean = clean[: -len(suffix)].rstrip("/")
                self.agent.setup_result_ready.emit("space", clean)
            else:
                self.agent.setup_result_ready.emit("none", "")

    def eventFilter(self, obj, ev):
        if ev.type() == QEvent.Resize and obj == self.centralWidget():
            w, h, s = obj.width(), obj.height(), 5
            self._eh_l.setGeometry(0,     s, s,     h - s)
            self._eh_r.setGeometry(w - s, s, s,     h - s)
            self._eh_t.setGeometry(0,     0, w,     s)
        return super().eventFilter(obj, ev)

    def closeEvent(self, event):
        if self.agent is not None:
            self.agent.running = False; self.agent.quit(); self.agent.wait(3000)
        event.accept()

    def _new_chat(self):
        self.chat.current_conv = None
        self.chat.hdr_title.setText("New Conversation")
        self.chat._chat_history.clear()
        while self.chat.msgs_lay.count() > 1:
            item = self.chat.msgs_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self._status.setText("New conversation")

    def _new_doc(self):
        self.editor.doc_id = None
        self.editor.title_inp.setText("Untitled Document")
        self.editor.editor.clear()

    def _load_conv(self, cid: int):
        self.chat.load_conversation(cid)
        self.chat._chat_history = [
            {"role": role, "content": content}
            for role, content, _ in self.db.get_messages(cid)
        ]
        self._status.setText(f"Conversation #{cid} loaded")

    def _on_msg(self, text: str):
        self.sidebar.refresh()
        self._status.setText(f"Sent · {datetime.now().strftime('%H:%M:%S')}")

    def _on_agent_log(self, msg: str, color: str):
        self._status.setText(msg)

    def _on_model_ready(self):
        self._status.setText("✓  Orvion AI ready")

    def _on_phase_changed(self, phase: str, detail: str):
        labels = {
            "checking":    "🔍 Checking hardware…",
            "downloading": "⬇  Downloading model…",
            "loading":     "⚙  Loading model…",
            "ready":       "✓  Orvion AI ready",
            "error":       "❌  Error — see chat panel",
        }
        self._status.setText(labels.get(phase, phase))

    def _on_download_progress(self, pct: float, speed: float, log: str):
        self._status.setText(
            f"⬇  Downloading… {pct:.0f}%  @  {speed:.1f} MB/s" if speed > 0
            else f"⬇  Downloading… {pct:.0f}%"
        )

    def keyPressEvent(self, e):
        if e.modifiers() == Qt.ControlModifier:
            if e.key() == Qt.Key_Q:   self.close()
            elif e.key() == Qt.Key_N: self._new_chat()
            elif e.key() == Qt.Key_S: self.editor._save()
        super().keyPressEvent(e)
