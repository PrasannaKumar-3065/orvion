import json
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QTabWidget, QStatusBar, QSizeGrip,
    QLabel, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt, QEvent, QUrl

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
        self.db    = Database()
        self.agent = None
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
        rl = QVBoxLayout(root); rl.setContentsMargins(0,0,0,0); rl.setSpacing(0)

        self.titlebar = TitleBar(self)
        rl.addWidget(self.titlebar)

        body = QWidget()
        bl   = QHBoxLayout(body); bl.setContentsMargins(0,0,0,0); bl.setSpacing(0)

        self.sidebar = Sidebar(self.db)
        self.sidebar.new_chat_requested.connect(self._new_chat)
        self.sidebar.conversation_selected.connect(self._load_conv)
        bl.addWidget(self.sidebar)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(1); self.splitter.setChildrenCollapsible(False)

        self.chat = ChatPanel(self.db)
        self.chat.message_sent.connect(self._on_msg)
        self.chat.rerun_requested.connect(self._on_rerun_requested)
        self.chat.url_changed.connect(self._on_url_changed)

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
        self._status = QLabel("Ready  \u00b7  SQLite connected")
        sb.addPermanentWidget(self._status)
        sb.addPermanentWidget(QSizeGrip(self))

        self._eh_l = EdgeHandle(self, EdgeHandle.L, root)
        self._eh_r = EdgeHandle(self, EdgeHandle.R, root)
        self._eh_t = EdgeHandle(self, EdgeHandle.T, root)
        root.installEventFilter(self)

        # Start AI worker
        if AI_AVAILABLE:
            self.agent = AgentWorker(db=self.db)
            # Browser-state bridge
            self.agent.request_browser_state.connect(self._provide_browser_state)
            # Tool execution bridge
            self.agent.tool_request.connect(self._execute_tool)
            self.agent.tool_result_ready.connect(self.agent._on_tool_result)
            # Screenshot bridge
            self.agent.request_screenshot.connect(self._provide_screenshot)
            # Setup bridge
            self.agent.setup_requested.connect(self._show_setup_dialog)
            self.agent.setup_result_ready.connect(self.agent._on_setup_result)
            # UI updates
            self.agent.log_signal.connect(self._on_agent_log)
            self.agent.model_ready.connect(self._on_model_ready)
            self.agent.download_progress.connect(self._on_download_progress)
            self.agent.phase_changed.connect(self._on_phase_changed)
            # Rerun / self-heal status to status bar
            self.agent.rerun_status.connect(
                lambda msg: self._status.setText(msg))
            self.agent.self_healing.connect(
                lambda msg: self._status.setText(msg))

            self.chat.set_agent(self.agent)
            self.agent.start()
        else:
            self._status.setText(
                "\u26a0  AI unavailable \u2014 install transformers + torch + qwen-vl-utils")
            self.chat.bottom_stack.setFixedHeight(84)
            self.chat.bottom_stack.setCurrentIndex(1)

    # ── Tool execution (main thread) ──────────────────────────────────────────

    def _execute_tool(self, tool_name: str, args: dict):
        """
        Dispatches every tool to web_page, emits result back to AgentWorker.
        args carries: cx, cy, value, el_id, el_name, el_cls, el_tag, el_type
        """
        result = "ERROR: unknown tool"
        try:
            wp = self.web_page

            if tool_name == "click":
                result = wp.agent_click(args)

            elif tool_name == "type":
                result = wp.agent_type(args)

            elif tool_name == "scroll":
                result = wp.agent_scroll(args)

            elif tool_name == "select":
                result = wp.agent_select(args)

            elif tool_name == "open_url":
                url = args.get("url") or args.get("value", "")
                wp.open_url(url)
                wp.wait_for_load(8000)
                self.tabs.setCurrentWidget(self.web_page)
                result = "success"

            elif tool_name == "bug_report":
                self._status.setText(f"\U0001f41b Bug: {args.get('value','')[:60]}")
                result = "success"

            elif tool_name == "search_emails":
                result = "search_emails not implemented"

            else:
                result = f"ERROR: tool '{tool_name}' not implemented"

        except Exception as exc:
            result = f"ERROR: {exc}"

        self.agent.tool_result_ready.emit(result)

    # ── Browser state / screenshot bridges ───────────────────────────────────

    def _provide_browser_state(self):
        screenshot_bytes = self.web_page.get_screenshot()
        dom              = self.web_page.get_dom()
        self.agent._on_browser_state_ready(screenshot_bytes, json.dumps(dom))

    def _provide_screenshot(self):
        self.agent.screenshot_ready.emit(self.web_page.get_screenshot())

    # ── Rerun / URL ───────────────────────────────────────────────────────────

    def _on_rerun_requested(self, conv_id: int):
        """Switch to browser tab and enqueue re-run."""
        self.tabs.setCurrentWidget(self.web_page)
        self.agent.enqueue_rerun(conv_id)

    def _on_url_changed(self, conv_id: int, url: str):
        """Immediately navigate when user sets the URL."""
        if url:
            self.web_page.open_url(url)
            self.tabs.setCurrentWidget(self.web_page)

    # ── Setup dialog ──────────────────────────────────────────────────────────

    def _show_setup_dialog(self):
        choice = QMessageBox.question(
            self, "Model Setup",
            "No local model found. Download it locally?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if choice == QMessageBox.Yes:
            self.agent.setup_result_ready.emit("local", "")
        else:
            url, ok = QInputDialog.getText(
                self, "Hugging Face Space API", "Enter your Space base URL:")
            if ok and url.strip():
                clean = url.strip().rstrip("/")
                for suffix in ("/gradio_api/call/generate", "/api/predict",
                               "/run/predict", "/predict"):
                    if clean.endswith(suffix):
                        clean = clean[:-len(suffix)].rstrip("/")
                self.agent.setup_result_ready.emit("space", clean)
            else:
                self.agent.setup_result_ready.emit("none", "")

    # ── Sidebar helpers ───────────────────────────────────────────────────────

    def _new_chat(self):
        self.chat.current_conv = None
        self.chat.title_edit.setText("New Test")
        self.chat.url_edit.setText("")
        self.chat.rerun_btn.hide()
        self.chat._chat_history.clear()
        while self.chat.msgs_lay.count() > 1:
            item = self.chat.msgs_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._status.setText("New test")

    def _load_conv(self, cid: int):
        self.chat.load_conversation(cid)
        self.chat._chat_history = [
            {"role": role, "content": content}
            for role, content, _ in self.db.get_messages(cid)
        ]
        conv = self.db.get_conversation(cid)
        if conv and conv["url"]:
            self.web_page.open_url(conv["url"])
            self.tabs.setCurrentWidget(self.web_page)
        self._status.setText(f"Test #{cid} loaded")

    # ── Status bar updates ────────────────────────────────────────────────────

    def _on_msg(self, text: str):
        self.sidebar.refresh()
        self._status.setText(f"Sent \u00b7 {datetime.now().strftime('%H:%M:%S')}")

    def _on_agent_log(self, msg: str, color: str):
        self._status.setText(msg)

    def _on_model_ready(self):
        self._status.setText("\u2713  Orvion AI ready")

    def _on_phase_changed(self, phase: str, detail: str):
        labels = {
            "checking":    "\U0001f50d Checking hardware\u2026",
            "downloading": "\u2b07  Downloading model\u2026",
            "loading":     "\u2699  Loading model\u2026",
            "ready":       "\u2713  Orvion AI ready",
            "error":       "\u274c  Error \u2014 see chat panel",
        }
        self._status.setText(labels.get(phase, phase))

    def _on_download_progress(self, pct: float, speed: float, log: str):
        self._status.setText(
            f"\u2b07  Downloading\u2026 {pct:.0f}%  @  {speed:.1f} MB/s"
            if speed > 0 else f"\u2b07  Downloading\u2026 {pct:.0f}%"
        )

    # ── Event filter / keyboard ───────────────────────────────────────────────

    def eventFilter(self, obj, ev):
        if ev.type() == QEvent.Resize and obj == self.centralWidget():
            w, h, s = obj.width(), obj.height(), 5
            self._eh_l.setGeometry(0,     s, s, h - s)
            self._eh_r.setGeometry(w - s, s, s, h - s)
            self._eh_t.setGeometry(0,     0, w, s)
        return super().eventFilter(obj, ev)

    def closeEvent(self, event):
        if self.agent is not None:
            self.agent.running = False; self.agent.quit(); self.agent.wait(3000)
        event.accept()

    def keyPressEvent(self, e):
        if e.modifiers() == Qt.ControlModifier:
            if e.key() == Qt.Key_Q:   self.close()
            elif e.key() == Qt.Key_N: self._new_chat()
            elif e.key() == Qt.Key_S: self.editor._save()
        super().keyPressEvent(e)