#!/usr/bin/env python3
"""
Orvion Launcher — PyInstaller entry point.

Responsibilities:
  1. On first run: show the Bootstrap wizard (GPU detection,
     torch-CUDA upgrade, model download).
  2. On subsequent runs: launch the main Orvion window directly.

The sentinel file  <app_data>/orvion_setup_complete  is created by the
bootstrap wizard when it finishes successfully.  Its absence triggers the
wizard again.
"""

import os
import sys
import pathlib
import multiprocessing
# ── Locate the persistent app-data directory ──────────────────────────────────
if sys.platform == "win32":
    _APP_DATA = pathlib.Path(os.environ.get("APPDATA", pathlib.Path.home())) / "Orvion"
elif sys.platform == "darwin":
    _APP_DATA = pathlib.Path.home() / "Library" / "Application Support" / "Orvion"
else:
    _APP_DATA = pathlib.Path.home() / ".local" / "share" / "orvion"

_APP_DATA.mkdir(parents=True, exist_ok=True)

_SENTINEL = _APP_DATA / "orvion_setup_complete"
_MODEL_DIR = _APP_DATA / "model"

# Expose to child modules so they use the same paths
os.environ["ORVION_APP_DATA"] = str(_APP_DATA)
os.environ["ORVION_MODEL_DIR"] = str(_MODEL_DIR)


def _need_bootstrap() -> bool:
    """Return True if the one-time setup has not yet completed."""
    return not _SENTINEL.exists()


def _run_bootstrap():
    """Launch the PyQt5 setup wizard.  Blocks until the wizard exits."""
    # PyQt5 is always bundled — safe to import here.
    from PyQt5.QtWidgets import QApplication
    import first_run_bootstrap

    app = QApplication.instance() or QApplication(sys.argv)
    wizard = first_run_bootstrap.SetupWizard(sentinel_path=_SENTINEL,
                                             model_dir=_MODEL_DIR)
    wizard.show()
    app.exec_()

    # If the wizard was closed without completing, abort launch.
    if not _SENTINEL.exists():
        sys.exit(0)


def _run_main_app():
    """Import and launch the main Orvion window."""
    # Delay heavy imports until torch/unsloth are confirmed available.
    from main import main          # noqa: PLC0415
    main()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    multiprocessing.freeze_support()
    if _need_bootstrap():
        _run_bootstrap()
    _run_main_app()
