# hooks/hook-unsloth.py
# PyInstaller hook — safely collect unsloth if it is installed.
# On CI machines without CUDA the package still installs in CPU-compat mode.

from PyInstaller.utils.hooks import collect_all, collect_submodules, logger

try:
    datas, binaries, hiddenimports = collect_all("unsloth")
    hiddenimports += collect_submodules("unsloth")
    logger.info("hook-unsloth: collected %d datas, %d binaries, %d hidden",
                len(datas), len(binaries), len(hiddenimports))
except Exception as exc:
    logger.warning("hook-unsloth: could not collect unsloth (%s) — "
                   "it will be installed at first run by the bootstrap wizard.", exc)
    datas, binaries, hiddenimports = [], [], []
