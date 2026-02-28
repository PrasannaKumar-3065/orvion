from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPoint, QRect


class EdgeHandle(QWidget):
    L, R, T, B = 1, 2, 4, 8

    def __init__(self, win, edge, parent=None):
        super().__init__(parent)
        self._win  = win
        self._edge = edge
        self._drag = False
        self._sp   = QPoint()
        self._sg   = QRect()
        self.setCursor(Qt.SizeHorCursor if edge in (self.L, self.R) else Qt.SizeVerCursor)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag = True
            self._sp   = e.globalPos()
            self._sg   = QRect(self._win.geometry())

    def mouseMoveEvent(self, e):
        if not self._drag:
            return
        dx = e.globalPos().x() - self._sp.x()
        dy = e.globalPos().y() - self._sp.y()
        g  = QRect(self._sg)
        mw, mh = self._win.minimumWidth(), self._win.minimumHeight()
        if   self._edge == self.R: g.setRight(g.right() + dx)
        elif self._edge == self.L: g.setLeft(min(g.left() + dx, g.right() - mw))
        elif self._edge == self.T: g.setTop(min(g.top() + dy, g.bottom() - mh))
        elif self._edge == self.B: g.setBottom(g.bottom() + dy)
        if g.width() >= mw and g.height() >= mh:
            self._win.setGeometry(g)

    def mouseReleaseEvent(self, e):
        self._drag = False
