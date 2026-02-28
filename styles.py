QSS_BASE = """
* { font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', sans-serif; outline: none; border: none; }
QMainWindow, QWidget#root { background: #0C0C0F; }
QWidget#titlebar { background: #0C0C0F; border-bottom: 1px solid #1A1A26; }
QLabel#tb_logo { color: #DDD6FF; font-size: 13px; font-weight: 700; letter-spacing: 4px; background: transparent; }
QLabel#tb_logo_dot { color: #7C5CFC; font-size: 18px; font-weight: 900; background: transparent; }
QLabel#tb_subtitle { color: #312C52; font-size: 13px; letter-spacing: 1.2px; background: transparent; }
QPushButton#tb_action { background: transparent; color: #332E58; border-radius: 5px; min-width: 26px; max-width: 26px; min-height: 22px; max-height: 22px; font-size: 14px; }
QPushButton#tb_action:hover { background: #18182A; color: #8870F0; }
QWidget#sidebar { background: #0F0F17; border-right: 1px solid #1A1A26; }
QPushButton#new_chat_btn { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #6B4EE6,stop:1 #4878E8); color: #fff; border-radius: 9px; padding: 9px 14px; font-size: 13px; font-weight: 600; letter-spacing: 0.3px; margin: 6px 14px; text-align: left; }
QPushButton#new_chat_btn:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #8060FF,stop:1 #6092FF); }
QPushButton#new_chat_btn:pressed { background: #4835B2; }
QPushButton#nav_btn { background: transparent; color: #635E88; border-radius: 7px; padding: 8px 14px; font-size: 13px; font-weight: 500; text-align: left; margin: 1px 8px; }
QPushButton#nav_btn:hover { background: #161624; color: #B0A8D8; }
QListWidget#conv_list { background: transparent; border: none; padding: 0 6px; font-size: 12px; color: #504A72; }
QListWidget#conv_list::item { color: #504A72; padding: 7px 10px; border-radius: 6px; margin: 1px 0; }
QListWidget#conv_list::item:hover { background: #161624; color: #A89ED0; }
QListWidget#conv_list::item:selected { background: #1A1832; color: #9478F0; }
QLabel#section_label { color: #2C2848; font-size: 13px; font-weight: 700; letter-spacing: 2.5px; padding: 10px 16px 3px; }
QWidget#chat_panel { background: #0C0C0F; border-right: 1px solid #181826; }
QScrollArea#chat_scroll, QWidget#chat_messages { background: transparent; border: none; }
QWidget#msg_user { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #20184C,stop:1 #18224C); border-radius: 13px 13px 3px 13px; border: 1px solid #342870; }
QWidget#msg_ai { background: #111120; border-radius: 13px 13px 13px 3px; border: 1px solid #1C1C2C; }
QLabel#msg_text_user { color: #D4CCFF; font-size: 13px; padding: 11px 15px; background: transparent; }
QLabel#msg_text_ai { color: #B0AACC; font-size: 13px; padding: 11px 15px; background: transparent; }
QLabel#msg_time { color: #2E2A4A; font-size: 13px; padding: 0 15px 6px; background: transparent; }
QLabel#ai_label { color: #7C5CFC; font-size: 9px; font-weight: 700; letter-spacing: 1.5px; padding: 4px 2px 0; background: transparent; }
QLabel#user_label { color: #4878E8; font-size: 9px; font-weight: 700; letter-spacing: 1.5px; padding: 4px 2px 0; background: transparent; }
QWidget#chat_header { background: #0F0F17; border-bottom: 1px solid #181826; }
QLabel#chat_header_title { color: #BCB4E0; font-size: 13px; font-weight: 600; background: transparent; }
QLabel#model_badge { color: #7C5CFC; font-size: 9px; font-weight: 700; letter-spacing: 0.8px; background: #18163A; border: 1px solid #342870; border-radius: 4px; padding: 2px 8px; }
QWidget#input_container { background: #0F0F17; border-top: 1px solid #181826; }
QTextEdit#chat_input { background: #161626; color: #CCC4F0; border: 1px solid #242248; border-radius: 10px; padding: 10px 13px; font-size: 13px; selection-background-color: #342870; }
QTextEdit#chat_input:focus { border: 1px solid #5540CC; background: #18183A; }
QPushButton#send_btn { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #6B4EE6,stop:1 #4878E8); color: white; border-radius: 10px; min-width: 40px; max-width: 40px; min-height: 40px; max-height: 40px; font-size: 17px; font-weight: 700; }
QPushButton#send_btn:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #8060FF,stop:1 #6092FF); }
QPushButton#send_btn:pressed { background: #4835B2; }
QLabel#typing_label { color: #42406A; font-size: 11px; font-style: italic; padding: 4px 20px; background: transparent; }
QWidget#loading_overlay { background: #0F0F17; border-top: 1px solid #181826; }
QLabel#loading_phase_icon { color: #7C5CFC; font-size: 28px; background: transparent; }
QLabel#loading_phase_label { color: #BCB4E0; font-size: 13px; font-weight: 600; letter-spacing: 0.4px; background: transparent; }
QLabel#loading_detail_label { color: #504A72; font-size: 11px; background: transparent; padding: 0 24px; }
QLabel#loading_hw_label { color: #3A3660; font-size: 10px; letter-spacing: 0.3px; background: transparent; }
QProgressBar#model_progress { background: #1A1826; border: 1px solid #242248; border-radius: 5px; min-height: 8px; max-height: 8px; text-align: center; color: transparent; }
QProgressBar#model_progress::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6B4EE6,stop:1 #4878E8); border-radius: 4px; }
QLabel#loading_pct_label { color: #6B4EE6; font-size: 11px; font-weight: 700; background: transparent; letter-spacing: 0.5px; }
QLabel#loading_speed_label { color: #3A3660; font-size: 10px; background: transparent; }
QWidget#editor_toolbar { border-bottom: 1px solid #181826; min-height: 46px; max-height: 46px; }
QLabel#editor_title_label { font-size: 13px; font-weight: 700; letter-spacing: 1.8px; padding-left: 18px; background: transparent; }
QLineEdit#doc_title_input { background: transparent; font-size: 13px; font-weight: 600; padding: 3px 8px; min-width: 180px; max-width: 280px; }
QPushButton#fmt_btn { background: transparent; border-radius: 5px; min-width: 28px; max-width: 28px; min-height: 24px; max-height: 24px; font-size: 11px; font-weight: 700; margin: 0 1px; }
QPushButton#save_btn { border-radius: 6px; padding: 4px 12px; font-size: 11px; font-weight: 600; margin-right: 8px; background: transparent; }
QPushButton#theme_toggle_btn { border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: 600; margin-right: 4px; background: transparent; letter-spacing: 0.2px; }
QWidget#wc_bar { min-height: 26px; max-height: 26px; }
QLabel#wc_label { font-size: 13px; letter-spacing: 0.4px; background: transparent; }
QPlainTextEdit#editor { border: none; font-family: 'JetBrains Mono','Cascadia Code','Fira Code','Consolas',monospace; font-size: 14px; padding: 24px 42px; }
QWidget#editor_statusbar { min-height: 26px; max-height: 26px; }
QLabel#cursor_pos_label { font-size: 13px; background: transparent; }
QSplitter::handle { background: #181826; width: 1px; }
QSplitter::handle:hover { background: #6B4EE6; }
QScrollBar:vertical { background: transparent; width: 5px; margin: 0; }
QScrollBar::handle:vertical { background: #22203C; border-radius: 2px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: #342870; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 5px; }
QScrollBar::handle:horizontal { background: #22203C; border-radius: 2px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QStatusBar { background: #080810; color: #282640; font-size: 13px; border-top: 1px solid #121220; padding: 0 8px; }
QSizeGrip { background: transparent; width: 12px; height: 12px; }
QToolTip { background: #161626; color: #BCB4E0; border: 1px solid #242248; border-radius: 5px; font-size: 11px; padding: 4px 8px; }
"""

EDITOR_DARK = """
QWidget#editor_panel      { background: #0E0E16; }
QWidget#editor_toolbar    { background: #0F0F17; }
QLabel#editor_title_label { color: #38346A; }
QLineEdit#doc_title_input { color: #BCB4E0; border-bottom: 1px solid #242248; }
QLineEdit#doc_title_input:focus { border-bottom: 1px solid #6B4EE6; color: #DDD6FF; }
QPushButton#fmt_btn        { color: #423E6A; }
QPushButton#fmt_btn:hover  { background: #1A1832; color: #9478F0; }
QPushButton#save_btn { color: #6B4EE6; border: 1px solid #342870; }
QPushButton#save_btn:hover { background: #1A1832; border-color: #6B4EE6; color: #9478F0; }
QPushButton#theme_toggle_btn { color: #423E6A; border: 1px solid #222040; }
QPushButton#theme_toggle_btn:hover { background: #161626; color: #8870F0; border-color: #423E6A; }
QPlainTextEdit#editor { background: #0E0E16; color: #BAB2DC; selection-background-color: #20184C; }
QWidget#wc_bar             { background: #0B0B12; border-bottom: 1px solid #131320; }
QLabel#wc_label            { color: #20204A; }
QWidget#editor_statusbar   { background: #090910; border-top: 1px solid #131320; }
QLabel#cursor_pos_label    { color: #20204A; }
"""

EDITOR_LIGHT = """
QWidget#editor_panel      { background: #F2F1F8; }
QWidget#editor_toolbar    { background: #ECEAF6; border-bottom: 1px solid #D8D4EE; }
QLabel#editor_title_label { color: #9490BC; }
QLineEdit#doc_title_input { color: #28224C; border-bottom: 1px solid #C4C0E0; }
QLineEdit#doc_title_input:focus { border-bottom: 1px solid #6B4EE6; color: #18143C; }
QPushButton#fmt_btn        { color: #AAA4CC; }
QPushButton#fmt_btn:hover  { background: #DDD8F4; color: #5540CC; }
QPushButton#save_btn { color: #6B4EE6; border: 1px solid #C4B8F4; }
QPushButton#save_btn:hover { background: #EAE6FC; }
QPushButton#theme_toggle_btn { color: #9490BC; border: 1px solid #CCCAE0; }
QPushButton#theme_toggle_btn:hover { background: #EAE6FC; color: #5540CC; }
QPlainTextEdit#editor { background: #F8F7FC; color: #1C183A; selection-background-color: #D0C8FF; }
QWidget#wc_bar             { background: #EAE8F4; border-bottom: 1px solid #D4D0EC; }
QLabel#wc_label            { color: #B0ACCE; }
QWidget#editor_statusbar   { background: #E6E4F0; border-top: 1px solid #D4D0EC; }
QLabel#cursor_pos_label    { color: #B0ACCE; }
"""
