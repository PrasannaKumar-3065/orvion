# Orvion — Modern AI Chat + Text Editor

A frameless, AI-powered desktop application combining a conversational chat interface with an integrated text editor and web browser. Built with PyQt5 and powered by **Qwen 2.5 3B VL Instruct**.

## ✨ Features

### Chat Panel
- **AI-Powered Conversations**: Real-time chat with Qwen 2.5 3B VL Instruct model
- **Conversation History**: SQLite persistence for managing multiple conversations
- **Model Loading Overlay**: Real-time progress tracking with hardware detection
- **Auto-Retry**: Automatic fallback strategies for model loading (4-bit quantization, CPU offload, etc.)

### Text Editor
- **Distraction-Free Writing**: Clean, minimal interface optimized for focus
- **Light/Dark Theme Toggle**: Switch editor themes on demand
- **Word & Character Counts**: Live statistics as you type
- **Line & Column Tracking**: Real-time cursor position indicator
- **Document Persistence**: Save and manage documents with SQLite
- **Formatting Toolbar**: Bold, italic, underline, heading, and alignment options

### Web Browser
- **Integrated Navigation**: Back, forward, and reload controls
- **URL Bar**: Enter web addresses or search queries
- **Progress Indicator**: Visual feedback during page loads
- **Theme Support**: Synchronized light/dark modes

### Hardware Support
- **Multi-Tier Model Loading**: Adaptive strategies for different hardware configurations
  - Tier 1: 4-bit quantization on GPU (optimal for 4GB VRAM)
  - Tier 2: 4-bit with CPU offload
  - Tier 3: 4-bit on CPU
  - Tier 4: fp16 on GPU (no quantization)
  - Tier 5: fp32 on CPU (fallback)
- **GPU Detection**: Automatic CUDA capability checking
- **Memory Monitoring**: RAM and VRAM assessment

### UI/UX
- **Frameless Design**: Custom window chrome with minimal styling
- **Dark Mode Default**: Deep purple and indigo color scheme
- **Responsive Layout**: Splitter-based dynamic resizing
- **Keyboard Shortcuts**:
  - `Ctrl+Q` — Quit
  - `Ctrl+N` — New Chat
  - `Ctrl+S` — Save Document
  - `Shift+Enter` — Add line break in chat

## 🚀 System Requirements

**Minimum**:
- Python 3.8+
- 8 GB RAM
- Windows 10+

**Recommended for AI Features**:
- NVIDIA GPU with ≥4 GB VRAM (e.g., RTX 3050, RTX 4050)
- 16 GB+ RAM
- CUDA 11.8+ (if using NVIDIA GPU)

## 📦 Dependencies

### Core Libraries
| Package | Version | Purpose |
|---------|---------|---------|
| `PyQt5` | ≥5.15.0 | GUI framework (widgets, web engine) |
| `PyQt5-WebEngine` | ≥5.15.0 | Chromium-based browser widget |
| `transformers` | ≥4.40.0 | Hugging Face model loading & inference |
| `torch` | ≥2.0.0 | Deep learning framework |
| `torchvision` | ≥0.15.0 | Computer vision utilities |
| `bitsandbytes` | ≥0.41.0 | 4-bit quantization support |
| `qwen-vl-utils` | Latest | Vision-language utilities for Qwen |
| `huggingface-hub` | ≥0.19.0 | Model downloading & hub integration |
| `Pillow` | ≥9.0.0 | Image processing |
| `psutil` | ≥5.9.0 | System resource monitoring |

### Model Details
- **Model**: `sanaX3065/aegis-vl-3b` (Qwen 2.5 3B VL Instruct variant)
- **Model Type**: Vision-Language (supports text + image inputs)
- **Default Path**: `./local_model/aegis-vl-3b/`
- **Size**: ~3B parameters (optimized for inference on consumer hardware)

## 📥 Installation

### 1. Clone or Download
```bash
# Clone repository (if applicable)
git clone <repository-url>
cd Orvion
```

### 2. Create Virtual Environment
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash

pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install transformers huggingface_hub accelerate sentencepiece pillow qwen-vl-utils PyQt5 PyQtWebEngine safetensors einops

# Core dependencies
pip install PyQt5 PyQt5-WebEngine

# AI/ML stack
pip install transformers torch torchvision bitsandbytes

# Vision utilities
pip install qwen-vl-utils huggingface-hub Pillow

# System monitoring
pip install psutil

# Or install all at once:
pip install -r requirements.txt
```

### 4. Download Model (Optional)
The model is downloaded automatically on first run. To pre-download:
```bash
python -c "from transformers import AutoModel, AutoProcessor; \
AutoModel.from_pretrained('sanaX3065/aegis-vl-3b'); \
AutoProcessor.from_pretrained('sanaX3065/aegis-vl-3b')"
```

## 🚀 Usage

### Start the Application
```bash
python new_mod.py
```

### First Run
1. Application will detect hardware capabilities
2. Model will automatically download (5-10 minutes, depending on internet speed)
3. Model will load into memory with auto-fallback if needed
4. Chat interface becomes available when model is ready

### Chat Interface
- Type messages in the input field
- Press `Enter` to send (or `Shift+Enter` for line breaks)
- AI responds with context-aware text
- Conversations are automatically saved to SQLite database

### Text Editor
- Click the **Editor** tab
- Start typing—no files need to be created
- Press ⌘/Ctrl+S or click **Save** to persist
- Toggle themes with the **☀ Light** / **🌙 Dark** button

### Web Browser
- Click the **Browser** tab
- Enter URLs (e.g., `google.com`) in the address bar
- Navigate with back/forward/reload buttons

## 🗄️ Database Structure

SQLite database (`orvion.db`) includes three tables:

```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    created_at TEXT
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER,
    role TEXT,  -- 'user' or 'assistant'
    content TEXT,
    timestamp TEXT
);

CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT,
    updated_at TEXT
);
```

## ⚙️ Configuration

### Model Settings
In `new_mod.py`, adjust these constants:

```python
REPO_ID = "sanaX3065/aegis-vl-3b"              # Model identifier
LOCAL_MODEL_PATH = "./local_model/aegis-vl-3b" # Download location
MIN_RAM_GB = 8                                  # Minimum RAM required
MIN_GPU_VRAM_GB = 4                             # Minimum GPU VRAM
```

### Inference Parameters
- **Max tokens**: 512 (chat), 150 (vision tasks)
- **Temperature**: 0.7 (chat), 0.0 (deterministic)
- **Top-p**: 0.9 (chat)

## 📜 Licensing

### Orvion Application
This project is provided as-is for personal and educational use.

### Qwen 2.5 3B VL Instruct Model License
The integrated AI model uses **Alibaba Qwen 2.5 3B VL Instruct**, which is licensed under the **Qwen License Agreement**.

**License Terms**:
- **Model Source**: Alibaba Cloud's Qwen open-source initiative
- **License Type**: Qwen License (with commercial usage restrictions)
- **Usage**: 
  - ✅ Personal research and development
  - ✅ Academic use
  - ✅ Non-commercial applications
  - ⚠️ Commercial use requires prior approval from Alibaba
- **Attribution**: When using this model, please cite:
  - Qwen Team, Alibaba. "Qwen 2.5: Advanced Large Language Model Family"

**For full license details**, visit:
- Qwen License: https://github.com/QwenLM/Qwen2.5/blob/main/Qwen%202.5%20License%20Agreement.pdf
- Model Card: https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct

### Third-Party Libraries
All dependencies are governed by their respective licenses:
- **PyQt5**: GPLv3 / Commercial license
- **Transformers**: Apache 2.0
- **PyTorch**: BSD
- **Hugging Face Hub**: Apache 2.0
- See `requirements.txt` for complete list

## 🛠️ Troubleshooting

### "AI Libraries Missing" Error
```bash
pip install -U transformers torch torchvision bitsandbytes qwen-vl-utils huggingface-hub
```

### Model Download Timeout
- Check internet connection
- Manually download model:
  ```bash
  python -c "from huggingface_hub import snapshot_download; \
  snapshot_download('sanaX3065/aegis-vl-3b', local_dir='./local_model/aegis-vl-3b')"
  ```

### "CUDA Out of Memory" Error
- Application automatically falls back through load strategies
- Click **Retry** button in chat overlay
- Or reduce max token count in code

### Chat Not Responding
- Check hardware info in bottom status bar
- Ensure model loaded successfully (✓ indicator in badge)
- Wait for inference to complete (watch status bar)

## 📊 Performance

| Hardware | Load Time | Chat Response Time |
|----------|-----------|-------------------|
| NVIDIA RTX 4050 (8GB) | 30-45s | 1-3s per response |
| NVIDIA RTX 3050 (6GB) | 45-90s | 2-5s per response |
| CPU (16GB RAM) | 90-180s | 10-30s per response |

*Times vary based on input length and model configuration.*

## 🔄 Updates & Contributing

To check for model updates:
```bash
huggingface-cli repo_sync sanaX3065/aegis-vl-3b --repo-type model
```

## 📝 Notes

- Database and model are stored locally—no cloud synchronization
- Conversations persist between sessions
- Model weights (~6GB) are downloaded on first run
- GPU monitoring via `torch.cuda` and `psutil`

---

**Made with ❤️ using PyQt5 & Qwen 2.5 3B VL**

For issues or questions, please refer to the logs in the status bar or check the system console output.
