"""
agent_worker.py  (v2 — record / rerun / self-heal)
───────────────────────────────────────────────────
Two modes, same Qt signals.

  API mode   → screenshot + scored DOM → HuggingFace Space via direct HTTP.
  Local mode → screenshot + scored DOM → local Qwen2.5-VL (torch + unsloth).

Execution modes
───────────────
  RECORD  (first run)
    Each user message runs the full DOM pipeline + LLM.
    Parsed action is saved to test_steps with cx/cy coordinates.
    Only the final Answer is emitted to chat; Thought/Action are silent.

  RERUN
    Steps are loaded from DB and replayed by coordinate.
    If an action fails (element not at expected position or DOM changed),
    self-healing kicks in: DOM pipeline + LLM finds the element again,
    updates the step in DB, and continues.

Self-healing flow
─────────────────
  1. Action fails (execute_step returns error string).
  2. Emit  step_log("Orvion is attempting self healing…").
  3. Capture fresh screenshot + DOM → score_and_select(original task hint).
  4. Call LLM → parse new action.
  5. Update test_steps row with new cx/cy/elem_* and status='healed'.
  6. Execute the new action.
"""

import json
import os
import pathlib
import re
import tempfile
import threading
import time
import traceback
from typing import Any, Dict, List, Optional

from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition
from dotenv import load_dotenv

load_dotenv()

from inference_helpers import (
    SYSTEM_PROMPT,
    score_and_select,
    format_dom_for_model,
    build_prompt,
    build_space_prompt,
    parse_output,
    warmup_scorer,
)


# ── Config ────────────────────────────────────────────────────────────────────

def _load_config() -> dict:
    cfg = pathlib.Path(os.environ.get("ORVION_APP_DATA", "")) / "orvion_config.json"
    if cfg.exists():
        try:
            return json.loads(cfg.read_text())
        except Exception:
            pass
    return {"mode": "api", "space_url": "https://sanax3065-orivion-api.hf.space"}


# ── Space client ──────────────────────────────────────────────────────────────

class _SpaceClient:
    def __init__(self, space_url: str):
        self.space_url = space_url.rstrip("/")

    def _call_direct(self, prompt_text: str, image_bytes: bytes = None) -> str:
        import urllib.request
        import urllib.parse
        import uuid

        session_hash = uuid.uuid4().hex
        hf_token     = os.getenv("HF_TOKEN", "")
        auth_hdr     = {"Authorization": f"Bearer {hf_token}"} if hf_token else {}

        image_ref = None
        if image_bytes is not None:
            try:
                image_ref = self._upload_file(image_bytes, hf_token)
            except Exception:
                image_ref = None

        body = json.dumps({
            "data":         [prompt_text, image_ref],
            "fn_index":     0,
            "session_hash": session_hash,
        }).encode()
        req = urllib.request.Request(
            f"{self.space_url}/queue/join",
            data=body,
            headers={"Content-Type": "application/json", **auth_hdr},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                jr = json.loads(r.read())
        except Exception as e:
            raise RuntimeError(f"queue/join failed: {e}")
        if "error" in jr:
            raise RuntimeError(f"queue/join error: {jr['error']}")

        qs = f"session_hash={urllib.parse.quote(session_hash)}"
        if hf_token:
            qs += f"&__hf_token={urllib.parse.quote(hf_token)}"
        sse_req = urllib.request.Request(
            f"{self.space_url}/queue/data?{qs}",
            headers={"Accept": "text/event-stream",
                     "Cache-Control": "no-cache", **auth_hdr},
        )
        buf, deadline = "", time.time() + 180
        with urllib.request.urlopen(sse_req, timeout=180) as sse:
            while time.time() < deadline:
                chunk = sse.read(4096)
                if not chunk:
                    break
                buf += chunk.decode("utf-8", errors="replace")
                while "\n\n" in buf:
                    msg, buf = buf.split("\n\n", 1)
                    for line in msg.split("\n"):
                        if not line.startswith("data:"):
                            continue
                        try:
                            ev = json.loads(line[5:].strip())
                        except Exception:
                            continue
                        mt = ev.get("msg", "")
                        if mt == "process_completed":
                            out = ev.get("output", {}).get("data", [])
                            return str(out[0]).strip() if out else ""
                        if mt == "queue_full":
                            raise RuntimeError("Space queue is full — retry shortly")
        raise RuntimeError("SSE stream ended without a result")

    def _upload_file(self, image_bytes: bytes, hf_token: str) -> dict:
        import urllib.request
        import uuid
        boundary = uuid.uuid4().hex
        body = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="files"; filename="shot.png"\r\n'
            "Content-Type: image/png\r\n\r\n"
        ).encode() + image_bytes + f"\r\n--{boundary}--\r\n".encode()
        hdrs = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
        if hf_token:
            hdrs["Authorization"] = f"Bearer {hf_token}"
        req = urllib.request.Request(
            f"{self.space_url}/upload", data=body, headers=hdrs, method="POST")
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read())
        return result[0] if isinstance(result, list) and result else result

    def _call_gradio_client(self, prompt_text: str, image_bytes: bytes = None) -> str:
        from gradio_client import Client
        hf_token = os.getenv("HF_TOKEN")
        try:
            client = Client(self.space_url, hf_token=hf_token)
        except TypeError:
            client = Client(self.space_url, token=hf_token)
        image_arg = None
        if image_bytes is not None:
            from gradio_client import handle_file
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tmp.write(image_bytes)
            tmp.close()
            image_arg = handle_file(tmp.name)
        return str(client.predict(
            prompt_text=prompt_text, image_file=image_arg, api_name="/generate",
        )).strip()

    def generate(self, prompt_text: str, image_bytes: bytes = None) -> str:
        try:
            return self._call_direct(prompt_text, image_bytes=image_bytes)
        except Exception as de:
            try:
                return self._call_gradio_client(prompt_text, image_bytes=image_bytes)
            except Exception as ge:
                raise RuntimeError(
                    f"Both paths failed.\n  Direct: {de}\n  gradio_client: {ge}")


# ── Agentic trigger detection ─────────────────────────────────────────────────

AGENTIC_TRIGGERS = (
    "open ", "go to ", "navigate", "search for", "click",
    "type ", "browse", "find on", "look up", "url ",
    "website", "google", "automate", "execute", "fill in",
    "log in", "login", "verify", "check", "scroll",
    "double click", "right click", "hover", "fill", "select",
)

def _is_agentic(text: str) -> bool:
    lower = text.lower()
    return any(t in lower for t in AGENTIC_TRIGGERS)


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
    step_log              = pyqtSignal(str)       # internal; NOT shown in chat
    tool_request          = pyqtSignal(str, dict)
    tool_result_ready     = pyqtSignal(object)
    setup_requested       = pyqtSignal()
    setup_result_ready    = pyqtSignal(str, str)
    request_screenshot    = pyqtSignal()
    screenshot_ready      = pyqtSignal(bytes)
    # New signals
    rerun_status          = pyqtSignal(str)       # "Running step 2/5…" etc.
    self_healing          = pyqtSignal(str)       # "Orvion is attempting self healing…"

    def __init__(self, db=None):
        super().__init__()
        self.running              = True
        self.mutex                = QMutex()
        self.condition            = QWaitCondition()
        self.browser_state        = None
        self._pending_tool_result = None
        self.chat_queue: list     = []
        self.lock                 = threading.Lock()
        self.model                = None
        self.processor            = None
        self.db                   = db   # Database instance (injected by main_window)

        cfg       = _load_config()
        self.mode = cfg.get("mode", "api")
        space_url = cfg.get("space_url",
                            os.environ.get("ORVION_SPACE_URL",
                                           "https://sanax3065-orivion-api.hf.space"))
        self._space = _SpaceClient(space_url) if self.mode == "api" else None

        # Rerun queue: list of conv_ids to re-execute
        self._rerun_queue: list = []

    # ── Qt signal handlers ────────────────────────────────────────────────────

    def enqueue_chat(self, user_text: str, history: list, conv_id: int = None):
        with self.lock:
            self.chat_queue.append((user_text, history, conv_id))

    def enqueue_rerun(self, conv_id: int):
        with self.lock:
            self._rerun_queue.append(conv_id)

    def _on_tool_result(self, result):
        self._pending_tool_result = result

    def _on_browser_state_ready(self, screenshot: bytes, dom_json: str):
        try:
            raw_dom = json.loads(dom_json) if dom_json else []
        except Exception:
            raw_dom = []
        self.browser_state = (screenshot, raw_dom)

    def _on_screenshot_ready(self, data: bytes):
        pass

    def _on_setup_result(self, mode: str, url: str):
        pass

    # ── Thread entry points ───────────────────────────────────────────────────

    def run(self):
        if self.mode == "api":
            self._run_api()
        else:
            self._run_local()

    def _run_api(self):
        self.phase_changed.emit("checking", "Connecting to HuggingFace Space\u2026")
        self.hw_info.emit(False, 0.0, 0.0, "HuggingFace Cloud")
        try:
            import urllib.request
            urllib.request.urlopen(self._space.space_url, timeout=10)
        except Exception as e:
            self.phase_changed.emit("error", f"Cannot reach Space: {e}")
            return
        # Pre-load sentence-transformer so first query has no delay
        self.phase_changed.emit("loading", "Loading sentence scorer\u2026")
        warmup_scorer()
        self.phase_changed.emit("ready", "Connected to HuggingFace Space \u2713")
        self.model_ready.emit()
        self._main_loop()

    def _run_local(self):
        self.phase_changed.emit("checking", "Checking hardware\u2026")
        try:
            import torch
            if torch.cuda.is_available():
                props = torch.cuda.get_device_properties(0)
                self.hw_info.emit(True, props.total_memory / (1024 ** 3),
                                  16.0, torch.cuda.get_device_name(0))
            else:
                self.hw_info.emit(False, 0.0, 0.0, "CPU (no CUDA)")
        except ImportError:
            self.hw_info.emit(False, 0.0, 0.0, "torch not installed")
            self.phase_changed.emit("error", "PyTorch not found — local mode requires torch.")
            return
        try:
            from constants import REPO_ID
            from unsloth import FastVisionModel
            self.phase_changed.emit("loading", "Loading model into memory\u2026")
            self.model, self.processor = FastVisionModel.from_pretrained(
                REPO_ID, load_in_4bit=True, use_gradient_checkpointing=False)
            if hasattr(self.processor, "image_processor"):
                self.processor.image_processor.max_pixels = 512 * 512
            FastVisionModel.for_inference(self.model)
            self.model.eval()
            self.model_ready.emit()
            self.phase_changed.emit("ready", "Aegis Vision Ready \u2713")
        except Exception as e:
            self.phase_changed.emit("error", f"Model load error: {e}")
            return
        self._main_loop()

    # ── Main event loop ───────────────────────────────────────────────────────

    def _main_loop(self):
        while self.running:
            # Check rerun queue first
            rerun_id = None
            chat_entry = None
            with self.lock:
                if self._rerun_queue:
                    rerun_id = self._rerun_queue.pop(0)
                elif self.chat_queue:
                    chat_entry = self.chat_queue.pop(0)

            if rerun_id is not None:
                self._do_rerun(rerun_id)
            elif chat_entry is not None:
                user_text, _history, conv_id = chat_entry
                self._handle_task(user_text, conv_id)
            else:
                self.msleep(50)

    # ── RECORD mode: first-run task handling ──────────────────────────────────

    def _handle_task(self, task: str, conv_id: int = None):
        """Full LLM run. Saves action to DB. Emits only the answer to chat."""

        # Step 1: capture browser state if agentic
        if _is_agentic(task):
            self.step_log.emit("Capturing page state\u2026")
            self.browser_state = None
            self.request_browser_state.emit()
            deadline = time.time() + 10.0
            while self.browser_state is None and time.time() < deadline:
                self.msleep(50)
            if self.browser_state is None:
                err = "Could not capture browser state (timeout)."
                self._log_error(conv_id, err)
                self.chat_reply.emit(err)
                return
            screenshot_bytes, raw_dom = self.browser_state
        else:
            screenshot_bytes, raw_dom = None, []

        # Step 2: score DOM
        scored = score_and_select(raw_dom, task, top_k=5) if raw_dom else []

        # Step 3: inference
        self.step_log.emit("Sending to model\u2026")
        try:
            if self.mode == "api":
                raw_output = self._infer_api(task, scored, screenshot_bytes)
            else:
                raw_output = self._infer_local(task, scored, screenshot_bytes)
        except Exception as exc:
            err = str(exc)
            self._log_error(conv_id, f"Inference error: {err}")
            self.chat_reply.emit(f"\u26a0\ufe0f Inference error: {err}")
            return

        # Step 4: parse
        action_type, elem_idx, value, thought, answer = parse_output(
            raw_output, pool_size=len(scored))

        # Step 5: dispatch
        if action_type in ("answer", ""):
            self.chat_reply.emit(answer or thought or raw_output)
            return

        if action_type == "bug_report":
            msg = f"Bug filed \u2014 {value}"
            if conv_id and self.db:
                self.db.add_message(conv_id, "assistant", msg)
            self.chat_reply.emit(msg)
            return

        # Executable action — get element coordinates
        element = (scored[elem_idx]
                   if elem_idx is not None and 0 <= elem_idx < len(scored)
                   else None)
        cx = element["box"]["cx"] if element else 0
        cy = element["box"]["cy"] if element else 0
        elem_text = element.get("text", "") if element else ""
        elem_tag  = element.get("tag",  "") if element else ""
        elem_type = element.get("type", "") if element else ""

        # Save step to DB
        step_id = None
        if conv_id and self.db:
            step_order = self.db.next_step_order(conv_id)
            step_id    = self.db.add_step(
                conv_id, step_order, action_type, elem_idx, value,
                cx, cy, elem_text, elem_tag, elem_type, thought
            )

        # Execute in browser
        result = self._execute_step(action_type, cx, cy, value, element=element)
        is_error = isinstance(result, str) and result.startswith("ERROR")

        if is_error:
            self._log_error(conv_id, result, step_id=step_id)
            if step_id and self.db:
                self.db.set_step_status(step_id, "failed")
            self.chat_reply.emit(f"\u26a0\ufe0f {result}")
        else:
            if step_id and self.db:
                self.db.set_step_status(step_id, "passed")
            reply = answer or f"Done \u2014 {action_type}({elem_idx})"
            self.chat_reply.emit(reply)

    # ── RERUN mode ────────────────────────────────────────────────────────────

    def _do_rerun(self, conv_id: int):
        """Replay all recorded steps for a conversation."""
        if not self.db:
            self.chat_reply.emit("\u26a0\ufe0f Database not connected.")
            return

        conv = self.db.get_conversation(conv_id)
        if not conv:
            self.chat_reply.emit("\u26a0\ufe0f Conversation not found.")
            return

        # Navigate to test URL if set
        url = conv["url"] if conv["url"] else None
        if url:
            self.tool_request.emit("open_url", {"url": url})
            self._wait_tool_result(timeout=15)
            self.msleep(1500)

        steps = self.db.get_steps(conv_id)
        if not steps:
            self.chat_reply.emit("No recorded steps to run.")
            return

        self.rerun_status.emit(f"Re-running {len(steps)} step(s)\u2026")

        for i, step in enumerate(steps):
            step_id  = step["id"]
            tool     = step["tool"]
            value    = step["value"]
            cx, cy   = step["cx"], step["cy"]
            elem_text = step["elem_text"]
            elem_tag  = step["elem_tag"]
            elem_type = step["elem_type"]
            thought   = step["thought"]

            self.rerun_status.emit(
                f"Step {i+1}/{len(steps)}: {tool}({elem_text[:30] or f'{cx},{cy}'})")

            # Build element dict from stored step metadata
            step_el = {
                "id":   "",   # not stored (pre-heal steps); self-heal will refresh
                "name": "",
                "cls":  "",
                "tag":  elem_tag,
                "type": elem_type,
            }
            result = self._execute_step(tool, cx, cy, value, element=step_el)
            is_error = isinstance(result, str) and result.startswith("ERROR")

            if is_error:
                # ── Self-healing ───────────────────────────────────────────
                self.self_healing.emit(
                    f"Orvion is attempting self healing for step {i+1}\u2026")
                self._log_error(conv_id, result, step_id=step_id)

                heal_result = self._self_heal(
                    step_id=step_id, conv_id=conv_id,
                    original_task=f"{tool} element with text '{elem_text}' "
                                  f"type='{elem_type}'",
                    tool=tool, value=value,
                )
                if heal_result == "healed":
                    self.rerun_status.emit(
                        f"Step {i+1} healed and executed \u2713")
                else:
                    self.db.set_step_status(step_id, "failed")
                    self.rerun_status.emit(
                        f"Step {i+1} could not be healed \u2014 stopping.")
                    self.chat_reply.emit(
                        f"\u26a0\ufe0f Re-run stopped at step {i+1}: "
                        f"{tool} failed and self-healing did not recover.")
                    return
            else:
                self.db.set_step_status(step_id, "passed")

        self.chat_reply.emit(
            f"\u2705 Re-run complete \u2014 {len(steps)} step(s) passed.")

    # ── Self-healing ──────────────────────────────────────────────────────────

    def _self_heal(self, step_id, conv_id, original_task, tool, value) -> str:
        """
        Capture current DOM, ask LLM for the right element, update the step.
        Returns 'healed' on success, 'failed' on failure.
        """
        self.browser_state = None
        self.request_browser_state.emit()
        deadline = time.time() + 10.0
        while self.browser_state is None and time.time() < deadline:
            self.msleep(50)
        if self.browser_state is None:
            return "failed"

        screenshot_bytes, raw_dom = self.browser_state
        scored = score_and_select(raw_dom, original_task, top_k=5) if raw_dom else []
        if not scored:
            return "failed"

        try:
            if self.mode == "api":
                raw_output = self._infer_api(original_task, scored, screenshot_bytes)
            else:
                raw_output = self._infer_local(original_task, scored, screenshot_bytes)
        except Exception as exc:
            self._log_error(conv_id, f"Self-heal inference error: {exc}",
                            step_id=step_id)
            return "failed"

        new_tool, new_elem_idx, new_value, new_thought, _ = parse_output(
            raw_output, pool_size=len(scored))

        if new_tool not in ("click", "type", "scroll", "select"):
            return "failed"

        element = (scored[new_elem_idx]
                   if new_elem_idx is not None and 0 <= new_elem_idx < len(scored)
                   else None)
        if not element:
            return "failed"

        new_cx   = element["box"]["cx"]
        new_cy   = element["box"]["cy"]
        new_val  = new_value if new_value else value  # keep original value if model omits it

        result = self._execute_step(new_tool, new_cx, new_cy, new_val,
                                    element=element)
        if isinstance(result, str) and result.startswith("ERROR"):
            self._log_error(conv_id, f"Self-heal execution failed: {result}",
                            step_id=step_id)
            return "failed"

        # Update DB with healed coordinates
        if self.db:
            self.db.update_step(
                step_id,
                new_cx, new_cy,
                element.get("text", ""), element.get("tag", ""), element.get("type", ""),
                new_val, new_thought, "healed"
            )
        return "healed"

    # ── Step execution ────────────────────────────────────────────────────────

    def _execute_step(self, tool: str, cx: int, cy: int, value: str,
                      element: dict = None) -> str:
        """
        Emit tool_request and wait for result.
        Returns result string; starts with 'ERROR' on failure.
        element dict carries id/name/cls/tag/type for selector resolution.
        """
        self._pending_tool_result = None
        args = {
            "cx":    cx,
            "cy":    cy,
            "value": value,
            # selector hints — priority: id > name > cls > tag+type > coords
            "el_id":   (element or {}).get("id",   ""),
            "el_name": (element or {}).get("name",  ""),
            "el_cls":  (element or {}).get("cls",   ""),
            "el_tag":  (element or {}).get("tag",   ""),
            "el_type": (element or {}).get("type",  ""),
        }
        self.tool_request.emit(tool, args)
        return self._wait_tool_result(timeout=15)

    def _wait_tool_result(self, timeout: int = 15) -> str:
        deadline = time.time() + timeout
        while self._pending_tool_result is None and time.time() < deadline:
            self.msleep(50)
        return self._pending_tool_result or "ERROR: tool timeout"

    # ── Inference helpers ─────────────────────────────────────────────────────

    def _infer_api(self, task, scored, screenshot_bytes):
        prompt_text = (build_space_prompt(task, scored)
                       if scored else f"{SYSTEM_PROMPT}\n\nTask: {task}")
        return self._space.generate(prompt_text, image_bytes=screenshot_bytes)

    def _infer_local(self, task, scored, screenshot_bytes):
        import torch
        from qwen_vl_utils import process_vision_info
        tmp_path = None
        if screenshot_bytes:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                f.write(screenshot_bytes)
                tmp_path = f.name
        try:
            messages = (build_prompt(task, scored, tmp_path)
                        if (scored and tmp_path)
                        else [{"role": "user", "content": task}])
            text           = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True)
            img_in, vid_in = process_vision_info(messages)
            inputs         = self.processor(
                text=[text], images=img_in, videos=vid_in,
                padding=True, return_tensors="pt",
            ).to(self.model.device)
            with torch.no_grad():
                out_ids = self.model.generate(
                    **inputs, max_new_tokens=256, do_sample=False,
                    temperature=1.0, repetition_penalty=1.15)
            new_ids = out_ids[0][inputs["input_ids"].shape[1]:]
            return self.processor.decode(new_ids, skip_special_tokens=True).strip()
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    # ── Error logging ─────────────────────────────────────────────────────────

    def _log_error(self, conv_id, error_text, step_id=None, context=""):
        if self.db and conv_id:
            try:
                self.db.log_error(conv_id, error_text, context, step_id)
            except Exception:
                pass
        self.step_log.emit(f"\u26a0\ufe0f {error_text}")