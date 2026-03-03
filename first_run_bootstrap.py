#!/usr/bin/env python3
"""
Orvion First-Run Setup Wizard
─────────────────────────────
One screen. Two cards. User picks API or Local. Done.
No pip. No downloads. No subprocess spawning. No zip bomb.
"""

import os, sys, json, pathlib

from PyQt5.QtCore    import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QApplication
)

DEFAULT_SPACE_URL = "https://sanax3065-orivion-api.hf.space"

_BG     = "#0C0C0F"
_PANEL  = "#0F0F17"
_BORDER = "#1A1A26"
_ACCENT = "#6B4EE6"
_TEXT   = "#BCB4E0"
_DIM    = "#504A72"

STYLE = f"""
QWidget   {{ background:{_BG}; color:{_TEXT};
             font-family:'Segoe UI','SF Pro Display',sans-serif; }}
QLabel    {{ background:transparent; }}
QLineEdit {{
    background:{_PANEL}; color:{_TEXT};
    border:1px solid {_BORDER}; border-radius:7px;
    padding:8px 12px; font-size:12px;
}}
QLineEdit:focus {{ border:1px solid {_ACCENT}; }}
QPushButton#primary {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 {_ACCENT},stop:1 #4878E8);
    color:#fff; border-radius:9px; padding:10px 28px;
    font-size:13px; font-weight:700; border:none;
}}
QPushButton#primary:hover  {{ background:#8060FF; }}
QPushButton#primary:disabled {{ background:#2A2840; color:{_DIM}; }}
QPushButton#card {{
    background:#111120; border:1px solid #1C1C2C;
    border-radius:12px; padding:18px 20px;
    text-align:left; color:{_TEXT}; font-size:13px;
}}
QPushButton#card:hover {{ background:#161630; border:1px solid {_ACCENT}; }}
QPushButton#card_sel {{
    background:#18163A; border:2px solid {_ACCENT};
    border-radius:12px; padding:18px 20px;
    text-align:left; color:{_TEXT}; font-size:13px;
}}
"""


class SetupWizard(QWidget):
    def __init__(self, sentinel_path: pathlib.Path, model_dir: pathlib.Path):
        super().__init__()
        self._sentinel  = sentinel_path
        self._model_dir = model_dir
        self._mode      = None

        self.setWindowTitle("Orvion — First Run Setup")
        self.setFixedSize(560, 420)
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        self.setStyleSheet(STYLE)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 32, 36, 28)
        lay.setSpacing(0)

        # Header
        title = QLabel("ORVION")
        title.setStyleSheet(f"color:{_TEXT};font-size:22px;font-weight:800;letter-spacing:6px;")
        sub = QLabel("Choose how the AI runs")
        sub.setStyleSheet(f"color:{_DIM};font-size:11px;margin-top:3px;")
        lay.addWidget(title)
        lay.addWidget(sub)
        lay.addSpacing(18)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color:{_BORDER};")
        lay.addWidget(sep)
        lay.addSpacing(18)

        # ── Card: API ──────────────────────────────────────────────────────────
        self._api_card = QPushButton()
        self._api_card.setObjectName("card")
        self._api_card.setCursor(Qt.PointingHandCursor)
        self._api_card.setMinimumHeight(85)
        self._api_card.clicked.connect(lambda: self._select("api"))

        api_lay = QVBoxLayout(self._api_card)
        api_lay.setContentsMargins(4, 0, 4, 0); api_lay.setSpacing(3)
        QLabel("☁  API Mode  —  Recommended", self._api_card).setStyleSheet(
            f"color:{_TEXT};font-size:13px;font-weight:700;background:transparent;")
        api_lay.addWidget(QLabel("☁  API Mode  —  Recommended"))
        desc = QLabel("Your HuggingFace Space runs the model on HF's GPU.\n"
                      "Works on any machine. No GPU, no Python deps needed.")
        desc.setStyleSheet(f"color:{_DIM};font-size:11px;background:transparent;")
        desc.setWordWrap(True)
        api_lay.addWidget(desc)
        lay.addWidget(self._api_card)
        lay.addSpacing(8)

        # Space URL input (shown when API selected)
        self._url_row = QWidget()
        ur = QVBoxLayout(self._url_row)
        ur.setContentsMargins(0, 0, 0, 0); ur.setSpacing(4)
        lbl = QLabel("HuggingFace Space URL")
        lbl.setStyleSheet(f"color:{_DIM};font-size:10px;font-weight:600;letter-spacing:0.8px;")
        self._url_input = QLineEdit(DEFAULT_SPACE_URL)
        self._url_input.setPlaceholderText("https://your-name-space.hf.space")
        ur.addWidget(lbl); ur.addWidget(self._url_input)
        self._url_row.setVisible(False)
        lay.addWidget(self._url_row)
        lay.addSpacing(8)

        # ── Card: Local ────────────────────────────────────────────────────────
        self._local_card = QPushButton()
        self._local_card.setObjectName("card")
        self._local_card.setCursor(Qt.PointingHandCursor)
        self._local_card.setMinimumHeight(85)
        self._local_card.clicked.connect(lambda: self._select("local"))

        loc_lay = QVBoxLayout(self._local_card)
        loc_lay.setContentsMargins(4, 0, 4, 0); loc_lay.setSpacing(3)
        loc_lay.addWidget(QLabel("💻  Local Mode"))
        loc_desc = QLabel("Runs the model on your machine.\n"
                          "Requires torch + unsloth installed in your Python env.")
        loc_desc.setStyleSheet(f"color:{_DIM};font-size:11px;background:transparent;")
        loc_desc.setWordWrap(True)
        loc_lay.addWidget(loc_desc)
        lay.addWidget(self._local_card)

        lay.addStretch()

        # Continue button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._btn = QPushButton("Continue")
        self._btn.setObjectName("primary")
        self._btn.setFixedWidth(160)
        self._btn.setEnabled(False)
        self._btn.clicked.connect(self._confirm)
        btn_row.addWidget(self._btn)
        lay.addLayout(btn_row)

    def _select(self, mode: str):
        self._mode = mode
        self._api_card.setObjectName(  "card_sel" if mode == "api"   else "card")
        self._local_card.setObjectName("card_sel" if mode == "local" else "card")
        # Re-polish so objectName change takes effect
        self._api_card.style().unpolish(self._api_card)
        self._api_card.style().polish(self._api_card)
        self._local_card.style().unpolish(self._local_card)
        self._local_card.style().polish(self._local_card)
        self._url_row.setVisible(mode == "api")
        self._btn.setEnabled(True)

    def _confirm(self):
        if self._mode == "api":
            url = self._url_input.text().strip().rstrip("/")
            if not url.startswith("http"):
                self._url_input.setStyleSheet("border:1px solid #E8534B;")
                return
            os.environ["ORVION_SPACE_URL"] = url
        elif self._mode == "local":
            url = ""

        # Write config file + sentinel
        self._sentinel.parent.mkdir(parents=True, exist_ok=True)
        cfg = {"mode": self._mode}
        if self._mode == "api":
            cfg["space_url"] = self._url_input.text().strip().rstrip("/")
        (self._sentinel.parent / "orvion_config.json").write_text(
            json.dumps(cfg, indent=2)
        )
        self._sentinel.write_text("ok")
        self.close()