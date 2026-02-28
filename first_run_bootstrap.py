#!/usr/bin/env python3
"""
Orvion First-Run Setup Wizard
─────────────────────────────
Shown once, on first launch.  Runs entirely inside the bundled Python/PyQt5
environment (no external Python needed).

Stages:
  1. DETECT    — check for NVIDIA GPU via nvidia-smi / torch
  2. TORCH     — upgrade bundled CPU-torch to CUDA build if GPU found
  3. UNSLOTH   — pip-install unsloth (GPU or CPU variant)
  4. MODEL     — download sanaX3065/Orvion-vl-3b from Hugging Face Hub
  5. DONE      — write sentinel file, emit finished signal
"""

import os
import sys
import subprocess
import pathlib
import threading

from PyQt5.QtCore    import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui     import QColor, QPalette, QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QApplication, QFrame
)

# ── Constants ─────────────────────────────────────────────────────────────────
REPO_ID       = "sanaX3065/Orvion-vl-3b"
TORCH_CPU_URL = "https://download.pytorch.org/whl/cpu"
TORCH_CU121   = "https://download.pytorch.org/whl/cu121"
TORCH_CU118   = "https://download.pytorch.org/whl/cu118"

# Dark palette colours reused from QSS_BASE
_BG     = "#0C0C0F"
_PANEL  = "#0F0F17"
_BORDER = "#1A1A26"
_ACCENT = "#6B4EE6"
_TEXT   = "#BCB4E0"
_DIM    = "#504A72"
_GREEN  = "#2EC440"
_RED    = "#E8534B"


# ── Worker thread ─────────────────────────────────────────────────────────────
class SetupWorker(QThread):
    stage_changed   = pyqtSignal(str, str)   # (stage_key, human label)
    detail_changed  = pyqtSignal(str)         # log line
    progress        = pyqtSignal(int)         # 0-100
    finished_ok     = pyqtSignal(str)         # hardware summary
    finished_error  = pyqtSignal(str)         # error message

    def __init__(self, model_dir: pathlib.Path):
        super().__init__()
        self.model_dir = model_dir

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _pip(*args):
        """Run pip as a subprocess using the same Python interpreter."""
        cmd = [sys.executable, "-m", "pip", "install", "--quiet", *args]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0, result.stderr

    def _emit_detail(self, msg: str):
        self.detail_changed.emit(msg)

    # ── GPU detection ─────────────────────────────────────────────────────────
    def _detect_gpu(self):
        """Returns (has_cuda: bool, cuda_version: str | None, hw_summary: str)."""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,driver_version",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=8
            )
            if result.returncode == 0:
                parts  = [p.strip() for p in result.stdout.strip().split(",")]
                name   = parts[0] if len(parts) > 0 else "NVIDIA GPU"
                vram   = parts[1] if len(parts) > 1 else "?"
                driver = parts[2] if len(parts) > 2 else "?"
                # Infer CUDA version from driver version (rough heuristic)
                try:
                    drv = float(driver.split(".")[0])
                    cuda = "cu121" if drv >= 525 else "cu118"
                except Exception:
                    cuda = "cu121"
                summary = f"{name}  ·  {vram} MB VRAM  ·  Driver {driver}"
                return True, cuda, summary
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return False, None, "No NVIDIA GPU detected — CPU mode"

    # ── pip install helpers ───────────────────────────────────────────────────
    def _install_torch_cuda(self, cuda_tag: str):
        url = TORCH_CU121 if cuda_tag == "cu121" else TORCH_CU118
        self._emit_detail(f"Installing torch with {cuda_tag.upper()} support…")
        ok, err = self._pip(
            "--upgrade",
            "torch", "torchvision", "torchaudio",
            "--index-url", url
        )
        if not ok:
            raise RuntimeError(f"torch CUDA install failed:\n{err[:400]}")

    def _install_unsloth(self, has_cuda: bool):
        if has_cuda:
            self._emit_detail("Installing Unsloth (GPU optimised)…")
            # Preferred GPU install
            ok, err = self._pip(
                "unsloth[cu121-torch240]",
                "--find-links", "https://download.pytorch.org/whl/cu121"
            )
            if not ok:
                # Fallback to plain unsloth
                self._emit_detail("Falling back to generic unsloth…")
                ok, err = self._pip("unsloth")
                if not ok:
                    raise RuntimeError(f"unsloth install failed:\n{err[:400]}")
        else:
            self._emit_detail("Installing Unsloth (CPU mode)…")
            ok, err = self._pip(
                "unsloth @ git+https://github.com/unslothai/unsloth.git"
            )
            if not ok:
                raise RuntimeError(f"unsloth install failed:\n{err[:400]}")

    def _install_extra_deps(self):
        self._emit_detail("Installing remaining AI dependencies…")
        deps = [
            "transformers>=4.45.0",
            "accelerate>=0.30.0",
            "bitsandbytes>=0.43.0",
            "qwen-vl-utils>=0.0.8",
            "safetensors>=0.4.0",
            "Pillow>=10.0.0",
            "huggingface_hub>=0.24.0",
        ]
        ok, err = self._pip(*deps)
        if not ok:
            raise RuntimeError(f"Dependency install failed:\n{err[:400]}")

    # ── model download ────────────────────────────────────────────────────────
    def _download_model(self):
        """Download model using huggingface_hub with progress reporting."""
        try:
            from huggingface_hub import snapshot_download, HfApi
            from huggingface_hub.utils import tqdm as hf_tqdm
        except ImportError:
            raise RuntimeError("huggingface_hub not available")

        self._emit_detail(f"Downloading {REPO_ID} …  (this may take 10-20 min)")
        self.model_dir.mkdir(parents=True, exist_ok=True)

        # Monkey-patch HF tqdm to forward progress to our signal
        _self = self
        _last_pct = [0]

        class _TqdmSpy(hf_tqdm):
            def update(self, n=1):
                super().update(n)
                if self.total and self.total > 0:
                    pct = int(min(100, self.n * 100 / self.total))
                    if pct != _last_pct[0]:
                        _last_pct[0] = pct
                        _self.progress.emit(pct)
                        _self._emit_detail(
                            f"  {self.desc or 'Downloading'}  {pct}%"
                            f"  ({self.n // 1_000_000} / {self.total // 1_000_000} MB)"
                        )

        try:
            import huggingface_hub.utils._tqdm as _tqdm_mod
            _orig = _tqdm_mod.hf_tqdm
            _tqdm_mod.hf_tqdm = _TqdmSpy
        except Exception:
            pass

        try:
            snapshot_download(
                repo_id=REPO_ID,
                local_dir=str(self.model_dir),
                ignore_patterns=["*.msgpack", "flax_model*", "tf_model*", "*.ot"],
            )
        finally:
            try:
                _tqdm_mod.hf_tqdm = _orig     # noqa: F821
            except Exception:
                pass

    # ── main run ──────────────────────────────────────────────────────────────
    def run(self):
        try:
            # ── Stage 1: GPU detection ──────────────────────────────────────
            self.stage_changed.emit("detect", "Detecting hardware…")
            self.progress.emit(2)
            has_cuda, cuda_tag, hw_summary = self._detect_gpu()
            self._emit_detail(hw_summary)
            self.progress.emit(8)

            # ── Stage 2: Torch ──────────────────────────────────────────────
            self.stage_changed.emit("torch", "Installing PyTorch…")
            if has_cuda:
                self._install_torch_cuda(cuda_tag)
            else:
                self._emit_detail("GPU not found — keeping bundled CPU torch.")
            self.progress.emit(30)

            # ── Stage 3: Unsloth + deps ──────────────────────────────────────
            self.stage_changed.emit("unsloth", "Installing AI runtime…")
            self._install_extra_deps()
            self.progress.emit(45)
            self._install_unsloth(has_cuda)
            self.progress.emit(55)

            # ── Stage 4: Model ───────────────────────────────────────────────
            self.stage_changed.emit("model", "Downloading Orvion AI model…")
            self.progress.emit(57)

            if not (self.model_dir / "config.json").exists():
                self._download_model()
            else:
                self._emit_detail("Model already present — skipping download.")

            self.progress.emit(100)

            # ── Done ─────────────────────────────────────────────────────────
            self.stage_changed.emit("done", "Setup complete!")
            self.finished_ok.emit(hw_summary)

        except Exception as exc:          # noqa: BLE001
            self.finished_error.emit(str(exc))


# ── Main wizard window ────────────────────────────────────────────────────────
class SetupWizard(QWidget):
    """
    Shown on first launch.  Creates the sentinel file when setup completes.
    """

    def __init__(self, sentinel_path: pathlib.Path, model_dir: pathlib.Path):
        super().__init__()
        self._sentinel  = sentinel_path
        self._model_dir = model_dir
        self._worker    = None
        self._success   = False

        self.setWindowTitle("Orvion — First Run Setup")
        self.setFixedSize(560, 380)
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self._apply_palette()
        self._build()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _apply_palette(self):
        pal = QPalette()
        pal.setColor(QPalette.Window,     QColor(_BG))
        pal.setColor(QPalette.WindowText, QColor(_TEXT))
        pal.setColor(QPalette.Base,       QColor(_PANEL))
        pal.setColor(QPalette.Text,       QColor(_TEXT))
        self.setPalette(pal)
        self.setAutoFillBackground(True)
        self.setStyleSheet(f"""
            QWidget           {{ background:{_BG}; color:{_TEXT};
                                 font-family:'Segoe UI','SF Pro Display','Helvetica Neue',sans-serif; }}
            QLabel#title      {{ font-size:22px; font-weight:700;
                                 color:#DDD6FF; letter-spacing:3px; }}
            QLabel#sub        {{ font-size:12px; color:{_DIM}; }}
            QLabel#stage_lbl  {{ font-size:13px; font-weight:600;
                                 color:{_TEXT}; }}
            QLabel#detail_lbl {{ font-size:11px; color:{_DIM};
                                 font-family:'Consolas','Fira Code',monospace; }}
            QLabel#hw_lbl     {{ font-size:11px; color:#7C5CFC; }}
            QProgressBar      {{ background:#1A1826; border:1px solid #242248;
                                 border-radius:5px; min-height:10px;
                                 max-height:10px; }}
            QProgressBar::chunk {{ background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                                    stop:0 #6B4EE6,stop:1 #4878E8);
                                   border-radius:4px; }}
            QPushButton#start_btn {{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #6B4EE6,stop:1 #4878E8);
                color:white; border-radius:9px;
                padding:10px 28px; font-size:13px; font-weight:600;
            }}
            QPushButton#start_btn:hover  {{ background:#8060FF; }}
            QPushButton#start_btn:pressed {{ background:#4835B2; }}
            QPushButton#launch_btn {{
                background:{_GREEN}; color:white; border-radius:9px;
                padding:10px 28px; font-size:13px; font-weight:600;
            }}
            QPushButton#launch_btn:hover {{ background:#30D44A; }}
            QPushButton#retry_btn {{
                background:{_RED}; color:white; border-radius:9px;
                padding:10px 20px; font-size:13px; font-weight:600;
            }}
            QFrame#separator {{
                background:{_BORDER}; max-height:1px; min-height:1px;
            }}
        """)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 28, 36, 28)
        root.setSpacing(0)

        # ── Header
        title = QLabel("ORVION"); title.setObjectName("title")
        sub   = QLabel("First-run setup  ·  One-time, ~10-20 minutes")
        sub.setObjectName("sub")
        root.addWidget(title)
        root.addSpacing(4)
        root.addWidget(sub)
        root.addSpacing(22)

        sep = QFrame(); sep.setObjectName("separator")
        root.addWidget(sep)
        root.addSpacing(22)

        # ── Stage label
        self.stage_lbl = QLabel("Ready to set up Orvion AI on your machine.")
        self.stage_lbl.setObjectName("stage_lbl")
        root.addWidget(self.stage_lbl)
        root.addSpacing(10)

        # ── Progress bar
        self.bar = QProgressBar()
        self.bar.setRange(0, 100); self.bar.setValue(0)
        self.bar.setTextVisible(False)
        root.addWidget(self.bar)
        root.addSpacing(10)

        # ── Detail log
        self.detail_lbl = QLabel("Waiting to start…")
        self.detail_lbl.setObjectName("detail_lbl")
        self.detail_lbl.setWordWrap(True)
        self.detail_lbl.setFixedHeight(48)
        self.detail_lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        root.addWidget(self.detail_lbl)

        # ── HW badge
        self.hw_lbl = QLabel("")
        self.hw_lbl.setObjectName("hw_lbl")
        root.addWidget(self.hw_lbl)
        root.addStretch()

        # ── Buttons row
        btn_row = QHBoxLayout(); btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.addStretch()

        self.start_btn = QPushButton("Begin Setup"); self.start_btn.setObjectName("start_btn")
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.clicked.connect(self._start)
        btn_row.addWidget(self.start_btn)

        self.launch_btn = QPushButton("Launch Orvion ✓"); self.launch_btn.setObjectName("launch_btn")
        self.launch_btn.setCursor(Qt.PointingHandCursor)
        self.launch_btn.clicked.connect(self.close)
        self.launch_btn.hide()
        btn_row.addWidget(self.launch_btn)

        self.retry_btn = QPushButton("Retry"); self.retry_btn.setObjectName("retry_btn")
        self.retry_btn.setCursor(Qt.PointingHandCursor)
        self.retry_btn.clicked.connect(self._start)
        self.retry_btn.hide()
        btn_row.addWidget(self.retry_btn)

        root.addLayout(btn_row)

    # ── Worker control ────────────────────────────────────────────────────────
    def _start(self):
        self.start_btn.hide()
        self.retry_btn.hide()
        self.launch_btn.hide()
        self.bar.setValue(0)
        self.detail_lbl.setText("Starting…")

        self._worker = SetupWorker(model_dir=self._model_dir)
        self._worker.stage_changed.connect(self._on_stage)
        self._worker.detail_changed.connect(self._on_detail)
        self._worker.progress.connect(self.bar.setValue)
        self._worker.finished_ok.connect(self._on_ok)
        self._worker.finished_error.connect(self._on_error)
        self._worker.start()

    def _on_stage(self, key: str, label: str):
        icons = {
            "detect":  "🔍",
            "torch":   "🔥",
            "unsloth": "⚙",
            "model":   "⬇",
            "done":    "✅",
        }
        self.stage_lbl.setText(f"{icons.get(key, '⏳')}  {label}")

    def _on_detail(self, msg: str):
        self.detail_lbl.setText(msg)

    def _on_ok(self, hw_summary: str):
        self.hw_lbl.setText(f"Hardware: {hw_summary}")
        self.stage_lbl.setText("✅  Setup complete — Orvion is ready!")
        self.detail_lbl.setText("All components installed. Model downloaded to local cache.")
        self.bar.setValue(100)
        # Write sentinel
        self._sentinel.write_text("ok")
        self._success = True
        self.launch_btn.show()

    def _on_error(self, msg: str):
        self.stage_lbl.setText("❌  Setup failed")
        self.detail_lbl.setText(f"Error: {msg[:200]}")
        self.retry_btn.show()

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            self._worker.running = False
            self._worker.quit()
            self._worker.wait(3000)
        event.accept()
