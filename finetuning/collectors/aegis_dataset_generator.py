"""
AEGIS DATASET AUTO-GENERATOR
=============================
This script visits a website, executes a defined flow step-by-step,
captures screenshots + DOM at each step, and writes JSONL training records
automatically — so you never have to manually write records again.

HOW TO USE:
-----------
1. Install:  pip install playwright && playwright install chromium
2. Define your flows in FLOWS at the bottom of this file
3. Run: python aegis_dataset_generator.py
4. Output: aegis_generated.jsonl  (ready to merge with your training set)

FLOW DEFINITION FORMAT:
-----------------------
Each flow is a list of steps. Each step is a dict:
  {
    "action":     "type" | "click" | "select_option" | "verify_text_present" |
                  "verify_element_visible" | "verify_input_value" | "navigate" |
                  "scroll_down" | "wait" | "raise_bug_ticket" | "mark_step_pass",
    "selector":   "CSS selector" (not needed for navigate/scroll/wait),
    "value":      "text to type / option to select / expected value",
    "task":       "What the model is being asked to do (the user prompt)",
    "is_verify":  True if this step is a verification (gets [GOAL ACHIEVED]),
    "raises_bug": True if this step should produce a raise_bug_ticket action,
    "expected_color": "#hex"  (for color verification steps),
  }
"""

import asyncio
import base64
import json
import time
import re
from pathlib import Path
from playwright.async_api import async_playwright, Page

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────

OUTPUT_FILE = "aegis_generated.jsonl"
SCREENSHOT_DIR = Path("generated_screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)


def extract_json_object(text: str, start_marker: str = "Action: ") -> str | None:
    """Extract a JSON object with balanced braces — handles nested objects like {args: {url: ...}}."""
    idx = text.find(start_marker)
    if idx == -1:
        return None
    start = text.find("{", idx)
    if start == -1:
        return None
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None

# Full tool list — matches your deployed agent_worker.py exactly
TOOL_LIST = (
    "click, type, clear_and_type, open_url, press_key, select_option, hover, "
    "double_click, right_click, scroll_down, scroll_up, scroll_to_element, "
    "scroll_to_top, scroll_to_bottom, verify_text_present, verify_text_absent, "
    "verify_element_visible, verify_element_enabled, verify_url_contains, "
    "verify_page_title, verify_input_value, verify_element_count, get_text, "
    "screenshot_diff, check_email_received, verify_email_content, verify_email_sender, "
    "get_email_link, verify_no_email, wait_for_element, wait_for_text, "
    "wait_for_url_change, wait_for_network_idle, wait, get_current_url, "
    "get_page_title, raise_bug_ticket, mark_step_pass, mark_step_fail, "
    "mark_flow_blocked, add_test_comment, capture_evidence"
)

SYSTEM_PROMPT = f"You are Aegis. Current Mode: QUALITY_TESTER\nTools: [{TOOL_LIST}]"


# ─────────────────────────────────────────────────────────────
# CORE: DOM EXTRACTION
# ─────────────────────────────────────────────────────────────

async def extract_relevant_dom(page: Page, selector_hint: str = None) -> list:
    """
    Smart DOM extraction with 5-tier selector resolution + proximity filtering.

    Tier 1: data-testid / data-cy / data-qa  — most stable
    Tier 2: #id                              — stable
    Tier 3: aria-label / placeholder         — semantic
    Tier 4: label[for] association           — form standard
    Tier 5: tag + visible text               — last resort

    Proximity filter: if a target selector hint is given, elements within
    300px of the target are ranked higher than distant nav chrome.
    This mirrors the hybrid BM25 strategy from the v2 architecture doc.
    """
    elements = await page.evaluate("""(hint) => {
        const INTERACTIVE = [
            'input:not([type="hidden"])', 'textarea', 'select',
            'button', 'a[href]', '[role="button"]', '[role="combobox"]',
            '[role="textbox"]', '[role="listbox"]', '[role="option"]'
        ].join(', ');

        function getBestSelector(el) {
            // Tier 1: test attributes
            for (const attr of ['data-testid', 'data-cy', 'data-qa', 'data-test']) {
                if (el.getAttribute(attr)) return `[${attr}="${el.getAttribute(attr)}"]`;
            }
            // Tier 2: id
            if (el.id && !el.id.match(/^[0-9]/)) return '#' + el.id;
            // Tier 3: aria-label
            if (el.getAttribute('aria-label')) return `[aria-label="${el.getAttribute('aria-label')}"]`;
            // Tier 3b: placeholder
            if (el.placeholder) return `[placeholder="${el.placeholder}"]`;
            // Tier 4: name attribute
            if (el.name) return `[name="${el.name}"]`;
            // Tier 5: tag + first stable class (skip random CSS-module hashes)
            if (el.className && typeof el.className === 'string') {
                const stableClasses = el.className.trim().split(/\s+/)
                    .filter(c => c.length < 40 && !c.match(/[0-9]{4,}/) && !c.match(/^css-/));
                if (stableClasses.length > 0) {
                    return el.tagName.toLowerCase() + '.' + stableClasses.slice(0, 2).join('.');
                }
            }
            // Fallback: tag + text
            const text = (el.innerText || '').trim().substring(0, 20);
            return text ? `${el.tagName.toLowerCase()}:has-text("${text}")` : el.tagName.toLowerCase();
        }

        function getBox(el) {
            const r = el.getBoundingClientRect();
            return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)};
        }

        function isVisible(el) {
            const r = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            return r.width > 0 && r.height > 0
                && r.top < window.innerHeight && r.bottom > 0
                && style.visibility !== 'hidden' && style.display !== 'none'
                && parseFloat(style.opacity) > 0;
        }

        const all = Array.from(document.querySelectorAll(INTERACTIVE)).filter(isVisible);

        // Find target element for proximity scoring
        let targetBox = null;
        if (hint) {
            try {
                const target = document.querySelector(hint);
                if (target && isVisible(target)) {
                    targetBox = target.getBoundingClientRect();
                }
            } catch(e) {}
        }

        function proximityScore(el) {
            if (!targetBox) return 0;
            const r = el.getBoundingClientRect();
            const cx = Math.abs((r.x + r.width/2) - (targetBox.x + targetBox.width/2));
            const cy = Math.abs((r.y + r.height/2) - (targetBox.y + targetBox.height/2));
            const dist = Math.sqrt(cx*cx + cy*cy);
            return Math.max(0, 1 - dist / 400);  // score 1.0 at dist=0, 0.0 at dist=400px
        }

        // Score and rank elements
        const scored = all.map(el => ({
            el,
            score: proximityScore(el),
            isTarget: hint && el === (document.querySelector(hint) || null),
        }));

        scored.sort((a, b) => {
            if (a.isTarget) return -1;
            if (b.isTarget) return 1;
            return b.score - a.score;
        });

        return scored.slice(0, 5).map(({el}) => ({
            tag: el.tagName.toLowerCase(),
            selector: getBestSelector(el),
            text: (el.innerText || el.value || el.placeholder || el.getAttribute('aria-label') || '').substring(0, 80).trim(),
            type: el.type || el.getAttribute('role') || '',
            value: el.value || '',
            box: getBox(el)
        }));
    }""", selector_hint)
    return elements


async def take_screenshot_b64(page: Page, step_id: str) -> str:
    """Take screenshot and save to disk. Returns file path (for JSONL) and saves file."""
    path = SCREENSHOT_DIR / f"{step_id}.png"
    await page.screenshot(path=str(path), full_page=False)
    return str(path)


# ─────────────────────────────────────────────────────────────
# CORE: RESPONSE GENERATION
# ─────────────────────────────────────────────────────────────

def build_action_response(step: dict, dom: list, prev_action: dict = None) -> str:
    """
    Generate the assistant response for an ACTION step (not verify).
    One action, no [GOAL ACHIEVED].
    """
    action = step["action"]
    selector = step.get("selector", "")
    value = step.get("value", "")

    matching = next((d for d in dom if d["selector"] == selector), None)
    element_desc = f"with selector {selector}" if not matching else \
                   f"({matching['tag']} selector={selector}, current value='{matching.get('value','')}')"

    if action in ("type", "clear_and_type"):
        thought = f"The field {element_desc} is visible. I will clear any existing value and type \"{value}\"."
        action_json = {"tool": "clear_and_type", "args": {"selector": selector, "text": value}}
        final = f"Typed \"{value}\" into field. Awaiting updated screenshot and DOM for validation."

    elif action == "click":
        dom_text = matching["text"] if matching else ""
        thought = f"The {dom_text or 'target'} element {element_desc} is visible and enabled. I will click it."
        action_json = {"tool": "click", "args": {"selector": selector}}
        final = f"Clicked {dom_text or selector}. Awaiting page response."

    elif action == "double_click":
        thought = f"Element {element_desc} requires a double-click interaction."
        action_json = {"tool": "double_click", "args": {"selector": selector}}
        final = f"Double-clicked {selector}."

    elif action == "select_option":
        thought = f"Dropdown {element_desc} is visible. I will select the option \"{value}\"."
        action_json = {"tool": "select_option", "args": {"selector": selector, "value": value}}
        final = f"Selected \"{value}\" from dropdown."

    elif action == "navigate":
        thought = f"I need to navigate to {value} to begin or continue the flow."
        action_json = {"tool": "open_url", "args": {"url": value}}
        final = f"Navigated to {value}. Awaiting page load."

    elif action == "go_back":
        thought = "I need to navigate back to the previous page using the browser back action."
        action_json = {"tool": "go_back", "args": {}}
        final = "Navigated back to the previous page."

    elif action == "scroll_down":
        thought = "The target element may be below the current viewport. I will scroll down to reveal it."
        action_json = {"tool": "scroll_down", "args": {"pixels": 300}}
        final = "Scrolled down. Awaiting updated viewport."

    elif action == "scroll_to_element":
        thought = f"Element {selector} may be outside the current viewport. I will scroll it into view."
        action_json = {"tool": "scroll_to_element", "args": {"selector": selector}}
        final = f"Scrolled to element {selector}."

    elif action == "scroll_to_top":
        thought = "I will scroll the page back to the top."
        action_json = {"tool": "scroll_to_top", "args": {}}
        final = "Scrolled to top of page."

    elif action == "scroll_to_bottom":
        thought = "I will scroll to the bottom of the page to find elements below the fold."
        action_json = {"tool": "scroll_to_bottom", "args": {}}
        final = "Scrolled to bottom of page."

    elif action == "hover":
        thought = f"I need to hover over {element_desc} to trigger its hover state."
        action_json = {"tool": "hover", "args": {"selector": selector}}
        final = f"Hovering over {selector}. Awaiting hover state screenshot."

    elif action == "press_key":
        thought = f"I will press the {value} key to trigger the keyboard action."
        action_json = {"tool": "press_key", "args": {"key": value}}
        final = f"Pressed {value}."

    elif action == "wait_for_element":
        thought = f"Element {selector} may not yet be present in the DOM. I will wait for it to appear."
        action_json = {"tool": "wait_for_element", "args": {"selector": selector}}
        final = f"Waiting for element {selector} to appear."

    elif action == "wait_for_url_change":
        thought = f"The page is navigating. I will wait for the URL to contain '{value}' before proceeding."
        action_json = {"tool": "wait_for_url_change", "args": {"expected_substring": value}}
        final = f"Waiting for URL to change to contain '{value}'."

    elif action == "get_current_url":
        thought = "I will retrieve the current page URL to confirm we are on the expected page."
        action_json = {"tool": "get_current_url", "args": {}}
        final = "Retrieved current URL. Will verify it matches expected route."

    else:
        thought = f"Executing {action} on {selector}."
        action_json = {"tool": action, "args": {"selector": selector} if selector else {}}
        final = f"Executed {action}."

    return (
        f"Thought: {thought}\n"
        f"Action: {json.dumps(action_json)}\n"
        f"Final Answer: {final}"
    )


def build_verify_response(step: dict, dom: list, prev_step: dict = None) -> str:
    """
    Generate the assistant response for a VERIFICATION step.
    Uses appropriate verify tool. Adds [GOAL ACHIEVED] or [FLOW BLOCKED].
    """
    action = step["action"]
    selector = step.get("selector", "")
    value = step.get("value", "")
    raises_bug = step.get("raises_bug", False)
    is_blocked = step.get("is_blocked", False)
    bug_title = step.get("bug_title", f"Defect: {selector} — expected {value}")
    bug_severity = step.get("bug_severity", "Medium")
    expected_color = step.get("expected_color", "")
    observed_color = step.get("observed_color", "")

    terminal = "[FLOW BLOCKED]" if (raises_bug and is_blocked) else "[GOAL ACHIEVED]"

    # ── Bug/raise scenarios ────────────────────────────────────────
    if raises_bug:
        if action == "verify_color_fail":
            thought = (
                f"VISUAL_OBSERVATION: Element {selector} is visible in the screenshot. "
                f"Examining its color — it appears to be {observed_color or 'an unexpected color'} visually. "
                f"The test specification requires it to be {value}. "
                f"These do NOT match. This is a UI defect that must be reported."
            )
        else:
            thought = (
                f"VISUAL_OBSERVATION: Checking for element {selector} on the current page. "
                f"The element is NOT found in the screenshot or DOM. "
                f"Expected: {value}. "
                f"{'This blocks the entire flow — cannot continue without this element.' if is_blocked else 'This is a defect.'}"
            )

        action_json = {
            "tool": "raise_bug_ticket",
            "args": {
                "title": bug_title,
                "severity": bug_severity,
                "evidence": f"Expected: {value}. Selector: {selector}. "
                            + (f"Observed color: {observed_color}" if observed_color else "Element not found in DOM or screenshot."),
            }
        }
        final = f"Bug raised: {bug_title}."
        return (
            f"Thought: {thought}\n"
            f"Action: {json.dumps(action_json)}\n"
            f"Final Answer: {final}\n"
            f"{terminal}"
        )

    # ── verify_input_value ─────────────────────────────────────────
    if action == "verify_input_value":
        matching = next((d for d in dom if d["selector"] == selector), {})
        current_val = matching.get("value", matching.get("text", value))
        thought = (
            f"VISUAL_OBSERVATION: The screenshot shows the input field {selector} "
            f"containing \"{current_val}\". "
            f"DOM confirms value=\"{current_val}\". "
            f"Expected: \"{value}\". These match — step passes."
        )
        action_json = {"tool": "verify_input_value", "args": {"selector": selector, "expected": value}}
        final = f"Verified: field {selector} contains \"{value}\"."

    # ── verify_text_present ────────────────────────────────────────
    elif action == "verify_text_present":
        thought = (
            f"VISUAL_OBSERVATION: Scanning the screenshot for the text \"{value}\". "
            f"The text is visible in the current page content. Step passes."
        )
        action_json = {"tool": "verify_text_present", "args": {"text": value}}
        final = f"Verified: text \"{value}\" is present on the page."

    # ── verify_element_visible ─────────────────────────────────────
    elif action == "verify_element_visible":
        thought = (
            f"VISUAL_OBSERVATION: Element {selector} is rendered within the viewport. "
            f"Bounding box is non-zero and element is not hidden by CSS. Step passes."
        )
        action_json = {"tool": "verify_element_visible", "args": {"selector": selector}}
        final = f"Verified: element {selector} is visible."

    # ── verify_element_hidden ──────────────────────────────────────
    elif action == "verify_element_hidden":
        thought = (
            f"VISUAL_OBSERVATION: Checking for element {selector} in the screenshot. "
            f"The element is NOT visible in the current viewport — it is either absent from the "
            f"DOM or hidden via CSS. This is the expected state. Step passes."
        )
        action_json = {"tool": "verify_element_visible", "args": {"selector": selector, "expected_visible": False}}
        final = f"Verified: element {selector} is correctly NOT visible."

    # ── verify_url_contains ────────────────────────────────────────
    elif action == "verify_url_contains":
        thought = (
            f"VISUAL_OBSERVATION: The browser URL bar shows a path containing \"{value}\". "
            f"Navigation succeeded as expected. Step passes."
        )
        action_json = {"tool": "verify_url_contains", "args": {"substring": value}}
        final = f"Verified: URL contains \"{value}\"."

    # ── verify_page_title ──────────────────────────────────────────
    elif action == "verify_page_title":
        thought = (
            f"VISUAL_OBSERVATION: The browser tab title shows \"{value}\". "
            f"Page title matches the expected value. Step passes."
        )
        action_json = {"tool": "verify_page_title", "args": {"expected": value}}
        final = f"Verified: page title is \"{value}\"."

    # ── verify_color_pass ──────────────────────────────────────────
    elif action == "verify_color_pass":
        thought = (
            f"VISUAL_OBSERVATION: Examining element {selector} in the screenshot. "
            f"The element visually appears to be {value} in color. "
            f"This matches the expected color specification {expected_color}. Step passes."
        )
        action_json = {"tool": "mark_step_pass", "args": {
            "message": f"Color verified: {selector} is {value} ({expected_color}) — matches spec."
        }}
        final = f"Color check passed: {selector} is correctly {value} ({expected_color})."

    # ── wait_for_url_change ────────────────────────────────────────
    elif action == "wait_for_url_change":
        thought = (
            f"VISUAL_OBSERVATION: The URL has changed. "
            f"It now contains \"{value}\" as expected after the navigation action. Step passes."
        )
        action_json = {"tool": "verify_url_contains", "args": {"substring": value}}
        final = f"URL change verified: URL now contains \"{value}\"."

    # ── mark_step_pass ─────────────────────────────────────────────
    elif action == "mark_step_pass":
        thought = (
            f"VISUAL_OBSERVATION: The previous action completed successfully. "
            f"Screenshot confirms the expected UI state is present. Marking step as passed."
        )
        action_json = {"tool": "mark_step_pass", "args": {"message": value or "Step completed successfully."}}
        final = value or "Step passed."

    # ── fallback ───────────────────────────────────────────────────
    else:
        thought = f"Verifying {action} on {selector} with expected \"{value}\"."
        action_json = {"tool": action, "args": {"selector": selector, "expected": value}}
        final = "Verification complete."

    return (
        f"Thought: {thought}\n"
        f"Action: {json.dumps(action_json)}\n"
        f"Final Answer: {final}\n"
        "[GOAL ACHIEVED]"
    )


# ─────────────────────────────────────────────────────────────
# CORE: RECORD BUILDER
# ─────────────────────────────────────────────────────────────

def build_record(screenshot_path: str, dom: list, task: str,
                 assistant_response: str, prev_action: dict = None,
                 prev_result: str = "success") -> dict:
    """Assemble one complete JSONL training record."""
    
    observations = "None"
    if prev_action:
        observations = (
            f"Previous Thought: {prev_action.get('thought', '')}\n"
            f"Previous Action: {json.dumps(prev_action.get('action_json', {}))}\n"
            f"Tool Result: {prev_result}"
        )

    dom_str = json.dumps(dom)
    context = f"<CONTEXT_BLOCK>\n[DOM]:\n{dom_str}\n[OBSERVATIONS]:\n{observations}\n</CONTEXT_BLOCK>\n\n{task}"

    return {
        "messages": [
            {
                "role": "system",
                "content": [{"type": "text", "text": SYSTEM_PROMPT}]
            },
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": screenshot_path},
                    {"type": "text", "text": context}
                ]
            },
            {
                "role": "assistant",
                "content": [{"type": "text", "text": assistant_response}]
            }
        ]
    }


# ─────────────────────────────────────────────────────────────
# CORE: FLOW EXECUTOR
# ─────────────────────────────────────────────────────────────

async def execute_flow(page: Page, flow: dict, writer) -> int:
    """
    Execute a complete flow against a live page.
    After each step: capture screenshot + DOM → build record → write to JSONL.
    Returns number of records written.
    """
    flow_name = flow["name"]
    steps = flow["steps"]
    records_written = 0
    prev_action_ctx = None

    print(f"\n{'='*60}")
    print(f"▶ Flow: {flow_name} ({len(steps)} steps)")
    print(f"{'='*60}")

    for i, step in enumerate(steps):
        step_id = f"{flow_name}_step{i+1}_{int(time.time())}"
        action = step["action"]
        selector = step.get("selector", "")
        value = step.get("value", "")
        task = step["task"]
        is_verify = step.get("is_verify", False)

        print(f"  Step {i+1}/{len(steps)}: {action} | {selector} | '{value}'")

        # ── Execute the action on the real page ──────────────────
        try:
            if action in ("type", "clear_and_type"):
                await page.fill(selector, "")
                await page.fill(selector, value)
                await page.wait_for_timeout(300)

            elif action == "click":
                await page.click(selector)
                await page.wait_for_timeout(600)

            elif action == "double_click":
                await page.dbl_click(selector)
                await page.wait_for_timeout(400)

            elif action == "select_option":
                await page.select_option(selector, label=value)
                await page.wait_for_timeout(300)

            elif action == "navigate":
                await page.goto(value, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(800)

            elif action == "go_back":
                await page.go_back(wait_until="domcontentloaded")
                await page.wait_for_timeout(600)

            elif action == "scroll_down":
                await page.evaluate("window.scrollBy(0, 300)")
                await page.wait_for_timeout(300)

            elif action == "scroll_to_element":
                try:
                    await page.locator(selector).scroll_into_view_if_needed(timeout=5000)
                except Exception:
                    await page.evaluate(f"document.querySelector('{selector}') && document.querySelector('{selector}').scrollIntoView()")
                await page.wait_for_timeout(300)

            elif action == "scroll_to_top":
                await page.evaluate("window.scrollTo(0, 0)")
                await page.wait_for_timeout(300)

            elif action == "scroll_to_bottom":
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(300)

            elif action == "hover":
                await page.hover(selector)
                await page.wait_for_timeout(400)

            elif action == "press_key":
                await page.keyboard.press(value)
                await page.wait_for_timeout(300)

            elif action == "wait_for_element":
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                except Exception:
                    pass  # Still capture state — negative example
                await page.wait_for_timeout(200)

            elif action == "wait_for_url_change":
                await page.wait_for_timeout(500)  # real wait happens in browser action above

            elif action == "get_current_url":
                await page.wait_for_timeout(200)

            elif action in ("verify_input_value", "verify_text_present",
                            "verify_element_visible", "verify_element_hidden",
                            "verify_url_contains", "verify_page_title",
                            "verify_color_pass", "verify_color_fail",
                            "mark_step_pass", "raise_bug_ticket",
                            "raises_bug"):
                await page.wait_for_timeout(200)

            else:
                print(f"    ⚠ Unknown action '{action}', skipping browser interaction")

        except Exception as e:
            print(f"    ✗ Browser action failed: {e}")

        # ── Capture state AFTER action ────────────────────────────
        screenshot_path = await take_screenshot_b64(page, step_id)
        dom = await extract_relevant_dom(page, selector if selector else None)

        # ── Build assistant response ──────────────────────────────
        if is_verify or step.get("raises_bug", False):
            response = build_verify_response(step, dom, prev_action_ctx)
        else:
            response = build_action_response(step, dom, prev_action_ctx)

        # ── Build and write JSONL record ──────────────────────────
        record = build_record(
            screenshot_path=screenshot_path,
            dom=dom,
            task=task,
            assistant_response=response,
            prev_action=prev_action_ctx,
            prev_result="success"
        )
        writer.write(json.dumps(record) + "\n")
        records_written += 1

        # ── Update context for next step ──────────────────────────
        thought_match = re.search(r"Thought: (.+?)\nAction:", response, re.DOTALL)
        action_json_str = extract_json_object(response, "Action: ")
        prev_action_ctx = {
            "thought": thought_match.group(1).strip() if thought_match else "",
            "action_json": json.loads(action_json_str) if action_json_str else {}
        }

        print(f"    ✓ Record written → {screenshot_path}")

    return records_written


# ─────────────────────────────────────────────────────────────
# FLOWS — imported from aegis_flows.py
# Run: python3 aegis_flows.py  to see the full record count breakdown
# ─────────────────────────────────────────────────────────────

from aegis_flows import ALL_FLOWS as FLOWS


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

async def main():
    print(f"\n🚀 AEGIS Dataset Generator")
    print(f"   Output: {OUTPUT_FILE}")
    print(f"   Flows:  {len(FLOWS)}")

    total_records = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        # Block ads/trackers for cleaner screenshots
        await page.route("**/*.{png,jpg,gif,svg,woff,woff2}", 
                        lambda route: route.abort() if "ad" in route.request.url else route.continue_())

        with open(OUTPUT_FILE, "w") as f:
            for flow in FLOWS:
                try:
                    count = await execute_flow(page, flow, f)
                    total_records += count
                    print(f"  → {count} records written for '{flow['name']}'")
                except Exception as e:
                    print(f"  ✗ Flow '{flow['name']}' failed: {e}")
                    continue

        await browser.close()

    print(f"\n{'='*60}")
    print(f"✅ Done! {total_records} training records written to {OUTPUT_FILE}")
    print(f"   Screenshots saved to: {SCREENSHOT_DIR}/")
    print(f"\nNext steps:")
    print(f"  1. Inspect a few records: head -n 3 {OUTPUT_FILE} | python3 -m json.tool")
    print(f"  2. Validate all records:  python3 validate_dataset.py {OUTPUT_FILE}")
    print(f"  3. Merge with existing:   cat aegis_final_perfect.jsonl {OUTPUT_FILE} > aegis_merged.jsonl")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())