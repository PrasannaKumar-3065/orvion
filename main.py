#!/usr/bin/env python3
"""
Orvion — Modern AI Chat + Browser Agent
Frameless window, SQLite persistence, editor light/dark mode.
https://sanax3065-orivion-api.hf.space
"""
import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QColor, QPalette

from main_window import OrvionWindow
import multiprocessing

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Orvion")
    app.setStyle("Fusion")

    pal = QPalette()
    pal.setColor(QPalette.Window,          QColor("#0C0C0F"))
    pal.setColor(QPalette.WindowText,      QColor("#BCB4E0"))
    pal.setColor(QPalette.Base,            QColor("#0F0F17"))
    pal.setColor(QPalette.AlternateBase,   QColor("#131321"))
    pal.setColor(QPalette.Text,            QColor("#BCB4E0"))
    pal.setColor(QPalette.Button,          QColor("#0F0F17"))
    pal.setColor(QPalette.ButtonText,      QColor("#BCB4E0"))
    pal.setColor(QPalette.Highlight,       QColor("#342870"))
    pal.setColor(QPalette.HighlightedText, QColor("#DDD6FF"))
    app.setPalette(pal)

    win = OrvionWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
