# -*- mode: python ; coding: utf-8 -*-
# ─────────────────────────────────────────────────────────────────────────────
#  Orvion — PyInstaller spec
#
#  Builds a one-directory bundle.  The CI workflow then wraps the directory
#  into a platform-native installer (Inno Setup / AppImage / DMG).
#
#  Build command:
#    pyinstaller orvion.spec --clean --noconfirm
# ─────────────────────────────────────────────────────────────────────────────

import sys
import os
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

# ── Collect heavy packages ────────────────────────────────────────────────────
# collect_all returns (datas, binaries, hiddenimports)
tf_data,    tf_bin,    tf_hidden    = collect_all("transformers")
hf_data,    hf_bin,    hf_hidden    = collect_all("huggingface_hub")
tok_data,   tok_bin,   tok_hidden   = collect_all("tokenizers")
qwen_data,  qwen_bin,  qwen_hidden  = collect_all("qwen_vl_utils")
acc_data,   acc_bin,   acc_hidden   = collect_all("accelerate")
safe_data,  safe_bin,  safe_hidden  = collect_all("safetensors")
pil_data,   pil_bin,   pil_hidden   = collect_all("PIL")
reg_data,   reg_bin,   reg_hidden   = collect_all("regex")

# torch — bundled as CPU; the bootstrap upgrades to CUDA at first run
torch_data,   torch_bin,   torch_hidden   = collect_all("torch")
vision_data,  vision_bin,  vision_hidden  = collect_all("torchvision")

# unsloth — may be CPU-only on build machine; that is intentional
try:
    uns_data, uns_bin, uns_hidden = collect_all("unsloth")
except Exception:
    uns_data, uns_bin, uns_hidden = [], [], []

# ── Aggregate ─────────────────────────────────────────────────────────────────
ALL_DATAS = (
    tf_data + hf_data + tok_data + qwen_data + acc_data +
    safe_data + pil_data + reg_data + torch_data + vision_data +
    uns_data
)
ALL_BINS = (
    tf_bin + hf_bin + tok_bin + qwen_bin + acc_bin +
    safe_bin + pil_bin + reg_bin + torch_bin + vision_bin +
    uns_bin
)
ALL_HIDDEN = (
    tf_hidden + hf_hidden + tok_hidden + qwen_hidden + acc_hidden +
    safe_hidden + pil_hidden + reg_hidden + torch_hidden + vision_hidden +
    uns_hidden +
    # Explicit extras that static analysis often misses
    collect_submodules("transformers.models") +
    collect_submodules("transformers.pipelines") +
    collect_submodules("huggingface_hub") +
    collect_submodules("tokenizers") +
    collect_submodules("torch") +
    [
        # PyQt5 / WebEngine
        "PyQt5",
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "PyQt5.QtWebEngineWidgets",
        "PyQt5.QtWebEngine",
        "PyQt5.QtNetwork",
        "PyQt5.QtPrintSupport",
        # App modules
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
        # Stdlib extras
        "sqlite3",
        "email",
        "email.mime",
        "email.mime.text",
        "urllib",
        "urllib.parse",
        "urllib.request",
        "xml",
        "xml.etree",
        "xml.etree.ElementTree",
        # ML extras
        "numpy",
        "scipy",
        "packaging",
        "filelock",
        "requests",
        "tqdm",
        "yaml",
        "pyyaml",
    ]
)

# ── Excludes ──────────────────────────────────────────────────────────────────
EXCLUDES = [
    # Test suites
    "unittest", "doctest", "pdb", "pydoc",
    # Unused ML backends
    "tensorflow", "jax", "flax", "paddle",
    # Jupyter / IPython
    "IPython", "jupyter", "notebook",
    # Build tools
    "setuptools", "distutils", "pip",
    # Other UI toolkits
    "tkinter", "wx", "gi",
    # Heavy unused
    "matplotlib", "scipy.signal", "scipy.fft",
]

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    ["launcher.py"],           # ← entry point (not main.py directly)
    pathex=["."],
    binaries=ALL_BINS,
    datas=ALL_DATAS,
    hiddenimports=ALL_HIDDEN,
    hookspath=["hooks"],       # custom hooks in ./hooks/
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
)

# ── Purge duplicate/unwanted ──────────────────────────────────────────────────
# Remove .pyc test files and avoid pulling in CUDA libs (CPU build)
# (CUDA libs will be installed at runtime by the bootstrap)
def _filter(entries, patterns):
    import fnmatch
    out = []
    for entry in entries:
        dest = entry[1] if isinstance(entry, tuple) else str(entry)
        if not any(fnmatch.fnmatch(dest.lower(), p) for p in patterns):
            out.append(entry)
    return out

SKIP_PATTERNS = [
    "*test*",
    "*/__pycache__/*",
    "*/tests/*",
    # CUDA shared libs — large & only needed with GPU torch (installed at runtime)
    "*/libcublas*",
    "*/libcudart*",
    "*/libnvrtc*",
    "*/libcufft*",
    "*/libcusparse*",
    "*/libcurand*",
    "*/nvcuda.dll",
]
a.datas    = _filter(a.datas, SKIP_PATTERNS)
a.binaries = _filter(a.binaries, SKIP_PATTERNS)

# ── PYZ archive ───────────────────────────────────────────────────────────────
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# ── EXE stub ──────────────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Orvion",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,           # compress if UPX is on PATH
    console=False,      # no console window on Windows
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=(
        "installer/windows/orvion.ico"  if sys.platform == "win32" else
        "installer/macos/orvion.icns"   if sys.platform == "darwin" else
        "installer/linux/orvion.png"
    ),
)

# ── Collect all into one directory ────────────────────────────────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[
        "vcruntime140.dll",
        "python3*.dll",
        "Qt5*.dll",
    ],
    name="Orvion",     # → dist/Orvion/
)

# ── macOS .app bundle ─────────────────────────────────────────────────────────
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Orvion.app",
        icon="installer/macos/orvion.icns",
        bundle_identifier="com.orvion.app",
        info_plist={
            "NSPrincipalClass":                    "NSApplication",
            "NSHighResolutionCapable":             True,
            "CFBundleShortVersionString":          "1.0.0",
            "CFBundleVersion":                     "1.0.0",
            "CFBundleName":                        "Orvion",
            "CFBundleDisplayName":                 "Orvion AI",
            "NSHumanReadableCopyright":            "© 2025 Orvion",
            "NSMicrophoneUsageDescription":        "",
            "NSCameraUsageDescription":            "",
        },
    )
