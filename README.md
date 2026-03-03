# Orvion

A frameless AI desktop agent — chat, browse, and automate the web from one window. Built with PyQt5, powered by a HuggingFace Space API. No local GPU or model download required.

![Python](https://img.shields.io/badge/Python-3.12-blue) ![PyQt5](https://img.shields.io/badge/PyQt5-5.15-green) ![License](https://img.shields.io/badge/License-See%20LICENSE-purple) ![Build](https://img.shields.io/badge/Build-GitHub%20Actions-orange)

---

## What it does

Orvion is a three-panel desktop app:

- **Chat** — conversational AI backed by a remote HuggingFace Space (no local model, no GPU needed)
- **Editor** — distraction-free text editor with live word count, theme toggle, and SQLite persistence
- **Browser** — embedded Chromium browser (PyQtWebEngine) the AI agent can see and control

The AI runs a ReAct loop — it takes a screenshot, reads the DOM, decides on an action (click, type, scroll, navigate), executes it, and repeats until the goal is done or it's blocked.

---

## Architecture

```
launcher.py
└── main_window.py          ← frameless PyQt5 shell
    ├── chat_panel.py        ← message history + input
    ├── editor_panel.py      ← text editor
    └── web_engine.py        ← embedded browser

agent_worker.py             ← QThread: ReAct loop
    ├── API mode  → gradio_client → HuggingFace Space
    └── Local mode → torch + unsloth (run from source only)

inference_helpers.py        ← BM25 DOM retrieval, action parser
constants.py                ← mode detection (api / local)
database.py                 ← SQLite (conversations, messages, docs)
first_run_bootstrap.py      ← one-time setup wizard
```

---

## Quick start

### Prerequisites

- Python 3.12
- A HuggingFace account and token ([get one here](https://huggingface.co/settings/tokens))

### 1. Clone

```bash
git clone https://github.com/your-org/orvion.git
cd orvion
```

### 2. Create virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your HuggingFace token

Create a `.env` file in the project root:

```env
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> **Never commit this file.** It is already listed in `.gitignore`.

### 5. Run

```bash
python launcher.py
```

On the very first launch a **setup wizard** appears. Select **API mode** (recommended) and confirm the Space URL. Your choice is saved to `orvion_config.json` in your app-data folder and the wizard never appears again.

---

## Configuration

### `orvion_config.json` (auto-created by setup wizard)

| Key | Default | Description |
|-----|---------|-------------|
| `mode` | `"api"` | `"api"` or `"local"` |
| `space_url` | `"https://sanax3065-orivion-api.hf.space"` | HuggingFace Space endpoint |

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `HF_TOKEN` | Yes (for private Spaces) | HuggingFace API token — read from `.env` via `python-dotenv` |
| `ORVION_APP_DATA` | No | Override the config/database directory |

---

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New conversation |
| `Ctrl+S` | Save document |
| `Ctrl+Q` | Quit |
| `Shift+Enter` | Line break in chat input |

---

## Building installers

All three platforms build automatically on push to `main` or via the GitHub Actions **workflow_dispatch** button.

### Set up GitHub Secrets

Go to **Settings → Secrets and variables → Actions** in your repo and add:

| Secret | Required | Description |
|--------|----------|-------------|
| `HF_TOKEN` | **Yes** | HuggingFace token — injected at build time so the frozen app can reach the Space |
| `WIN_CERT_BASE64` | No | Base64-encoded `.pfx` code-signing cert (Windows) |
| `WIN_CERT_PWD` | No | Password for the `.pfx` cert |
| `APPLE_IDENTITY` | No | `Developer ID Application: ...` string (macOS) |
| `APPLE_TEAM_ID` | No | 10-char Apple Team ID |
| `APPLE_ID` | No | Apple ID email (notarization) |
| `APPLE_APP_PWD` | No | App-specific password (notarization) |

> Signing secrets are optional — the build succeeds without them. Unsigned builds will trigger OS security prompts on end-user machines.

### Manual trigger

```
GitHub → Actions → "Build Orvion Installers" → Run workflow
```

### Artifacts produced

| Platform | File |
|----------|------|
| Windows 10/11 | `OrvionSetup-windows-x64.exe` |
| Linux x86_64 | `Orvion-linux-x86_64.AppImage` |
| macOS 12+ | `Orvion-macos-universal.dmg` |

---

## Running from source vs. the installer

| | Installer | From source |
|--|-----------|-------------|
| AI inference | API (HF Space) | API or Local |
| GPU required | No | No (API) / Yes (Local) |
| PyTorch needed | No | No (API) / Yes (Local) |
| `HF_TOKEN` | GitHub Secret → bundled at build time | `.env` file |

**Local mode** (from source only) requires PyTorch + unsloth installed manually. It is not supported in the frozen installer.

---

## Database

SQLite file at `orvion.db` (excluded from git):

```sql
conversations (id, title, created_at)
messages      (id, conversation_id, role, content, timestamp)
documents     (id, title, content, updated_at)
```

---

## Project structure

```
orvion/
├── launcher.py              # entry point
├── main.py                  # QApplication bootstrap
├── main_window.py           # root window
├── agent_worker.py          # AI ReAct loop (QThread)
├── inference_helpers.py     # BM25 DOM retrieval, action parser
├── constants.py             # mode detection
├── database.py              # SQLite helpers
├── first_run_bootstrap.py   # setup wizard
├── styles.py                # QSS theme
├── widgets/
│   ├── chat_panel.py
│   ├── editor_panel.py
│   ├── web_engine.py
│   ├── sidebar.py
│   ├── titlebar.py
│   ├── message_widget.py
│   └── edge_handle.py
├── installer/
│   ├── windows/             # setup.iss + icon
│   ├── macos/               # build_dmg.sh + entitlements
│   └── linux/               # build_appimage.sh + AppRun
├── .env                     # ← YOU CREATE THIS (never committed)
├── .gitignore
├── requirements.txt
├── orvion.spec              # PyInstaller spec
└── build.yml                # GitHub Actions pipeline
```

---

## License

See [LICENSE](LICENSE). The underlying AI model is served remotely — no model weights are bundled or redistributed.

---

**Built with PyQt5 · Powered by HuggingFace Spaces**