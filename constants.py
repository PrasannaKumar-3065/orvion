import os
import json
import pathlib

try:
    import psutil
except ImportError:
    psutil = None

REPO_ID          = "sanaX3065/aegis-qwen2vl-3b"
LOCAL_MODEL_PATH = "./local_model/Orvion-vl-3b"


def _get_mode() -> str:
    """Read the mode the user chose in the setup wizard."""
    cfg = pathlib.Path(os.environ.get("ORVION_APP_DATA", "")) / "orvion_config.json"
    if cfg.exists():
        try:
            return json.loads(cfg.read_text()).get("mode", "api")
        except Exception:
            pass
    # No config yet (running before first-run wizard) — still return "api"
    # so the UI starts and shows the wizard properly.
    return "api"


def _check_ai_available() -> bool:
    """
    API mode  → always True, no local ML stack needed.
    Local mode → True only if torch + transformers + qwen_vl_utils importable.
    """
    if _get_mode() == "api":
        return True
    # Local mode — check full ML stack (lazy, so no crash on import)
    try:
        import torch                                                  # noqa
        from transformers import Qwen2_5_VLForConditionalGeneration  # noqa
        from qwen_vl_utils import process_vision_info                # noqa
        from PIL import Image                                         # noqa
        return True
    except ImportError as e:
        print(f"[Orvion] Local AI stack not available: {e}")
        return False


AI_AVAILABLE = _check_ai_available()