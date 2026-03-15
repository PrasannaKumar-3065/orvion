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


# ── Selector builder ─────────────────────────────────────────────────────────
#
# Priority: id > name > class(es) > tag+type > coordinates fallback
# Returns a JS expression string: either a CSS selector string or a
# coordinate-based elementFromPoint call — always resolves to a single element.

def _build_selector_js(el_id="", el_name="", el_cls="",
                       el_tag="", el_type="", cx=0, cy=0) -> str:
    """
    Build the safest, most specific CSS selector for a given element,
    falling back gracefully through attribute priority.

    Returns a JS snippet that evaluates to the element (or null).
    """
    def esc(s):
        # CSS.escape equivalent for use inside a JS string
        return s.replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")

    # 1. id — most specific, guaranteed unique
    if el_id:
        return f'document.getElementById("{esc(el_id)}")'

    # 2. name attribute — very reliable for form inputs
    if el_name and el_tag in ("input", "textarea", "select", "button"):
        tag = el_tag or "*"
        sel = f'{tag}[name="{esc(el_name)}"]'
        return f'document.querySelector("{sel}")'

    # 3. name on any element
    if el_name:
        return f'document.querySelector("[name=\\"{esc(el_name)}\\"]")'

    # 4. tag + type — e.g. input[type="password"]
    if el_tag and el_type:
        sel = f'{el_tag}[type="{esc(el_type)}"]'
        return f'document.querySelector("{sel}")'

    # 5. class(es) + tag — use first non-generic class
    if el_cls and el_tag:
        first_cls = [c for c in el_cls.split() if len(c) > 2]
        if first_cls:
            sel = f'{el_tag}.{first_cls[0]}'
            return f'document.querySelector("{sel}")'

    # 6. bare tag
    if el_tag:
        return f'document.querySelector("{el_tag}")'

    # 7. coordinate fallback — last resort
    return f'document.elementFromPoint({cx}, {cy})'


# ── JS action helper ─────────────────────────────────────────────────────────

# React / Vue / Angular all intercept native value assignment through
# Object.getOwnPropertyDescriptor on the prototype — this is the canonical
# way to trigger their onChange handlers correctly.
_SET_VALUE_JS = """
function _orvionSetValue(el, val) {
    // Try native setter first (React controlled inputs)
    var proto = el.tagName === 'INPUT'    ? window.HTMLInputElement.prototype
              : el.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype
              : el.tagName === 'SELECT'   ? window.HTMLSelectElement.prototype
              : null;
    if (proto) {
        var setter = Object.getOwnPropertyDescriptor(proto, 'value');
        if (setter && setter.set) {
            setter.set.call(el, val);
        } else {
            el.value = val;
        }
    } else {
        el.textContent = val;
    }
    el.dispatchEvent(new Event('input',  { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
}
"""


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

        self.theme_btn = QPushButton("☀  Light")
        self.theme_btn.setObjectName("theme_toggle_btn")
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.clicked.connect(self._toggle)
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

    # ── UI helpers ────────────────────────────────────────────────────────────

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
                "https://www.google.com/search?q="
                + QUrl.toPercentEncoding(text).data().decode()
            )
        self.browser.setUrl(QUrl(text))

    # ── JS runner ─────────────────────────────────────────────────────────────

    def _run_js(self, js: str) -> object:
        """Run JS synchronously on the main thread, return the result."""
        loop   = QEventLoop()
        result = {}
        def cb(r):
            result["v"] = r
            loop.quit()
        self.browser.page().runJavaScript(js, cb)
        loop.exec_()
        return result.get("v")

    # ── DOM / screenshot ──────────────────────────────────────────────────────

    def get_dom(self) -> list:
        # DOM_JS is an arrow-function expression: "() => { ... return pool; }"
        # Qt's runJavaScript evaluates but does NOT auto-call function expressions
        # the way Playwright's page.evaluate() does.
        # Wrapping as (...)() makes it an IIFE that actually executes.
        raw = self._run_js(f"({DOM_JS})()")
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except Exception:
                return []
        return raw if isinstance(raw, list) else []

    def get_screenshot(self) -> bytes:
        pixmap = self.browser.grab()
        buf    = QBuffer()
        buf.open(QIODevice.WriteOnly)
        pixmap.save(buf, "PNG")
        return bytes(buf.data())

    def get_state(self) -> tuple:
        screenshot = self.get_screenshot()
        dom_list   = self.get_dom()
        return screenshot, json.dumps(dom_list, ensure_ascii=False)

    # ── Navigation ────────────────────────────────────────────────────────────

    def open_url(self, url: str) -> str:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        self.browser.setUrl(QUrl(url))
        return "success"

    def wait_for_load(self, timeout: int = 15000):
        loop = QEventLoop()
        def on_finished(_):
            QTimer.singleShot(500, loop.quit)
        self.browser.loadFinished.connect(on_finished)
        QTimer.singleShot(timeout, loop.quit)
        loop.exec_()
        try:
            self.browser.loadFinished.disconnect(on_finished)
        except Exception:
            pass

    def browser_wait(self, seconds: float) -> str:
        loop = QEventLoop()
        QTimer.singleShot(int(seconds * 1000), loop.quit)
        loop.exec_()
        return "success"

    # ── Agent actions (called by main_window._execute_tool) ───────────────────
    #
    # Each method receives the full args dict from tool_request, which carries:
    #   cx, cy              — viewport coordinates from DOM pipeline
    #   el_id, el_name,     — selector hints, priority order:
    #   el_cls, el_tag,       id > name > tag+type > class+tag > coords
    #   el_type
    #   value               — text to type / option to select / scroll px

    def agent_click(self, args: dict) -> str:
        """
        Click an element.

        Strategy:
          1. JS: resolve element, scroll into view, get its viewport centre.
          2. Qt: send real mouse press+release to focusProxy() at those coords.

        Using Qt mouse events (not JS .click()) means navigation triggered by
        the click doesn't cause the JS callback to vanish before it fires.
        """
        from PyQt5.QtGui import QMouseEvent
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QEvent, QPoint, QPointF

        el_js = _build_selector_js(
            el_id   = args.get("el_id",   ""),
            el_name = args.get("el_name", ""),
            el_cls  = args.get("el_cls",  ""),
            el_tag  = args.get("el_tag",  ""),
            el_type = args.get("el_type", ""),
            cx      = args.get("cx", 0),
            cy      = args.get("cy", 0),
        )

        # Step 1 — scroll into view and get the element's centre coordinate
        pos_js = f"""
        (function() {{
            var el = {el_js};
            if (!el) return null;
            el.scrollIntoView({{block:'center', inline:'center', behavior:'instant'}});
            el.focus();
            var r = el.getBoundingClientRect();
            return {{x: Math.round(r.left + r.width/2),
                     y: Math.round(r.top  + r.height/2),
                     tag: el.tagName}};
        }})()
        """
        pos = self._run_js(pos_js)

        # Fall back to stored coordinates if JS can't find element
        if pos and isinstance(pos, dict) and "x" in pos:
            cx = int(pos["x"])
            cy = int(pos["y"])
        else:
            cx = args.get("cx", 0)
            cy = args.get("cy", 0)

        # Step 2 — Qt mouse events on focusProxy (the Chromium render surface)
        target = self.browser.focusProxy() or self.browser
        pt     = QPointF(cx, cy)
        press  = QMouseEvent(QEvent.MouseButtonPress,   pt, Qt.LeftButton,
                             Qt.LeftButton, Qt.NoModifier)
        release = QMouseEvent(QEvent.MouseButtonRelease, pt, Qt.LeftButton,
                              Qt.LeftButton, Qt.NoModifier)
        QApplication.sendEvent(target, press)
        QApplication.sendEvent(target, release)

        tag = pos.get("tag", "?") if isinstance(pos, dict) else "?"
        return f"clicked:{tag}@({cx},{cy})"

    def agent_type(self, args: dict) -> str:
        """
        Type text into a form element.

        Two-stage strategy:
          Stage A — JS:
            1. Resolve element by selector (id > name > tag+type > …)
            2. Scroll into view, focus, click
            3. Clear with native prototype setter (works for React controlled inputs)
            4. Build the final string from scratch in the loop (never read el.value
               back — reading after a failed clear returns stale text and causes
               accumulation like "tomsmithtomsmith")
            5. Dispatch keydown → keypress → native-set(full_so_far) → InputEvent
               → keyup for each character, then a final change event

          Stage B — Qt key events to focusProxy():
            The actual Chromium render widget so keys go through the real
            browser input pipeline as a visual fallback.
        """
        from PyQt5.QtGui import QKeyEvent
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QEvent

        text  = args.get("value", "")
        el_js = _build_selector_js(
            el_id   = args.get("el_id",   ""),
            el_name = args.get("el_name", ""),
            el_cls  = args.get("el_cls",  ""),
            el_tag  = args.get("el_tag",  ""),
            el_type = args.get("el_type", ""),
            cx      = args.get("cx", 0),
            cy      = args.get("cy", 0),
        )

        # Build the char list as a safe JS literal via json.dumps
        chars_js = json.dumps(list(text))

        type_js = f"""
        (function() {{
            var el = {el_js};
            if (!el) return 'ERROR: element not found';

            el.scrollIntoView({{block:'center', inline:'center', behavior:'instant'}});
            el.focus();
            el.click();

            // Resolve native value setter once
            var nativeSetter = null;
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {{
                var proto = el.tagName === 'INPUT'
                    ? window.HTMLInputElement.prototype
                    : window.HTMLTextAreaElement.prototype;
                var desc = Object.getOwnPropertyDescriptor(proto, 'value');
                if (desc && desc.set) nativeSetter = desc.set;
            }}

            function setVal(v) {{
                if (nativeSetter) nativeSetter.call(el, v);
                else el.value = v;
            }}

            // Clear existing value
            setVal('');
            el.dispatchEvent(new Event('input', {{bubbles: true}}));

            // Type char by char — accumulate into 'built' so we never read
            // el.value back (reading after a failed clear returns stale text)
            var chars = {chars_js};
            var built = '';
            for (var i = 0; i < chars.length; i++) {{
                var ch = chars[i];
                built += ch;
                el.dispatchEvent(new KeyboardEvent('keydown',  {{key: ch, code: 'Key' + ch.toUpperCase(), bubbles: true, cancelable: true}}));
                el.dispatchEvent(new KeyboardEvent('keypress', {{key: ch, code: 'Key' + ch.toUpperCase(), bubbles: true, cancelable: true}}));
                setVal(built);
                el.dispatchEvent(new InputEvent('input', {{data: ch, inputType: 'insertText', bubbles: true}}));
                el.dispatchEvent(new KeyboardEvent('keyup',   {{key: ch, code: 'Key' + ch.toUpperCase(), bubbles: true, cancelable: true}}));
            }}
            el.dispatchEvent(new Event('change', {{bubbles: true}}));
            return built;
        }})()
        """
        result = self._run_js(type_js)

        if result is None or str(result).startswith("ERROR"):
            return f"ERROR: type failed — {result}"

        # Stage B — Qt key events to focusProxy (Chromium render surface)
        loop = QEventLoop()
        QTimer.singleShot(50, loop.quit)
        loop.exec_()

        target = self.browser.focusProxy() or self.browser
        for char in text:
            press   = QKeyEvent(QEvent.KeyPress,   0, Qt.NoModifier, char)
            release = QKeyEvent(QEvent.KeyRelease, 0, Qt.NoModifier, char)
            QApplication.sendEvent(target, press)
            QApplication.sendEvent(target, release)

        return f"typed:{result}"

    def agent_select(self, args: dict) -> str:
        value = args.get("value", "")
        el_js = _build_selector_js(
            el_id   = args.get("el_id",   ""),
            el_name = args.get("el_name", ""),
            el_cls  = args.get("el_cls",  ""),
            el_tag  = args.get("el_tag",  "select"),
            el_type = args.get("el_type", ""),
            cx      = args.get("cx", 0),
            cy      = args.get("cy", 0),
        )
        js = f"""
        (function() {{
            {_SET_VALUE_JS}
            var el = {el_js};
            if (!el) return 'ERROR: element not found';
            if (el.tagName.toLowerCase() !== 'select') {{
                // Maybe elementFromPoint landed on a child — try parent
                var p = el.closest('select');
                if (p) el = p; else return 'ERROR: not a select element';
            }}
            _orvionSetValue(el, {json.dumps(value)});
            return 'selected:' + el.value;
        }})()
        """
        result = self._run_js(js)
        return str(result) if result is not None else "ERROR: js returned null"

    def agent_scroll(self, args: dict) -> str:
        value = args.get("value", "down")
        try:
            px = abs(int(value))
        except (ValueError, TypeError):
            px = 300
        direction = "down" if value not in ("up",) else "up"
        dy = px if direction == "down" else -px
        self._run_js(f"window.scrollBy(0, {dy});")
        return f"scrolled:{direction}:{px}"