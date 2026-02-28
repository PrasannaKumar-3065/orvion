import re
import json
import math
import threading
from io import BytesIO

import torch
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition
from unsloth import FastVisionModel
from transformers import Qwen2VLProcessor
from qwen_vl_utils import process_vision_info
from PIL import Image

from constants import REPO_ID


class AgentWorker(QThread):
    # --- All UI Signals ---
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
        self.model = None
        self.processor = None
        self.running = True
        self.mutex = QMutex()
        self.condition = QWaitCondition()
        self.browser_state = None
        self._pending_tool_result = None
        self.chat_queue = []
        self.lock = threading.Lock()
        self.mode = "local" # We default to local for Unsloth

    # ── UI Interface Methods ─────────────────────────────────────────────────

    def enqueue_chat(self, user_text: str, history: list):
        with self.lock:
            self.chat_queue.append((user_text, history))

    def _on_screenshot_ready(self, data):
        pass # Placeholder to prevent UI crash

    def _on_setup_result(self, mode, url):
        pass # Placeholder to prevent UI crash

    def _on_tool_result(self, result):
        self._pending_tool_result = result

    def _on_browser_state_ready(self, screenshot, dom):
        self.browser_state = (screenshot, dom)

    # ── Helpers (Exact Port from Inference Script) ───────────────────────────

    def _tokenize(self, text: str) -> list:
        return re.findall(r'[a-z0-9]+', text.lower())

    def _bm25_score(self, query_tokens: list, doc_tokens: list,
                    k1: float = 1.5, b: float = 0.75, avg_dl: float = 8.0) -> float:
        if not doc_tokens: return 0.0
        dl = len(doc_tokens)
        freq = {t: doc_tokens.count(t) for t in set(query_tokens) & set(doc_tokens)}
        score = 0.0
        for qt in query_tokens:
            f = freq.get(qt, 0)
            if f == 0: continue
            idf = math.log(2.0)
            tf = (f * (k1 + 1)) / (f + k1 * (1 - b + b * dl / avg_dl))
            score += idf * tf
        return score

    def retrieve_dom_context(self, dom: list, goal: str, top_k: int = 12, viewport_bonus: float = 2.0) -> list:
        if not dom: return []
        query_tokens = self._tokenize(goal)
        scored = []
        for el in dom:
            doc_text = " ".join(filter(None, [el.get("text", ""), el.get("tag", ""), el.get("type", ""), el.get("selector", "")]))
            doc_tokens = self._tokenize(doc_text)
            score = self._bm25_score(query_tokens, doc_tokens)
            if el.get("in_viewport"): score *= viewport_bonus
            scored.append((score, el))
        scored.sort(key=lambda x: (-x[0], x[1].get("vp_top", 9999)))
        results = [el for score, el in scored if score > 0][:top_k]
        return [{"tag": el.get("tag"), "selector": el.get("selector"), "text": el.get("text"), "type": el.get("type"), "value": el.get("value")} for el in results]

    def extract_first_action(self, text: str):
        m = re.search(r"Action:\s*(.+?)(?:\nFinal Answer:|\Z)", text, re.DOTALL)
        if not m: return None
        raw = m.group(1).strip()
        if raw.lower() in ("none", "null", ""): return None
        raw = raw.replace("\u2018", "'").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
        raw_json = raw.replace("'", '"')
        raw_json = re.sub(r'([}\]])\s*[^}\]]*$', r'\1', raw_json, count=1)
        raw_json = re.sub(r'[^\x00-\x7F]+', '', raw_json)
        try:
            parsed = json.loads(raw_json)
        except:
            return {"tool": "__parse_error__", "args": {}}

        VALID_TOOLS = ("click", "type", "open_url", "wait", "scroll")
        if isinstance(parsed, list):
            valid = [a for a in parsed if isinstance(a, dict) and a.get("tool") in VALID_TOOLS]
            return valid[0] if valid else {"tool": "__parse_error__", "args": {}}
        return parsed if (isinstance(parsed, dict) and parsed.get("tool") in VALID_TOOLS) else {"tool": "__parse_error__", "args": {}}

    # ── Model Lifecycle ──────────────────────────────────────────────────────

    def run(self):
        self.phase_changed.emit("checking", "Checking hardware...")
        self.log_signal.emit(f"Loading {REPO_ID} via Unsloth...", "#7C5CFC")

        # Emit HW info for the UI (using your 5070 Ti stats if available)
        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            vram_gb = props.total_memory / (1024**3)
            hw_name = torch.cuda.get_device_name(0)
            self.hw_info.emit(True, vram_gb, 16.0, hw_name)
        else:
            self.hw_info.emit(False, 0.0, 0.0, "CPU")

        try:
            self.phase_changed.emit("loading", "Loading model into memory...")
            self.model, _ = FastVisionModel.from_pretrained(REPO_ID, load_in_4bit=True)
            FastVisionModel.for_inference(self.model)
            self.processor = Qwen2VLProcessor.from_pretrained(REPO_ID)
            self.model_ready.emit()
            self.phase_changed.emit("ready", "Aegis Vision Ready")
        except Exception as e:
            self.log_signal.emit(f"Load Failed: {e}", "#FF5F57")
            self.phase_changed.emit("error", f"Model Load Error: {e}")
            return

        while self.running:
            task = None
            with self.lock:
                if self.chat_queue: task = self.chat_queue.pop(0)

            if task:
                user_text, history = task
                self._chat_inference(user_text, history)

            self.msleep(100)

    # ── Task Routing (Chat vs Action) ────────────────────────────────────────

    def _chat_inference(self, user_text: str, history: list):
        self.log_signal.emit("Processing…", "#E8A030")

        # Keywords that trigger the browser agent
        AGENTIC_TRIGGERS = (
            "open ", "go to ", "navigate", "search for", "click",
            "type ", "browse", "find on", "look up", "url ",
            "website", "google", "open url", "automate", "run test",
            "stress test", "execute", "fill in", "log in", "login",
        )
        needs_agent = any(t in user_text.lower() for t in AGENTIC_TRIGGERS)

        try:
            if needs_agent:
                raw_goals = re.split(r'[\n;]+', user_text.strip())
                subgoals  = [g.strip() for g in raw_goals if g.strip()] or [user_text.strip()]
                result    = self._react_loop(subgoals)
            else:
                result = self._plain_chat_local(user_text, history)
        except Exception as e:
            result = f"[Error] {e}"

        self.chat_reply.emit(result)

    def _plain_chat_local(self, user_text: str, history: list) -> str:
        if self.model is None or self.processor is None:
            return "[Error] Local model not loaded."
        try:
            # Format history for standard Qwen text generation
            messages = [{"role": "system", "content": [{"type": "text", "text": "You are Orvion, a helpful AI assistant."}]}]
            for h in history[-4:]:
                messages.append({"role": h["role"], "content": [{"type": "text", "text": h["content"]}]})
            messages.append({"role": "user", "content": [{"type": "text", "text": user_text}]})

            input_text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = self.processor(text=[input_text], padding=True, return_tensors="pt").to("cuda")

            with torch.inference_mode():
                outputs = self.model.generate(**inputs, max_new_tokens=250, do_sample=False)

            generated_ids = outputs[:, inputs["input_ids"].shape[1]:]
            return self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
        except Exception as e:
            return f"[Error] Plain chat failed: {e}"

    # ── The Stress Test Core Loop ────────────────────────────────────────────

    def _react_loop(self, subgoals: list, max_steps: int = 40):
        history = []
        goal_idx = 0
        last_action_sig = None
        stale_count = 0
        abstain_count = 0
        ABSTAIN_LIMIT = 4

        for step in range(1, max_steps + 1):
            if goal_idx >= len(subgoals): break
            current_goal = subgoals[goal_idx]
            self.step_log.emit(f"Step {step} | Goal {goal_idx+1}: {current_goal[:50]}...")

            # 1. Capture State
            self.browser_state = None
            self.request_browser_state.emit()
            waited = 0
            while self.browser_state is None and waited < 15000:
                self.msleep(50); waited += 50

            if not self.browser_state: continue
            screenshot_bytes, dom_raw = self.browser_state
            screenshot = Image.open(BytesIO(screenshot_bytes))
            dom = json.loads(dom_raw) if isinstance(dom_raw, str) else dom_raw

            # 2. Context Building
            relevant_dom = self.retrieve_dom_context(dom, current_goal, top_k=30)
            obs_text = "\n".join(str(h) for h in history[-5:])
            context_block = f"<CONTEXT_BLOCK>\n[DOM]:\n{json.dumps(relevant_dom)}\n" + \
                            (f"[OBSERVATIONS]:\n{obs_text}\n" if obs_text else "") + "</CONTEXT_BLOCK>"

            # 3. System Prompt & Messages
            system_text = (
                "You are Aegis. Current Mode: QUALITY_TESTER\n"
                "RULES: 1. You are FORBIDDEN from outputting [GOAL ACHIEVED] unless you visually see the success state."
                "2. If you click a button and the page does not change, you MUST try a different selector or strategy."
                "3. NEVER make up selectors. Use the provided [DOM] list exactly."
                'Tools: [{"name": "click", "description": "Click an element", "args": {"selector": "string"}}, '
                '{"name": "type", "description": "Types into an input", "args": {"selector": "string", "text": "string"}}, '
                '{"name": "open_url", "description": "Navigate to URL", "args": {"url": "string"}}]'
            )
            messages = [
                {"role": "system", "content": [{"type": "text", "text": system_text}]},
                {"role": "user", "content": [{"type": "image", "image": screenshot}, {"type": "text", "text": f"{context_block}\n\n{current_goal}"}]}
            ]

            # 4. Inference
            input_text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            image_inputs, video_inputs = process_vision_info(messages)
            inputs = self.processor(text=[input_text], images=image_inputs, videos=video_inputs, padding=True, return_tensors="pt").to("cuda")

            with torch.inference_mode():
                outputs = self.model.generate(**inputs, max_new_tokens=150, do_sample=False, temperature=0.0)

            response = self.processor.batch_decode([outputs[0][inputs["input_ids"].shape[1]:]], skip_special_tokens=True)[0].strip()
            self.log_signal.emit(f"Aegis: {response[:200]}", "#AAAAAA")

            # 5. Goal Achievement Logic
            if "[GOAL ACHIEVED]" in response:
                goal_idx += 1; stale_count = 0; abstain_count = 0; last_action_sig = None
                if goal_idx >= len(subgoals):
                    return "Goal sequence complete."
                continue

            # 6. Action Extraction & Stale Detection
            action = self.extract_first_action(response)
            is_parse_error = isinstance(action, dict) and action.get("tool") == "__parse_error__"
            is_deliberate_none = action is None

            if not is_parse_error and not is_deliberate_none:
                sig = json.dumps(action, sort_keys=True)
                stale_count = stale_count + 1 if sig == last_action_sig else 0
                last_action_sig = sig
                abstain_count = 0
            else:
                stale_count = 0

            # 7. Stale Recovery & Abstention Logic
            if stale_count >= 3 or (is_deliberate_none and abstain_count >= ABSTAIN_LIMIT):
                self.step_log.emit("⚠️ Stale/Abstain Recovery: Force Advancing")
                goal_idx += 1; stale_count = 0; abstain_count = 0; last_action_sig = None
                continue

            if is_parse_error: continue
            if is_deliberate_none:
                abstain_count += 1; continue

            # 8. Tool Execution
            tool = action.get("tool")
            args = action.get("args")
            self.step_log.emit(f"⚡ {tool}: {args.get('selector') or args.get('url') or ''}")

            self._pending_tool_result = None
            self.tool_request.emit(tool, args)

            # Wait for main thread to execute via signals
            waited = 0
            while self._pending_tool_result is None and waited < 10000:
                self.msleep(50); waited += 50

            history.append({"thought": response, "action": action, "tool_result": str(self._pending_tool_result)})
            self.msleep(1200)

        return "Finished processing (Max steps reached)."
