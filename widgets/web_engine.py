import json

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QProgressBar
)
from PyQt5.QtCore import Qt, QEventLoop, QTimer, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QBuffer, QIODevice

from inference_helpers import DOM_JS
from styles import EDITOR_LIGHT, EDITOR_DARK


class WebEngine(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("https://duckduckgo.com"))
        self.browser.loadFinished.connect(self._on_load_finished)
        self._light = False
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)

        toolbar   = QWidget(); toolbar.setObjectName("editor_toolbar")
        toollayout = QHBoxLayout(toolbar)
        toollayout.setContentsMargins(10, 0, 8, 0); toollayout.setSpacing(4)

        label = QLabel("BROWSER"); label.setObjectName("editor_title_label")
        toollayout.addWidget(label)

        sep = QFrame(); sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("min-width:1px; max-width:1px; margin:10px 4px;")
        toollayout.addWidget(sep)

        self.goback  = QPushButton("←"); self.goback.setObjectName("fmt_btn")
        self.forward = QPushButton("→"); self.forward.setObjectName("fmt_btn")
        self.reload  = QPushButton("↻"); self.reload.setObjectName("fmt_btn")
        for b in (self.goback, self.forward, self.reload):
            b.setCursor(Qt.PointingHandCursor); toollayout.addWidget(b)

        self.goback.clicked.connect(self.browser.back)
        self.forward.clicked.connect(self.browser.forward)
        self.reload.clicked.connect(self.browser.reload)

        self.title_inp = QLineEdit("https://duckduckgo.com")
        self.title_inp.setObjectName("doc_title_input")
        self.title_inp.returnPressed.connect(self._load_url)
        toollayout.addWidget(self.title_inp)

        self.theme_btn = QPushButton("☀  Light"); self.theme_btn.setObjectName("theme_toggle_btn")
        self.theme_btn.setCursor(Qt.PointingHandCursor); self.theme_btn.clicked.connect(self._toggle)
        toollayout.addWidget(self.theme_btn)

        lay.addWidget(toolbar)

        self.progress = QProgressBar()
        self.progress.setFixedHeight(3); self.progress.setTextVisible(False)
        self.progress.setStyleSheet("QProgressBar::chunk { background-color: #7C5CFC; }")
        self.browser.loadStarted.connect(lambda: self.progress.show())
        self.browser.loadProgress.connect(self.progress.setValue)
        self.browser.loadFinished.connect(lambda _: self.progress.hide())
        lay.addWidget(self.progress)
        lay.addWidget(self.browser)

    def _toggle(self):
        self._light = not self._light
        self.setStyleSheet(EDITOR_LIGHT if self._light else EDITOR_DARK)
        self.theme_btn.setText("🌙  Dark" if self._light else "☀  Light")

    def _on_load_finished(self, _):
        self.title_inp.setText(self.browser.url().toString())

    def _load_url(self):
        text = self.title_inp.text().strip()
        if not text:
            return
        if not text.startswith(("http://", "https://")):
            text = ("https://" + text) if "." in text else (
                "https://www.google.com/search?q=" + QUrl.toPercentEncoding(text).data().decode()
            )
        self.browser.setUrl(QUrl(text))

    # ── Agent-facing methods ─────────────────────────────────────────────────

    def click_selector(self, selector: str):
        loop = QEventLoop()
        result = {}
        def cb(r): result["v"] = r; loop.quit()
        self.browser.page().runJavaScript(
            f'(function(){{var el=document.querySelector("{selector}");'
            f'if(!el)return "NOT_FOUND";el.click();return "OK";}})();', cb
        )
        loop.exec_()
        return result.get("v")

    def type_selector(self, selector: str, text: str):
        loop = QEventLoop()
        result = {}
        def cb(r): result["v"] = r; loop.quit()
        safe_text = text.replace('"', '\\"').replace("\n", "\\n")
        self.browser.page().runJavaScript(
            f'(function(){{var el=document.querySelector("{selector}");'
            f'if(!el)return "NOT_FOUND";el.value="{safe_text}";'
            f'el.dispatchEvent(new Event("input",{{bubbles:true}}));return "OK";}})();', cb
        )
        loop.exec_()
        return result.get("v")

    def get_dom(self):
        loop = QEventLoop()
        result = {}
        def cb(r): result["v"] = r; loop.quit()
        self.browser.page().runJavaScript(DOM_JS, cb)
        loop.exec_()
        raw = result.get("v", "[]")
        try:
            return json.loads(raw) if isinstance(raw, str) else (raw or [])
        except Exception:
            return []

    def get_screenshot(self) -> bytes:
        pixmap = self.browser.grab()
        buf    = QBuffer()
        buf.open(QIODevice.WriteOnly)
        pixmap.save(buf, "PNG")
        return bytes(buf.data())

    def open_url(self, url: str):
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        self.browser.setUrl(QUrl(url))

    def wait_for_load(self, timeout=15000):
        loop = QEventLoop()
        def on_finished(_): QTimer.singleShot(500, loop.quit)
        self.browser.loadFinished.connect(on_finished)
        QTimer.singleShot(timeout, loop.quit)
        loop.exec_()
        try:
            self.browser.loadFinished.disconnect(on_finished)
        except Exception:
            pass
