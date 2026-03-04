import json
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QTabWidget, QStatusBar, QSizeGrip,
    QLabel, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt, QEvent

from database import Database
from email_hub import EmailHub
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
        self.mail_hub = EmailHub(self.db)
        self.tabs.addTab(self.editor,   "Editor")
        self.tabs.addTab(self.web_page, "Browser")
        self.tabs.addTab(self.mail_hub, 'Emails')

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
        """
        Runs on the main thread. Dispatches every supported tool to web_page,
        then emits the result back to the sleeping AgentWorker thread.
        """
        result = "ERROR: unknown tool"
        try:
            wp = self.web_page
            a  = args  # shorthand

            # ── Navigation ────────────────────────────────────────────────────
            if tool_name == "open_url":
                wp.open_url(a["url"])
                wp.wait_for_load(8000)
                result = "success"

            elif tool_name == "go_back":
                result = wp.go_back()
                wp.wait_for_load(5000)

            # ── Click family ──────────────────────────────────────────────────
            elif tool_name == "click":
                result = wp.click_selector(a["selector"])

            elif tool_name == "double_click":
                result = wp.double_click_selector(a["selector"])

            elif tool_name == "right_click":
                result = wp.right_click_selector(a["selector"])

            elif tool_name == "hover":
                result = wp.hover_selector(a["selector"])

            # ── Typing ────────────────────────────────────────────────────────
            elif tool_name == "type":
                result = wp.type_selector(a["selector"], a.get("text", ""))

            elif tool_name == "clear_and_type":
                result = wp.clear_and_type(a["selector"], a.get("text", ""))

            elif tool_name == "press_key":
                result = wp.press_key(a.get("key", "Enter"), a.get("selector"))

            elif tool_name == "select_option":
                result = wp.select_option(a["selector"], a.get("value", ""))

            # ── Scroll ────────────────────────────────────────────────────────
            elif tool_name == "scroll_down":
                result = wp.scroll_down(a.get("pixels", 300))

            elif tool_name == "scroll_up":
                result = wp.scroll_up(a.get("pixels", 300))

            elif tool_name == "scroll_to_top":
                result = wp.scroll_to_top()

            elif tool_name == "scroll_to_bottom":
                result = wp.scroll_to_bottom()

            elif tool_name == "scroll_to_element":
                result = wp.scroll_to_element(a["selector"])

            # ── Verify ────────────────────────────────────────────────────────
            elif tool_name == "verify_text_present":
                result = wp.verify_text_present(a.get("text", ""))

            elif tool_name == "verify_text_absent":
                result = wp.verify_text_absent(a.get("text", ""))

            elif tool_name == "verify_element_visible":
                result = wp.verify_element_visible(a["selector"])

            elif tool_name == "verify_element_enabled":
                result = wp.verify_element_enabled(a["selector"])

            elif tool_name == "verify_url_contains":
                result = wp.verify_url_contains(a.get("substring", ""))

            elif tool_name == "verify_page_title":
                result = wp.verify_page_title(a.get("expected", ""))

            elif tool_name == "verify_input_value":
                result = wp.verify_input_value(a["selector"], a.get("expected", ""))

            elif tool_name == "verify_element_count":
                result = wp.verify_element_count(a["selector"], a.get("expected_count", 1))

            # ── Get ───────────────────────────────────────────────────────────
            elif tool_name == "get_text":
                result = wp.get_text(a["selector"])

            elif tool_name == "get_current_url":
                result = wp.get_current_url()

            elif tool_name == "get_page_title":
                result = wp.get_page_title()

            # ── Wait ──────────────────────────────────────────────────────────
            elif tool_name == "wait":
                result = wp.browser_wait(float(a.get("seconds", 1)))

            elif tool_name == "wait_for_element":
                result = wp.wait_for_element(a["selector"], int(a.get("timeout", 10)))

            elif tool_name == "wait_for_text":
                result = wp.wait_for_text(a.get("text", ""), int(a.get("timeout", 10)))

            elif tool_name == "wait_for_url_change":
                result = wp.wait_for_url_change(a.get("expected_substring", ""), int(a.get("timeout", 10)))

            elif tool_name == "wait_for_network_idle":
                result = wp.wait_for_network_idle(int(a.get("timeout", 10)))

            # ── Meta tools (no browser action, always success) ────────────────
            elif tool_name in ("raise_bug_ticket", "mark_step_pass", "mark_step_fail",
                               "mark_flow_blocked", "add_test_comment", "capture_evidence",
                               "screenshot_diff"):
                # Log to status bar for visibility
                label = {
                    "raise_bug_ticket": f"🐛 Bug: {a.get('title','')[:60]}",
                    "mark_step_pass":   f"✅ Pass: {a.get('message','')[:60]}",
                    "mark_step_fail":   f"❌ Fail: {a.get('message','')[:60]}",
                    "mark_flow_blocked":f"🚫 Blocked: {a.get('message','')[:60]}",
                    "add_test_comment": f"💬 {a.get('comment','')[:60]}",
                    "capture_evidence": f"📸 Evidence captured",
                    "screenshot_diff":  f"🖼 Screenshot diff",
                }.get(tool_name, tool_name)
                self._status.setText(label)
                result = "success"

            else:
                result = f"ERROR: tool '{tool_name}' not implemented"

        except KeyError as e:
            result = f"ERROR: missing arg {e} for tool '{tool_name}'"
        except Exception as e:
            result = f"ERROR: {e}"

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