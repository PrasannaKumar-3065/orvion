#!/usr/bin/env python3
"""
Orvion Launcher — PyInstaller entry point.
"""
import multiprocessing
multiprocessing.freeze_support()

import os, sys, pathlib
from dotenv import load_dotenv # <--- Required to read your secret

# ── 1. Load the Bundled .env File ──────────────────────────────────────────
def load_bundled_env():
    # When running as a PyInstaller EXE, sys._MEIPASS points to the temp folder
    # where the .env file was unpacked.
    if getattr(sys, 'frozen', False):
        base_path = pathlib.Path(sys._MEIPASS)
    else:
        base_path = pathlib.Path(__file__).parent

    env_path = base_path / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)

load_bundled_env() # Call this immediately

# ── 2. Single-instance guard ───────────────────────────────────────────────
if sys.platform == "win32":
    import ctypes
    _mtx = ctypes.windll.kernel32.CreateMutexW(None, False, "OrvionApp_SingleInstance")
    if ctypes.windll.kernel32.GetLastError() == 183:
        sys.exit(0)

# ── 3. App-data paths ──────────────────────────────────────────────────────
if sys.platform == "win32":
    _APP_DATA = pathlib.Path(os.environ.get("APPDATA", "~")) / "Orvion"
elif sys.platform == "darwin":
    _APP_DATA = pathlib.Path.home() / "Library" / "Application Support" / "Orvion"
else:
    _APP_DATA = pathlib.Path.home() / ".local" / "share" / "orvion"

_APP_DATA.mkdir(parents=True, exist_ok=True)
_SENTINEL  = _APP_DATA / "orvion_setup_complete"
_MODEL_DIR = _APP_DATA / "model"

os.environ["ORVION_APP_DATA"] = str(_APP_DATA)
os.environ["ORVION_MODEL_DIR"] = str(_MODEL_DIR)

# ── 4. Main Entry ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not _SENTINEL.exists():
        from PyQt5.QtWidgets import QApplication
        import first_run_bootstrap
        # Ensure we have a QApp instance for the wizard
        app = QApplication.instance() or QApplication(sys.argv)
        wiz = first_run_bootstrap.SetupWizard(sentinel_path=_SENTINEL, model_dir=_MODEL_DIR)
        wiz.show()
        app.exec_()
        if not _SENTINEL.exists():
            sys.exit(0)

    # By the time main() runs, HF_TOKEN is now in os.environ
    from main import main
    main()
