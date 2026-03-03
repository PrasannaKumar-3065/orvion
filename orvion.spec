# -*- mode: python ; coding: utf-8 -*-
# ─────────────────────────────────────────────────────────────────────────────
#  Orvion — PyInstaller spec  (API-only build)
#
#  Bundled:     PyQt5, PyQtWebEngine, Pillow, requests, gradio_client, stdlib
#  NOT bundled: torch, transformers, unsloth, huggingface_hub, numpy, etc.
#
#  All AI inference is done remotely via gradio_client → HuggingFace Space.
#  No local model, no GPU required on the end-user machine.
# ─────────────────────────────────────────────────────────────────────────────
import certifi
import sys
from PyInstaller.utils.hooks import collect_all
cert_path = certifi.where()
# ── Collect data/binaries for packages that need it ──────────────────────────
pil_datas,     pil_bins,     pil_hidden     = collect_all("PIL")
req_datas,     req_bins,     req_hidden     = collect_all("requests")
gradio_datas,  gradio_bins,  gradio_hidden  = collect_all("gradio_client")

ALL_DATAS  = pil_datas  + req_datas  + gradio_datas
ALL_BINS   = pil_bins   + req_bins   + gradio_bins
ALL_HIDDEN = pil_hidden + req_hidden + gradio_hidden + [
    # ── PyQt5 ──────────────────────────────────────────────────────────────
    "PyQt5",
    "PyQt5.QtCore",
    "PyQt5.QtGui",
    "PyQt5.QtWidgets",
    "PyQt5.QtWebEngineWidgets",
    "PyQt5.QtWebEngine",
    "PyQt5.QtNetwork",
    "PyQt5.QtPrintSupport",
    # ── App modules ────────────────────────────────────────────────────────
    "database",
    "styles",
    "constants",
    "inference_helpers",
    "agent_worker",
    "main_window",
    "first_run_bootstrap",
    "widgets",
    "widgets.edge_handle",
    "widgets.titlebar",
    "widgets.message_widget",
    "widgets.sidebar",
    "widgets.chat_panel",
    "widgets.web_engine",
    "widgets.editor_panel",
    # ── Stdlib ─────────────────────────────────────────────────────────────
    "sqlite3",
    "urllib",
    "urllib.parse",
    "urllib.request",
    "urllib.error",
    "json",
    "base64",
    "pathlib",
    "threading",
    "email",
    "email.mime",
    "email.mime.text",
    "xml",
    "xml.etree",
    "xml.etree.ElementTree",
    "ssl",
    "http",
    "http.client",
    "dotenv",
]

# ── Packages to hard-exclude (keeps the installer small) ─────────────────────
EXCLUDES = [
    # ML / local-model stack — not used in API build
    "torch", "torchvision", "torchaudio",
    "transformers", "tokenizers",
    "unsloth",
    "accelerate", "safetensors", "bitsandbytes",
    "huggingface_hub",
    "qwen_vl_utils",
    "numpy", "scipy", "sklearn", "pandas",
    # Other unused heavy deps
    "tensorflow", "jax", "flax",
    "IPython", "jupyter", "notebook",
    "matplotlib",
    "unittest", "doctest", "pdb", "pydoc",
    "setuptools", "distutils", "pip",
    "tkinter", "wx", "gi",
    "pytest", "mypy",
]

a = Analysis(
    ["launcher.py"],
    pathex=["."],
    binaries=ALL_BINS,
    datas=ALL_DATAS + [('.env', '.'), (cert_path, 'certifi')],
    hiddenimports=ALL_HIDDEN,
    hookspath=[],           # no custom hooks needed — ML packages are excluded
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Orvion",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=(
        "installer/windows/orvion.ico" if sys.platform == "win32"  else
        "installer/macos/orvion.icns"  if sys.platform == "darwin" else
        "installer/linux/orvion.png"
    ),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=["vcruntime140.dll", "python3*.dll", "Qt5*.dll"],
    name="Orvion",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Orvion.app",
        icon="installer/macos/orvion.icns",
        bundle_identifier="com.orvion.app",
        info_plist={
            "NSPrincipalClass":           "NSApplication",
            "NSHighResolutionCapable":    True,
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleName":               "Orvion",
            "CFBundleDisplayName":        "Orvion AI",
            "NSHumanReadableCopyright":   "© 2025 Orvion",
        },
    )
