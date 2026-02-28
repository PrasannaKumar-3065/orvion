# hooks/hook-torch.py
# Collect torch for the CPU build that ships in the installer.
# GPU-capable torch is pip-installed at first run by first_run_bootstrap.py.

from PyInstaller.utils.hooks import collect_all, collect_submodules, logger
import os

datas, binaries, hiddenimports = collect_all("torch")
hiddenimports += collect_submodules("torch")

# Collect torchvision safely
try:
    _d, _b, _h = collect_all("torchvision")
    datas      += _d
    binaries   += _b
    hiddenimports += _h
except Exception:
    pass

logger.info("hook-torch: collected %d datas, %d binaries", len(datas), len(binaries))
