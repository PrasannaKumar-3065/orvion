from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer


class MessageWidget(QWidget):
    def __init__(self, role, content, ts="", parent=None):
        super().__init__(parent)
        is_user = (role == "user")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 5, 16, 5)
        lay.setSpacing(8)

        row = QHBoxLayout(); row.setContentsMargins(0, 0, 0, 0)
        who = QLabel("YOU" if is_user else "ORVION")
        who.setObjectName("user_label" if is_user else "ai_label")
        if is_user:
            row.addStretch(); row.addWidget(who)
        else:
            row.addWidget(who); row.addStretch()
        lay.addLayout(row)

        brow = QHBoxLayout(); brow.setContentsMargins(0, 0, 0, 0)
        bubble = QWidget()
        bubble.setObjectName("msg_user" if is_user else "msg_ai")
        bubble.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
        bl = QVBoxLayout(bubble); bl.setContentsMargins(0, 0, 0, 0); bl.setSpacing(0)

        txt = QLabel(content)
        txt.setObjectName("msg_text_user" if is_user else "msg_text_ai")
        txt.setWordWrap(True); txt.setMaximumWidth(400)
        bl.addWidget(txt)

        if ts:
            tl = QLabel(ts[11:16] if len(ts) > 11 else ts)
            tl.setObjectName("msg_time")
            tl.setAlignment(Qt.AlignRight if is_user else Qt.AlignLeft)
            bl.addWidget(tl)

        if is_user:
            brow.addStretch(); brow.addWidget(bubble)
        else:
            brow.addWidget(bubble); brow.addStretch()
        lay.addLayout(brow)


class TypingIndicator(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("typing_label")
        self._d = 0
        self._t = QTimer(self)
        self._t.timeout.connect(self._tick)

    def start(self):
        self.setText("  Orvion is thinking…"); self._t.start(380); self.show()

    def stop(self):
        self._t.stop(); self.hide(); self.setText("")

    def _tick(self):
        self._d = (self._d + 1) % 4
        self.setText("  Orvion is thinking" + "·" * self._d)
