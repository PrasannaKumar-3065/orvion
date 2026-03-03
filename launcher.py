#!/usr/bin/env python3
"""
Orvion Launcher — PyInstaller entry point.
"""
# freeze_support MUST be the absolute first call.
# On Windows, PyInstaller re-executes the .exe for every subprocess.
# freeze_support() detects that and exits before any UI code runs.
import multiprocessing
multiprocessing.freeze_support()

import os, sys, pathlib

import os, sys, pathlib
from dotenv import load_dotenv  # Add this import

# --- New: Load bundled .env file ---
def load_bundled_env():
    if getattr(sys, 'frozen', False):
        # Path where PyInstaller extracts data at runtime
        bundle_dir = pathlib.Path(sys._MEIPASS)
    else:
        # Standard script path
        bundle_dir = pathlib.Path(__file__).parent

    env_path = bundle_dir / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        # Optional: Print for debugging in console mode
        print(f"DEBUG: .env not found at {env_path}")

load_bundled_env()
# -----------------------------------

# Single-instance guard — prevents the zip-bomb effect
if sys.platform == "win32":
    import ctypes
    _mtx = ctypes.windll.kernel32.CreateMutexW(None, False, "OrvionApp_SingleInstance")
    if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        sys.exit(0)

# App-data paths
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

if __name__ == "__main__":
    if not _SENTINEL.exists():
        from PyQt5.QtWidgets import QApplication
        import first_run_bootstrap
        app = QApplication.instance() or QApplication(sys.argv)
        wiz = first_run_bootstrap.SetupWizard(sentinel_path=_SENTINEL, model_dir=_MODEL_DIR)
        wiz.show()
        app.exec_()
        if not _SENTINEL.exists():
            sys.exit(0)

    from main import main
    main()
