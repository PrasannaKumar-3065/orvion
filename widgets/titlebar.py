from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, QPoint


class TitleBar(QWidget):
    def __init__(self, win, parent=None):
        super().__init__(parent)
        self._win = win
        self._dp  = None
        self.setObjectName("titlebar")
        self.setFixedHeight(46)
        self._build()

    def _mkwm(self, bg, hov, name):
        b = QPushButton("")
        b.setObjectName(f"wmbtn_{name}")
        b.setFixedSize(16, 16)
        b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet(f"""
            QPushButton#wmbtn_{name} {{ background:{bg}; border-radius:7px; }}
            QPushButton#wmbtn_{name}:hover {{ background:{hov}; }}
        """)
        return b

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(0)

        def toggle_max():
            self._win.showNormal() if self._win.isMaximized() else self._win.showMaximized()

        lay.addSpacing(12)
        logo = QLabel("ORVION"); logo.setObjectName("tb_logo")
        dot  = QLabel("·");      dot.setObjectName("tb_logo_dot")
        lay.addWidget(logo); lay.addWidget(dot)
        lay.addStretch()

        sub = QLabel("AI WORKSPACE"); sub.setObjectName("tb_subtitle")
        sub.setAlignment(Qt.AlignCenter)
        lay.addWidget(sub)
        lay.addStretch()

        for sym, tip, fn in [("⊞", "New Chat", lambda: self._win._new_chat()),
                              ("⊟", "New Doc",  lambda: self._win._new_doc())]:
            b = QPushButton(sym); b.setObjectName("tb_action")
            b.setToolTip(tip); b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(fn)
            lay.addWidget(b); lay.addSpacing(2)

        bc = self._mkwm("#E8534B", "#FF3B30", "close")
        bm = self._mkwm("#E8A030", "#FF9500", "min")
        bx = self._mkwm("#2EC440", "#30D44A", "max")
        bc.clicked.connect(self._win.close)
        bm.clicked.connect(self._win.showMinimized)
        bx.clicked.connect(toggle_max)
        for b in (bc, bm, bx):
            lay.addWidget(b); lay.addSpacing(6)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._dp = e.globalPos() - self._win.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton and self._dp:
            self._win.move(e.globalPos() - self._dp)

    def mouseReleaseEvent(self, e):
        self._dp = None

    def mouseDoubleClickEvent(self, e):
        self._win.showNormal() if self._win.isMaximized() else self._win.showMaximized()
