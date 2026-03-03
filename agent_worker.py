"""
agent_worker.py
───────────────
Two modes, same Qt signals.

  API mode   → calls HuggingFace Space via gradio_client.
  Local mode → torch + unsloth, lazy imported.

ReAct loop format matches training data exactly:
  - System: Aegis system prompt + tool list
  - User:   screenshot + <CONTEXT_BLOCK>[DOM][OBSERVATIONS: prev thought/action/result]</CONTEXT_BLOCK> + goal
  - Same goal every step; only the single previous step in OBSERVATIONS.
  - Loop ends on [GOAL ACHIEVED], [FLOW BLOCKED], action=None, or max steps.
"""

import re
import json
import math
import os
import threading
import pathlib
from io import BytesIO

from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition

from dotenv import load_dotenv
load_dotenv()


# ── Config ────────────────────────────────────────────────────────────────────

def _load_config() -> dict:
    cfg = pathlib.Path(os.environ.get("ORVION_APP_DATA", "")) / "orvion_config.json"
    if cfg.exists():
        try:
            return json.loads(cfg.read_text())
        except Exception:
            pass
    return {"mode": "api", "space_url": "https://sanax3065-orivion-api.hf.space"}


# ── Prompt builder ────────────────────────────────────────────────────────────

def _build_prompt(messages: list) -> str:
    """Flatten message list into the training prompt format."""
    parts = []
    for m in messages:
        role    = m.get("role", "user")
        content = m.get("content", "")
        if isinstance(content, list):
            content = "\n".join(
                block.get("text", "")
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            )
        if role == "system":
            parts.append(f"System: {content}")
        elif role == "user":
            parts.append(f"User: {content}")
        elif role == "assistant":
            parts.append(f"Assistant: {content}")
    parts.append("Assistant:")
    return "\n\n".join(parts)


# ── Space client ──────────────────────────────────────────────────────────────

class _SpaceClient:
    def __init__(self, space_url: str):
        self.space_url = space_url
        self._client   = None

    def _get_client(self):
        if self._client is None:
            try:
                from gradio_client import Client
                HF_TOKEN = os.getenv("HF_TOKEN")
                try:
                    # Try the modern keyword first
                    self._client = Client(self.space_url, hf_token=HF_TOKEN)
                except TypeError:
                    # Fallback for very old versions (pre-0.3.0)
                    self._client = Client(self.space_url, token=HF_TOKEN)
            except ImportError:
                raise RuntimeError("gradio_client not installed. Run: pip install gradio_client")
        return self._client

    def generate(self, prompt_text: str, image=None) -> str:
        client    = self._get_client()
        image_arg = None
        if image is not None:
            import tempfile
            from gradio_client import handle_file
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            if isinstance(image, bytes):
                tmp.write(image)
            else:
                image.save(tmp.name)
            tmp.close()
            image_arg = handle_file(tmp.name)

        result = client.predict(
            prompt_text=prompt_text,
            image_file=image_arg,
            api_name="/generate",
        )
        return str(result).strip()

    def chat(self, messages: list, image_bytes: bytes = None) -> str:
        return self.generate(_build_prompt(messages), image=image_bytes)


# ── Tool list (no email tools) ────────────────────────────────────────────────

TOOL_LIST = (
    "click, type, clear_and_type, open_url, press_key, select_option, hover, "
    "double_click, right_click, go_back, scroll_down, scroll_up, scroll_to_element, "
    "scroll_to_top, scroll_to_bottom, verify_text_present, verify_text_absent, "
    "verify_element_visible, verify_element_enabled, verify_url_contains, "
    "verify_page_title, verify_input_value, verify_element_count, get_text, "
    "wait_for_element, wait_for_text, wait_for_url_change, wait_for_network_idle, "
    "wait, get_current_url, get_page_title, raise_bug_ticket, mark_step_pass, "
    "mark_step_fail, mark_flow_blocked, add_test_comment, capture_evidence"
)

SYSTEM_PROMPT = (
    f"You are Aegis. Current Mode: QUALITY_TESTER\n"
    f"Tools: [{TOOL_LIST}]"
)

AGENTIC_TRIGGERS = (
    "open ", "go to ", "navigate", "search for", "click",
    "type ", "browse", "find on", "look up", "url ",
    "website", "google", "automate", "execute", "fill in",
    "log in", "login", "verify", "check", "scroll",
    "double click", "right click", "hover",
)


# ── AgentWorker ───────────────────────────────────────────────────────────────

class AgentWorker(QThread):
    log_signal            = pyqtSignal(str, str)
    model_ready           = pyqtSignal()
    action_ready          = pyqtSignal(dict, str)
    chat_reply            = pyqtSignal(str)
    download_progress     = pyqtSignal(float, float, str)
    download_done         = pyqtSignal()
    phase_changed         = pyqtSignal(str, str)
    hw_info               = pyqtSignal(bool, float, float, str)
    request_browser_state = pyqtSignal()
    browser_state_ready   = pyqtSignal(bytes, str)
    step_log              = pyqtSignal(str)
    tool_request          = pyqtSignal(str, dict)
    tool_result_ready     = pyqtSignal(object)
    setup_requested       = pyqtSignal()
    setup_result_ready    = pyqtSignal(str, str)
    request_screenshot    = pyqtSignal()
    screenshot_ready      = pyqtSignal(bytes)

    def __init__(self):
        super().__init__()
        self.running              = True
        self.mutex                = QMutex()
        self.condition            = QWaitCondition()
        self.browser_state        = None
        self._pending_tool_result = None
        self.chat_queue           = []
        self.lock                 = threading.Lock()
        self.model                = None   # local mode only
        self.processor            = None   # local mode only

        cfg       = _load_config()
        self.mode = cfg.get("mode", "api")
        space_url = cfg.get("space_url",
                            os.environ.get("ORVION_SPACE_URL",
                                           "https://sanax3065-orivion-api.hf.space"))
        self._space = _SpaceClient(space_url) if self.mode == "api" else None

    # ── Qt signal handlers ────────────────────────────────────────────────────

    def enqueue_chat(self, user_text: str, history: list):
        with self.lock:
            self.chat_queue.append((user_text, history))

    def _on_screenshot_ready(self, data):  pass
    def _on_setup_result(self, mode, url): pass
    def _on_tool_result(self, result):     self._pending_tool_result = result
    def _on_browser_state_ready(self, screenshot, dom):
        self.browser_state = (screenshot, dom)

    # ── BM25 DOM retrieval ────────────────────────────────────────────────────

    def _tokenize(self, text: str) -> list:
        return re.findall(r'[a-z0-9]+', text.lower())

    def _bm25_score(self, query_tokens, doc_tokens, k1=1.5, b=0.75, avg_dl=8.0):
        if not doc_tokens: return 0.0
        dl   = len(doc_tokens)
        freq = {t: doc_tokens.count(t) for t in set(query_tokens) & set(doc_tokens)}
        score = 0.0
        for qt in query_tokens:
            f = freq.get(qt, 0)
            if f == 0: continue
            tf    = (f * (k1 + 1)) / (f + k1 * (1 - b + b * dl / avg_dl))
            score += math.log(2.0) * tf
        return score

    def retrieve_dom_context(self, dom, goal, top_k=30, viewport_bonus=2.0):
        if not dom: return []
        q_tok  = self._tokenize(goal)
        scored = []
        for el in dom:
            doc   = " ".join(filter(None, [el.get("text",""), el.get("tag",""),
                                           el.get("type",""), el.get("selector","")]))
            score = self._bm25_score(q_tok, self._tokenize(doc))
            if el.get("in_viewport"): score *= viewport_bonus
            scored.append((score, el))
        scored.sort(key=lambda x: (-x[0], x[1].get("vp_top", 9999)))
        top = [el for s, el in scored if s > 0][:top_k]
        return [{"tag": el.get("tag"), "selector": el.get("selector"),
                 "text": el.get("text"), "type": el.get("type"),
                 "value": el.get("value")} for el in top]

    # ── Action parser ─────────────────────────────────────────────────────────

    VALID_TOOLS = {
        "click", "type", "clear_and_type", "open_url", "press_key",
        "select_option", "hover", "double_click", "right_click", "go_back",
        "scroll_down", "scroll_up", "scroll_to_element", "scroll_to_top",
        "scroll_to_bottom", "verify_text_present", "verify_text_absent",
        "verify_element_visible", "verify_element_enabled", "verify_url_contains",
        "verify_page_title", "verify_input_value", "verify_element_count",
        "get_text", "wait_for_element", "wait_for_text", "wait_for_url_change",
        "wait_for_network_idle", "wait", "get_current_url", "get_page_title",
        "raise_bug_ticket", "mark_step_pass", "mark_step_fail", "mark_flow_blocked",
        "add_test_comment", "capture_evidence", "screenshot_diff",
    }

    def extract_action(self, text: str):
        """
        Parse Action: line from model output.
        Returns dict with 'tool' and 'args', or None if action is absent/none.
        Returns {"tool": "__parse_error__"} on malformed JSON.
        """
        m = re.search(r"^Action:\s*(.+)$", text, re.MULTILINE)
        if not m:
            return None
        raw = m.group(1).strip()
        if raw.lower() in ("none", "null", ""):
            return None
        # Normalise quotes
        raw = (raw.replace("\u2018", "'").replace("\u2019", "'")
                  .replace("\u201c", '"').replace("\u201d", '"'))
        raw = re.sub(r'[^\x00-\x7F]+', '', raw)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            raw2 = raw.replace("'", '"')
            try:
                parsed = json.loads(raw2)
            except Exception:
                return {"tool": "__parse_error__", "args": {}}
        if isinstance(parsed, list):
            valid = [a for a in parsed if isinstance(a, dict) and a.get("tool") in self.VALID_TOOLS]
            return valid[0] if valid else {"tool": "__parse_error__", "args": {}}
        if isinstance(parsed, dict) and parsed.get("tool") in self.VALID_TOOLS:
            return parsed
        return {"tool": "__parse_error__", "args": {}}

    # ── Thread run ────────────────────────────────────────────────────────────

    def run(self):
        if self.mode == "api":
            self._run_api()
        else:
            self._run_local()

    def _run_api(self):
        self.phase_changed.emit("checking", "Connecting to HuggingFace Space…")
        self.hw_info.emit(False, 0.0, 0.0, "HuggingFace Cloud")
        try:
            import urllib.request
            urllib.request.urlopen(self._space.space_url, timeout=10)
        except Exception as e:
            self.phase_changed.emit("error", f"Cannot reach Space: {e}")
            return
        self.phase_changed.emit("ready", "Connected to HuggingFace Space ✓")
        self.model_ready.emit()
        self._main_loop()

    def _run_local(self):
        self.phase_changed.emit("checking", "Checking hardware…")
        try:
            import torch
            if torch.cuda.is_available():
                props = torch.cuda.get_device_properties(0)
                self.hw_info.emit(True, props.total_memory / (1024**3),
                                  16.0, torch.cuda.get_device_name(0))
            else:
                self.hw_info.emit(False, 0.0, 0.0, "CPU")
        except ImportError:
            self.hw_info.emit(False, 0.0, 0.0, "torch not installed")

        try:
            from constants import REPO_ID
            from unsloth import FastVisionModel
            from transformers import Qwen2VLProcessor
            self.phase_changed.emit("loading", "Loading model into memory…")
            self.model, _ = FastVisionModel.from_pretrained(REPO_ID, load_in_4bit=True)
            FastVisionModel.for_inference(self.model)
            self.processor = Qwen2VLProcessor.from_pretrained(REPO_ID)
            self.model_ready.emit()
            self.phase_changed.emit("ready", "Aegis Vision Ready")
        except Exception as e:
            self.phase_changed.emit("error", f"Model Load Error: {e}")
            return

        self._main_loop()

    def _main_loop(self):
        while self.running:
            task = None
            with self.lock:
                if self.chat_queue:
                    task = self.chat_queue.pop(0)
            if task:
                user_text, history = task
                self._chat_inference(user_text, history)
            self.msleep(100)

    # ── Chat routing ──────────────────────────────────────────────────────────

    def _chat_inference(self, user_text: str, history: list):
        needs_agent = any(t in user_text.lower() for t in AGENTIC_TRIGGERS)
        try:
            if needs_agent:
                result = self._react_loop(user_text)
            else:
                result = self._plain_chat(user_text, history)
        except Exception as e:
            result = f"[Error] {e}"
        self.chat_reply.emit(result)

    # ── Plain chat ────────────────────────────────────────────────────────────

    def _plain_chat(self, user_text: str, history: list) -> str:
        messages = [{"role": "system", "content": "You are Orvion, a helpful AI assistant. Answer clearly and concisely."}]
        for h in history[-4:]:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": user_text})
        if self.mode == "api":
            return self._space.chat(messages)
        return self._plain_chat_local(messages)

    def _plain_chat_local(self, messages: list) -> str:
        if self.model is None or self.processor is None:
            return "[Error] Local model not loaded."
        try:
            import torch
            fmt = [{"role": m["role"], "content": [{"type": "text", "text": m["content"]}]}
                   for m in messages]
            input_text = self.processor.apply_chat_template(fmt, tokenize=False, add_generation_prompt=True)
            inputs = self.processor(text=[input_text], padding=True, return_tensors="pt").to("cuda")
            with torch.inference_mode():
                outputs = self.model.generate(**inputs, max_new_tokens=250, do_sample=False)
            generated = outputs[:, inputs["input_ids"].shape[1]:]
            return self.processor.batch_decode(generated, skip_special_tokens=True)[0].strip()
        except Exception as e:
            return f"[Error] Plain chat failed: {e}"

    # ── ReAct loop ────────────────────────────────────────────────────────────

    def _react_loop(self, goal: str, max_steps: int = 40) -> str:
        """
        Clean single-observation ReAct loop matching training data format.

        Each step sends:
          System: Aegis system prompt
          User:   [screenshot] + <CONTEXT_BLOCK>[DOM][OBSERVATIONS: prev step only]</CONTEXT_BLOCK> + goal

        The goal is ALWAYS the original user query — never changes.
        OBSERVATIONS contains only the immediately previous thought/action/result.
        Loop ends on [GOAL ACHIEVED], [FLOW BLOCKED], action=None, or max_steps.
        """
        # last_obs holds the single previous step for the OBSERVATIONS block
        last_obs: dict = {}   # keys: thought, action, tool_result
        stale_count = 0
        last_action_sig = None

        for step in range(1, max_steps + 1):
            # ── 1. Capture browser state ──────────────────────────────────────
            self.browser_state = None
            self.request_browser_state.emit()
            waited = 0
            while self.browser_state is None and waited < 15000:
                self.msleep(50); waited += 50
            if not self.browser_state:
                self.step_log.emit("⚠ Browser state timeout — skipping step")
                continue

            screenshot_bytes, dom_raw = self.browser_state
            dom          = json.loads(dom_raw) if isinstance(dom_raw, str) else dom_raw
            relevant_dom = self.retrieve_dom_context(dom, goal, top_k=30)

            # ── 2. Build OBSERVATIONS block (only previous step) ──────────────
            if last_obs:
                obs_text = (
                    f"Previous Thought: {last_obs['thought']}\n"
                    f"Previous Action: {json.dumps(last_obs['action'])}\n"
                    f"Tool Result: {last_obs['tool_result']}"
                )
            else:
                obs_text = "None"

            context_block = (
                f"<CONTEXT_BLOCK>\n"
                f"[DOM]:\n{json.dumps(relevant_dom)}\n"
                f"[OBSERVATIONS]:\n{obs_text}\n"
                f"</CONTEXT_BLOCK>"
            )

            # ── 3. Build message — single system + single user ────────────────
            user_content = f"{context_block}\n\n{goal}"
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_content},
            ]

            # ── 4. Call model ─────────────────────────────────────────────────
            if self.mode == "api":
                response = self._space.chat(messages, image_bytes=screenshot_bytes)
            else:
                response = self._react_local(screenshot_bytes, context_block, goal)

            # ── 5. Emit thought + action to chat panel ────────────────────────
            thought_line = ""
            for line in response.split("\n"):
                if line.startswith("Thought:"):
                    thought_line = line
                    break
            self.step_log.emit(f"💭 {thought_line or response[:120]}")

            action_line = ""
            for line in response.split("\n"):
                if line.startswith("Action:"):
                    action_line = line
                    break
            if action_line:
                self.step_log.emit(f"⚡ {action_line}")

            self.log_signal.emit(f"Aegis[{step}]: {response[:200]}", "#AAAAAA")

            # ── 6. Check terminal conditions ──────────────────────────────────
            if "[GOAL ACHIEVED]" in response:
                self.step_log.emit("✅ [GOAL ACHIEVED]")
                return response
            if "[FLOW BLOCKED]" in response:
                self.step_log.emit("🚫 [FLOW BLOCKED]")
                return response

            # ── 7. Parse action ───────────────────────────────────────────────
            action = self.extract_action(response)

            if action is None:
                # Model decided no action needed — done
                self.step_log.emit("⏹ No action — loop complete")
                return response

            if action.get("tool") == "__parse_error__":
                self.step_log.emit("⚠ Parse error — retrying next step")
                last_obs = {
                    "thought":     thought_line or "Parse error",
                    "action":      action,
                    "tool_result": "parse_error",
                }
                continue

            # ── 8. Stale detection ────────────────────────────────────────────
            sig = json.dumps(action, sort_keys=True)
            if sig == last_action_sig:
                stale_count += 1
            else:
                stale_count = 0
                last_action_sig = sig

            if stale_count >= 3:
                self.step_log.emit("⚠ Stale action x3 — aborting")
                return f"[Stuck] Repeated action {stale_count} times: {sig}"

            # ── 9. Execute tool via main thread ───────────────────────────────
            tool = action.get("tool", "")
            args = action.get("args", {})
            self.step_log.emit(f"🔧 {tool}({', '.join(f'{k}={repr(v)[:40]}' for k,v in args.items())})")

            self._pending_tool_result = None
            self.tool_request.emit(tool, args)
            waited = 0
            while self._pending_tool_result is None and waited < 15000:
                self.msleep(50); waited += 50

            tool_result = str(self._pending_tool_result or "timeout")
            self.step_log.emit(f"   → {tool_result[:80]}")

            # ── 10. Store as single observation for next step ─────────────────
            last_obs = {
                "thought":     thought_line or "...",
                "action":      action,
                "tool_result": tool_result,
            }

            # Wait after navigation/interaction tools
            if tool in ("open_url", "click", "double_click", "right_click", "press_key", "go_back"):
                self.msleep(1500)
            else:
                self.msleep(600)

        return f"[Max steps ({max_steps}) reached]"

    # ── Local vision inference ────────────────────────────────────────────────

    def _react_local(self, screenshot_bytes: bytes, context_block: str, goal: str) -> str:
        if self.model is None or self.processor is None:
            return "[Error] Local model not loaded."
        try:
            import torch
            from PIL import Image
            from qwen_vl_utils import process_vision_info
            screenshot = Image.open(BytesIO(screenshot_bytes))
            messages = [
                {"role": "system", "content": [{"type": "text", "text": SYSTEM_PROMPT}]},
                {"role": "user",   "content": [
                    {"type": "image", "image": screenshot},
                    {"type": "text",  "text": f"{context_block}\n\n{goal}"},
                ]},
            ]
            input_text = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True)
            image_inputs, video_inputs = process_vision_info(messages)
            inputs = self.processor(
                text=[input_text], images=image_inputs,
                videos=video_inputs, padding=True, return_tensors="pt").to("cuda")
            with torch.inference_mode():
                outputs = self.model.generate(
                    **inputs, max_new_tokens=200, do_sample=False, temperature=0.0)
            return self.processor.batch_decode(
                [outputs[0][inputs["input_ids"].shape[1]:]],
                skip_special_tokens=True)[0].strip()
        except Exception as e:
            return f"[Error] Local vision failed: {e}"