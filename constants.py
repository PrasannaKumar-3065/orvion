try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import psutil
except ImportError:
    psutil = None

REPO_ID          = "sanaX3065/Orvion-vl-3b"
LOCAL_MODEL_PATH = "./local_model/Orvion-vl-3b"

try:
    from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
    from qwen_vl_utils import process_vision_info
    from PIL import Image
    AI_AVAILABLE = True
except ImportError as e:
    print(f"AI Import Error: {e}")
    AI_AVAILABLE = False
