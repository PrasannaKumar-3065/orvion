import json
import time

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

        toolbar    = QWidget(); toolbar.setObjectName("editor_toolbar")
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

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _run_js(self, js: str):
        """Run JS synchronously, return result."""
        loop   = QEventLoop()
        result = {}
        def cb(r): result["v"] = r; loop.quit()
        self.browser.page().runJavaScript(js, cb)
        loop.exec_()
        return result.get("v")

    def _safe_sel(self, selector: str) -> str:
        """Escape selector for JS string."""
        return selector.replace('"', '\\"').replace("'", "\\'")

    def _safe_str(self, text: str) -> str:
        """Escape text for JS string."""
        return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")

    # ── Agent-facing tool methods ────────────────────────────────────────────

    def click_selector(self, selector: str) -> str:
        r = self._run_js(
            f'(function(){{'
            f'  var el=document.querySelector("{self._safe_sel(selector)}");'
            f'  if(!el) return "NOT_FOUND";'
            f'  el.click(); return "success";'
            f'}})();'
        )
        return r or "NOT_FOUND"

    def double_click_selector(self, selector: str) -> str:
        r = self._run_js(
            f'(function(){{'
            f'  var el=document.querySelector("{self._safe_sel(selector)}");'
            f'  if(!el) return "NOT_FOUND";'
            f'  el.dispatchEvent(new MouseEvent("dblclick",{{bubbles:true,cancelable:true}}));'
            f'  return "success";'
            f'}})();'
        )
        return r or "NOT_FOUND"

    def right_click_selector(self, selector: str) -> str:
        r = self._run_js(
            f'(function(){{'
            f'  var el=document.querySelector("{self._safe_sel(selector)}");'
            f'  if(!el) return "NOT_FOUND";'
            f'  el.dispatchEvent(new MouseEvent("contextmenu",{{bubbles:true,cancelable:true,button:2}}));'
            f'  return "success";'
            f'}})();'
        )
        return r or "NOT_FOUND"

    def hover_selector(self, selector: str) -> str:
        r = self._run_js(
            f'(function(){{'
            f'  var el=document.querySelector("{self._safe_sel(selector)}");'
            f'  if(!el) return "NOT_FOUND";'
            f'  el.dispatchEvent(new MouseEvent("mouseover",{{bubbles:true}}));'
            f'  el.dispatchEvent(new MouseEvent("mouseenter",{{bubbles:false}}));'
            f'  return "success";'
            f'}})();'
        )
        return r or "NOT_FOUND"

    def type_selector(self, selector: str, text: str) -> str:
        r = self._run_js(
            f'(function(){{'
            f'  var el=document.querySelector("{self._safe_sel(selector)}");'
            f'  if(!el) return "NOT_FOUND";'
            f'  el.focus();'
            f'  el.value="{self._safe_str(text)}";'
            f'  el.dispatchEvent(new Event("input",{{bubbles:true}}));'
            f'  el.dispatchEvent(new Event("change",{{bubbles:true}}));'
            f'  return "success";'
            f'}})();'
        )
        return r or "NOT_FOUND"

    def clear_and_type(self, selector: str, text: str) -> str:
        r = self._run_js(
            f'(function(){{'
            f'  var el=document.querySelector("{self._safe_sel(selector)}");'
            f'  if(!el) return "NOT_FOUND";'
            f'  el.focus();'
            f'  el.value="";'
            f'  el.dispatchEvent(new Event("input",{{bubbles:true}}));'
            f'  el.value="{self._safe_str(text)}";'
            f'  el.dispatchEvent(new Event("input",{{bubbles:true}}));'
            f'  el.dispatchEvent(new Event("change",{{bubbles:true}}));'
            f'  return "success";'
            f'}})();'
        )
        return r or "NOT_FOUND"

    def select_option(self, selector: str, value: str) -> str:
        r = self._run_js(
            f'(function(){{'
            f'  var el=document.querySelector("{self._safe_sel(selector)}");'
            f'  if(!el) return "NOT_FOUND";'
            f'  var found=false;'
            f'  for(var i=0;i<el.options.length;i++){{'
            f'    if(el.options[i].value==="{self._safe_str(value)}" ||'
            f'       el.options[i].text==="{self._safe_str(value)}")'
            f'    {{ el.selectedIndex=i; found=true; break; }}'
            f'  }}'
            f'  if(!found) return "VALUE_NOT_FOUND";'
            f'  el.dispatchEvent(new Event("change",{{bubbles:true}}));'
            f'  return "success";'
            f'}})();'
        )
        return r or "NOT_FOUND"

    def press_key(self, key: str, selector: str = None) -> str:
        """Press a key globally or on a specific element."""
        KEY_CODES = {
            "Enter": 13, "Tab": 9, "Escape": 27, "Space": 32,
            "ArrowDown": 40, "ArrowUp": 38, "ArrowLeft": 37, "ArrowRight": 39,
            "Backspace": 8, "Delete": 46, "Home": 36, "End": 35,
        }
        key_code = KEY_CODES.get(key, 0)
        if selector:
            r = self._run_js(
                f'(function(){{'
                f'  var el=document.querySelector("{self._safe_sel(selector)}");'
                f'  if(!el) return "NOT_FOUND";'
                f'  el.focus();'
                f'  el.dispatchEvent(new KeyboardEvent("keydown",{{key:"{key}",keyCode:{key_code},bubbles:true}}));'
                f'  el.dispatchEvent(new KeyboardEvent("keyup",{{key:"{key}",keyCode:{key_code},bubbles:true}}));'
                f'  return "success";'
                f'}})();'
            )
        else:
            r = self._run_js(
                f'(function(){{'
                f'  document.dispatchEvent(new KeyboardEvent("keydown",{{key:"{key}",keyCode:{key_code},bubbles:true}}));'
                f'  document.dispatchEvent(new KeyboardEvent("keyup",{{key:"{key}",keyCode:{key_code},bubbles:true}}));'
                f'  return "success";'
                f'}})();'
            )
        return r or "success"

    def scroll_down(self, pixels: int = 300) -> str:
        self._run_js(f"window.scrollBy(0, {int(pixels)});")
        return "success"

    def scroll_up(self, pixels: int = 300) -> str:
        self._run_js(f"window.scrollBy(0, -{int(pixels)});")
        return "success"

    def scroll_to_top(self) -> str:
        self._run_js("window.scrollTo(0, 0);")
        return "success"

    def scroll_to_bottom(self) -> str:
        self._run_js("window.scrollTo(0, document.body.scrollHeight);")
        return "success"

    def scroll_to_element(self, selector: str) -> str:
        r = self._run_js(
            f'(function(){{'
            f'  var el=document.querySelector("{self._safe_sel(selector)}");'
            f'  if(!el) return "NOT_FOUND";'
            f'  el.scrollIntoView({{behavior:"smooth",block:"center"}});'
            f'  return "success";'
            f'}})();'
        )
        return r or "NOT_FOUND"

    def verify_text_present(self, text: str) -> str:
        r = self._run_js(
            f'(function(){{'
            f'  var body=document.body.innerText||"";'
            f'  return body.includes("{self._safe_str(text)}") ? "success" : "FAIL: text not found";'
            f'}})();'
        )
        return r or "FAIL: no result"

    def verify_text_absent(self, text: str) -> str:
        r = self._run_js(
            f'(function(){{'
            f'  var body=document.body.innerText||"";'
            f'  return !body.includes("{self._safe_str(text)}") ? "success" : "FAIL: text unexpectedly present";'
            f'}})();'
        )
        return r or "FAIL: no result"

    def verify_element_visible(self, selector: str) -> str:
        r = self._run_js(
            f'(function(){{'
            f'  var el=document.querySelector("{self._safe_sel(selector)}");'
            f'  if(!el) return "FAIL: element not found";'
            f'  var r=el.getBoundingClientRect();'
            f'  var visible=(r.width>0&&r.height>0&&r.top<window.innerHeight&&r.bottom>0);'
            f'  return visible ? "success" : "FAIL: element not visible";'
            f'}})();'
        )
        return r or "FAIL: no result"

    def verify_element_enabled(self, selector: str) -> str:
        r = self._run_js(
            f'(function(){{'
            f'  var el=document.querySelector("{self._safe_sel(selector)}");'
            f'  if(!el) return "FAIL: element not found";'
            f'  return !el.disabled ? "success" : "FAIL: element is disabled";'
            f'}})();'
        )
        return r or "FAIL: no result"

    def verify_url_contains(self, substring: str) -> str:
        current = self.browser.url().toString()
        if substring in current:
            return "success"
        return f"FAIL: URL '{current}' does not contain '{substring}'"

    def verify_page_title(self, expected: str) -> str:
        r = self._run_js("document.title;")
        title = str(r or "")
        if expected in title:
            return "success"
        return f"FAIL: title is '{title}', expected to contain '{expected}'"

    def verify_input_value(self, selector: str, expected: str) -> str:
        r = self._run_js(
            f'(function(){{'
            f'  var el=document.querySelector("{self._safe_sel(selector)}");'
            f'  if(!el) return "FAIL: element not found";'
            f'  return el.value==="{self._safe_str(expected)}" ? "success"'
            f'       : "FAIL: value is \'"+el.value+"\', expected \'{expected}\'";'
            f'}})();'
        )
        return r or "FAIL: no result"

    def verify_element_count(self, selector: str, expected_count: int) -> str:
        r = self._run_js(
            f'(function(){{'
            f'  var els=document.querySelectorAll("{self._safe_sel(selector)}");'
            f'  var n=els.length;'
            f'  return n==={int(expected_count)} ? "success"'
            f'       : "FAIL: found "+n+" elements, expected {expected_count}";'
            f'}})();'
        )
        return r or "FAIL: no result"

    def get_text(self, selector: str) -> str:
        r = self._run_js(
            f'(function(){{'
            f'  var el=document.querySelector("{self._safe_sel(selector)}");'
            f'  if(!el) return "NOT_FOUND";'
            f'  return (el.innerText||el.textContent||el.value||"").trim();'
            f'}})();'
        )
        return str(r) if r is not None else "NOT_FOUND"

    def get_current_url(self) -> str:
        return self.browser.url().toString()

    def get_page_title(self) -> str:
        r = self._run_js("document.title;")
        return str(r or "")

    def go_back(self) -> str:
        self.browser.back()
        return "success"

    def wait_for_element(self, selector: str, timeout: int = 10) -> str:
        """Poll for up to `timeout` seconds for element to appear."""
        loop    = QEventLoop()
        found   = [False]
        elapsed = [0]
        interval = 500  # ms

        def check():
            elapsed[0] += interval
            r = self._run_js(
                f'!!document.querySelector("{self._safe_sel(selector)}")'
            )
            if r:
                found[0] = True
                loop.quit()
            elif elapsed[0] >= timeout * 1000:
                loop.quit()

        timer = QTimer()
        timer.timeout.connect(check)
        timer.start(interval)
        loop.exec_()
        timer.stop()
        return "success" if found[0] else f"FAIL: '{selector}' not found after {timeout}s"

    def wait_for_text(self, text: str, timeout: int = 10) -> str:
        loop    = QEventLoop()
        found   = [False]
        elapsed = [0]
        interval = 500

        def check():
            elapsed[0] += interval
            r = self._run_js(
                f'document.body.innerText.includes("{self._safe_str(text)}")'
            )
            if r:
                found[0] = True
                loop.quit()
            elif elapsed[0] >= timeout * 1000:
                loop.quit()

        timer = QTimer()
        timer.timeout.connect(check)
        timer.start(interval)
        loop.exec_()
        timer.stop()
        return "success" if found[0] else f"FAIL: text '{text}' not found after {timeout}s"

    def wait_for_url_change(self, expected_substring: str, timeout: int = 10) -> str:
        loop    = QEventLoop()
        found   = [False]
        elapsed = [0]
        interval = 500

        def check():
            elapsed[0] += interval
            current = self.browser.url().toString()
            if expected_substring in current:
                found[0] = True
                loop.quit()
            elif elapsed[0] >= timeout * 1000:
                loop.quit()

        timer = QTimer()
        timer.timeout.connect(check)
        timer.start(interval)
        loop.exec_()
        timer.stop()
        return "success" if found[0] else f"FAIL: URL did not contain '{expected_substring}' after {timeout}s"

    def wait_for_network_idle(self, timeout: int = 10) -> str:
        """Wait for page load to finish."""
        self.wait_for_load(timeout * 1000)
        return "success"

    def browser_wait(self, seconds: float) -> str:
        loop = QEventLoop()
        QTimer.singleShot(int(seconds * 1000), loop.quit)
        loop.exec_()
        return "success"

    def get_dom(self):
        loop   = QEventLoop()
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

    def open_url(self, url: str) -> str:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        self.browser.setUrl(QUrl(url))
        return "success"

    def wait_for_load(self, timeout: int = 15000):
        loop = QEventLoop()
        def on_finished(_): QTimer.singleShot(500, loop.quit)
        self.browser.loadFinished.connect(on_finished)
        QTimer.singleShot(timeout, loop.quit)
        loop.exec_()
        try:
            self.browser.loadFinished.disconnect(on_finished)
        except Exception:
            pass