#!/usr/bin/env python3
"""
build_records.py
================
Reads raw captures from ./aegis_captures/<scenario_id>/
Converts paired before/after captures into training JSONL records.

Each training record:
  messages[0] = system prompt (tools list)
  messages[1] = user: step_desc + DOM (+ image path reference)
  messages[2] = assistant: VISUAL_OBSERVATION + DOM_CONFIRMATION + Thought + Action + OUTCOME

Usage:
  python build_records.py --scenario S01
  python build_records.py --all
  python build_records.py --validate
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict

CAPTURE_DIR = Path("./aegis_captures")
OUTPUT_DIR  = Path("./aegis_dataset")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── SYSTEM PROMPT ─────────────────────────────────────────────────────────────
SYSTEM = """You are Aegis, a UAT execution agent. You receive a screenshot, a DOM snapshot, and one atomic step to execute.

TOOLS:
click, clear_and_type, verify_input_value, verify_text_present, verify_text_absent,
verify_element_visible, verify_element_enabled, verify_url_contains, verify_color,
verify_text_color, get_text, get_char_count, verify_char_limit, type_n_chars,
select_option, scroll_down, scroll_up, scroll_to_element, scroll_to_top, scroll_to_bottom,
wait_for_element, wait_for_text, wait_for_url_change, wait_for_network_idle, wait,
open_url, press_key, hover, double_click, right_click,
check_email_received, verify_email_content, verify_email_sender, get_email_link, verify_no_email,
mark_step_pass, mark_step_fail, raise_bug_ticket, mark_flow_blocked, capture_evidence

RESPONSE FORMAT (always in this exact order):
VISUAL_OBSERVATION: [What you see in the screenshot — be specific about text, colors, positions]
DOM_CONFIRMATION: [Which selector you will use and confirm it exists in DOM, OR state DOM is empty for color tasks]
Thought: [Your reasoning for the chosen action]
Action: {"tool": "...", "args": {...}}
OUTCOME_PREDICTION: [What the result will be]

RULES:
1. Always describe screenshot BEFORE acting
2. Only use selectors that appear in the provided DOM — never invent selectors
3. For table actions: use row_context from DOM to scope selectors, confirm visually
4. For color checks: DOM is empty — use verify_color with computed style
5. One Action per response only
6. [GOAL ACHIEVED] only after explicit visual confirmation of complete success"""

# ── ACTION TEMPLATES — generated based on capture metadata ───────────────────
def infer_action(capture, dom):
    """
    Given capture metadata and DOM, generate a plausible Action JSON.
    This is a TEMPLATE — human annotator reviews and edits in build phase.
    """
    desc   = capture.get("step_desc", "").lower()
    state  = capture.get("capture_state", "normal")
    family = capture.get("family", "")

    # Find relevant DOM elements
    inputs    = [d for d in dom if d.get("tag") in ("input", "textarea") and not d.get("_meta")]
    buttons   = [d for d in dom if d.get("tag") in ("button", "a") and not d.get("_meta")]
    selects   = [d for d in dom if d.get("tag") == "select" and not d.get("_meta")]
    in_vp_els = [d for d in dom if d.get("in_viewport") and not d.get("_meta")]

    # Infer tool from step description keywords
    if any(w in desc for w in ["type", "enter", "fill", "input"]):
        target = next((i for i in inputs if i.get("in_viewport")), inputs[0] if inputs else None)
        if target:
            value = ""
            # Extract quoted value from description
            import re
            m = re.search(r"['\"]([^'\"]+)['\"]", capture.get("step_desc", ""))
            if m:
                value = m.group(1)
            return {"tool": "clear_and_type", "args": {"selector": target["selector"], "text": value}}

    if any(w in desc for w in ["click", "press", "submit"]):
        target = next((b for b in buttons if any(w in b.get("text","").lower() for w in ["submit","save","login","click","add","delete","confirm"])), None)
        if not target:
            target = buttons[0] if buttons else None
        if target:
            return {"tool": "click", "args": {"selector": target["selector"]}}

    if any(w in desc for w in ["verify", "check", "confirm", "assert"]):
        if "url" in desc:
            return {"tool": "verify_url_contains", "args": {"substring": "FILL_IN"}}
        if "text" in desc or "visible" in desc or "present" in desc:
            import re
            m = re.search(r"['\"]([^'\"]+)['\"]", capture.get("step_desc", ""))
            text = m.group(1) if m else "FILL_IN"
            return {"tool": "verify_text_present", "args": {"text": text}}
        if "color" in desc:
            return {"tool": "verify_color", "args": {"selector": "FILL_IN", "expected_color": "#FILL_IN", "tolerance": 20}}
        if "value" in desc:
            target = inputs[0] if inputs else None
            sel = target["selector"] if target else "FILL_IN"
            return {"tool": "verify_input_value", "args": {"selector": sel, "expected_value": "FILL_IN"}}
        target = in_vp_els[0] if in_vp_els else None
        sel = target["selector"] if target else "FILL_IN"
        return {"tool": "verify_element_visible", "args": {"selector": sel}}

    if "scroll" in desc:
        if "element" in desc or "button" in desc:
            target = buttons[-1] if buttons else None
            sel = target["selector"] if target else "FILL_IN"
            return {"tool": "scroll_to_element", "args": {"selector": sel}}
        return {"tool": "scroll_down", "args": {"pixels": 300}}

    if "wait" in desc:
        return {"tool": "wait_for_element", "args": {"selector": "FILL_IN", "timeout_sec": 10}}

    if any(w in desc for w in ["select", "choose", "dropdown", "option"]):
        target = selects[0] if selects else None
        sel = target["selector"] if target else "FILL_IN"
        return {"tool": "select_option", "args": {"selector": sel, "value": "FILL_IN"}}

    if state == "fail":
        return {"tool": "raise_bug_ticket", "args": {
            "title": capture.get("step_desc", "FILL_IN"),
            "expected": "FILL_IN",
            "actual": capture.get("fail_reason", "FILL_IN"),
            "severity": "medium"
        }}

    if state == "goal_achieved":
        return {"tool": "mark_step_pass", "args": {
            "step_id": capture["id"],
            "evidence": capture.get("goal_evidence", "FILL_IN")
        }}

    if state == "flow_blocked":
        return {"tool": "mark_flow_blocked", "args": {
            "reason": capture.get("blocked_reason", "FILL_IN"),
        }}

    return {"tool": "FILL_IN", "args": {}}


def build_response(capture, dom):
    """Build the assistant response template from capture metadata."""
    state    = capture.get("capture_state", "normal")
    step_desc = capture.get("step_desc", "")
    url      = capture.get("url", "")
    dom_clean = [d for d in dom if not d.get("_meta")]

    # VISUAL_OBSERVATION
    if state == "before_action":
        vis_obs = f"[DESCRIBE WHAT YOU SEE IN THE SCREENSHOT BEFORE THIS ACTION — be specific about visible elements, text, colors, positions at {url}]"
    elif state == "after_action":
        vis_obs = f"[DESCRIBE THE STATE OF THE PAGE AFTER THE ACTION — what changed, what is now visible, any new elements]"
    elif state == "fail":
        vis_obs = f"[DESCRIBE THE FAILURE STATE — what is visible on screen that indicates the expected outcome did not occur]"
    elif state == "goal_achieved":
        evidence = capture.get("goal_evidence", "")
        vis_obs = f"[DESCRIBE COMPLETE SUCCESS STATE VISIBLE IN SCREENSHOT] — {evidence}"
    else:
        vis_obs = f"[DESCRIBE WHAT YOU SEE IN THE SCREENSHOT — elements, text, colors, layout at {url}]"

    # DOM_CONFIRMATION
    in_vp = [d for d in dom_clean if d.get("in_viewport")]
    action = infer_action(capture, dom_clean)

    if action.get("tool") in ("verify_color", "verify_text_color"):
        dom_conf = "This is a color verification task — DOM is intentionally empty. Using verify_color with computed CSS style."
    elif action.get("tool") == "FILL_IN":
        dom_conf = "[CONFIRM WHICH SELECTOR FROM DOM YOU WILL USE AND WHY]"
    else:
        sel = action.get("args", {}).get("selector", "FILL_IN")
        # Check if selector exists in DOM
        matching = [d for d in dom_clean if d.get("selector") == sel or sel in d.get("selector","")]
        if matching and matching[0].get("row_context"):
            dom_conf = f"DOM contains {sel} with row_context='{matching[0]['row_context']}' — visually confirmed this is the correct row."
        elif matching:
            dom_conf = f"DOM contains {sel} — in_viewport={matching[0].get('in_viewport', False)}, confirmed present."
        else:
            dom_conf = f"[CONFIRM SELECTOR {sel} IS IN DOM OR EXPLAIN ALTERNATIVE]"

    # Thought
    if state == "fail":
        thought = f"Expected outcome not visible in screenshot. {capture.get('fail_reason', 'Test step failed.')} I will raise a bug ticket."
    elif state == "goal_achieved":
        thought = "All expected outcomes are visually confirmed in the screenshot. The flow is complete."
    elif state == "flow_blocked":
        thought = f"The flow cannot continue. {capture.get('blocked_reason', 'Unrecoverable state.')} Marking flow as blocked."
    else:
        thought = f"[YOUR REASONING FOR CHOOSING THIS TOOL AND SELECTOR TO ACCOMPLISH: {step_desc}]"

    # Build full response
    action_str = json.dumps(action, ensure_ascii=False)

    if state == "goal_achieved":
        outcome = f"PASS — {capture.get('goal_evidence', 'Flow completed successfully.')}"
        goal_line = f"\n[GOAL ACHIEVED] Visual confirmation: {capture.get('goal_evidence', '[describe success]')}. Flow complete."
    elif state == "fail":
        outcome = f"FAIL — {capture.get('fail_reason', 'Expected outcome not present.')}"
        goal_line = ""
    elif state == "flow_blocked":
        outcome = f"FLOW_BLOCKED — {capture.get('blocked_reason', 'Cannot proceed.')}"
        goal_line = ""
    else:
        outcome = "[WHAT WILL THE RESULT BE AFTER THIS ACTION]"
        goal_line = ""

    return f"""VISUAL_OBSERVATION: {vis_obs}
DOM_CONFIRMATION: {dom_conf}
Thought: {thought}
Action: {action_str}
OUTCOME_PREDICTION: {outcome}{goal_line}"""


def build_user_content(capture, dom):
    """Build the user message: step description + DOM list."""
    dom_clean = [d for d in dom if not d.get("_meta")]
    dom_str   = json.dumps(dom_clean, ensure_ascii=False, separators=(",", ":"))
    prev      = capture.get("prev_result")
    prev_line = f"\nPREVIOUS_RESULT: {prev}" if prev else ""
    return f"[DOM]: {dom_str}\nSTEP: {capture['step_desc']}{prev_line}"


def load_captures(scenario_dir):
    """Load all captures from a scenario directory, sorted by ID."""
    caps = []
    for json_file in sorted(scenario_dir.glob("*.json")):
        if "summary" in json_file.name:
            continue
        with open(json_file) as f:
            data = json.load(f)
        # Skip meta-only files
        if not data.get("step_desc"):
            continue
        caps.append(data)
    return caps


def pair_captures(captures):
    """
    Pair before/after captures within the same workflow.
    A before+after pair = 1 training record where:
      - user message uses BEFORE state dom + step_desc
      - assistant response is for the AFTER state (action taken)
    Single captures (state=normal) are standalone records.
    """
    records = []
    i = 0
    while i < len(captures):
        cap = captures[i]

        if cap["capture_state"] == "before_action" and i + 1 < len(captures):
            next_cap = captures[i + 1]
            if next_cap["capture_state"] == "after_action" and next_cap["workflow"] == cap["workflow"]:
                # Pair: user=before context, assistant=after action
                record = {
                    "capture_id":       cap["id"],
                    "after_capture_id": next_cap["id"],
                    "user_capture":     cap,
                    "action_capture":   next_cap,
                    "paired":           True,
                }
                records.append(record)
                i += 2
                continue

        # Standalone capture
        records.append({
            "capture_id":   cap["id"],
            "user_capture": cap,
            "action_capture": cap,
            "paired":       False,
        })
        i += 1

    return records


def build_training_record(pair_info):
    """Convert a paired or standalone capture into a training record."""
    user_cap   = pair_info["user_capture"]
    action_cap = pair_info["action_capture"]

    dom = user_cap.get("dom", [])

    user_content = build_user_content(user_cap, dom)
    asst_content = build_response(action_cap, dom)

    return {
        "messages": [
            {"role": "system",    "content": SYSTEM},
            {"role": "user",      "content": user_content,
             "_image": user_cap.get("screenshot"),
             "_image_dir": str(CAPTURE_DIR / user_cap["scenario_id"])},
            {"role": "assistant", "content": asst_content},
        ],
        "_meta": {
            "capture_id":    pair_info["capture_id"],
            "scenario_id":   user_cap["scenario_id"],
            "family":        user_cap["family"],
            "capture_state": action_cap["capture_state"],
            "workflow":      user_cap["workflow"],
            "paired":        pair_info["paired"],
            "needs_review":  "FILL_IN" in asst_content,
        }
    }


def validate_record(record):
    """Check record structure for common issues."""
    errors = []
    msgs = record["messages"]

    if len(msgs) != 3:
        errors.append("Must have exactly 3 messages")
        return errors

    asst = msgs[2]["content"]

    required_sections = ["VISUAL_OBSERVATION:", "DOM_CONFIRMATION:", "Thought:", "Action:", "OUTCOME_PREDICTION:"]
    for section in required_sections:
        if section not in asst:
            errors.append(f"Missing section: {section}")

    # Check Action is valid JSON
    import re
    m = re.search(r'Action:\s*(\{.*?\})', asst, re.DOTALL)
    if m:
        try:
            action = json.loads(m.group(1))
            if action.get("tool") == "FILL_IN":
                errors.append("Action tool is FILL_IN — needs human review")
        except json.JSONDecodeError as e:
            errors.append(f"Action is not valid JSON: {e}")
    else:
        errors.append("No Action JSON found")

    if "FILL_IN" in asst:
        errors.append("WARNING: Contains FILL_IN placeholders — needs human review")

    return errors


# ── MAIN ──────────────────────────────────────────────────────────────────────
def process_scenario(scenario_id):
    scen_dir = CAPTURE_DIR / scenario_id
    if not scen_dir.exists():
        print(f"  No captures found for {scenario_id}")
        return [], []

    captures = load_captures(scen_dir)
    if not captures:
        print(f"  No captures in {scen_dir}")
        return [], []

    pairs   = pair_captures(captures)
    records = [build_training_record(p) for p in pairs]

    errors_found = []
    for r in records:
        errs = validate_record(r)
        if errs:
            errors_found.append((r["_meta"]["capture_id"], errs))

    print(f"\n  {scenario_id}: {len(captures)} captures → {len(records)} records")
    needs_review = sum(1 for r in records if r["_meta"]["needs_review"])
    if needs_review:
        print(f"    ⚠️  {needs_review} records need human review (FILL_IN placeholders)")
    if errors_found:
        print(f"    ❌ {len(errors_found)} validation errors")
        for cap_id, errs in errors_found[:3]:
            print(f"       {cap_id}: {errs}")

    return records, errors_found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", help="Process single scenario e.g. S01")
    parser.add_argument("--all",      action="store_true", help="Process all scenarios")
    parser.add_argument("--validate", action="store_true", help="Validate existing JSONL files")
    args = parser.parse_args()

    all_records   = []
    all_errors    = []

    if args.scenario:
        records, errors = process_scenario(args.scenario.upper())
        all_records.extend(records)
        all_errors.extend(errors)

    elif args.all or args.validate:
        for scen_dir in sorted(CAPTURE_DIR.iterdir()):
            if scen_dir.is_dir() and scen_dir.name.startswith("S"):
                records, errors = process_scenario(scen_dir.name)
                all_records.extend(records)
                all_errors.extend(errors)

    if not all_records:
        print("\n  No records to write. Run collect.py first.")
        return

    # Split by family for analysis
    from collections import Counter
    families = Counter(r["_meta"]["family"] for r in all_records)

    # Write JSONL (strip _image and _meta for training)
    out_path = OUTPUT_DIR / "executor_dataset.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for r in all_records:
            clean = {
                "messages": [
                    {k: v for k, v in m.items() if not k.startswith("_")}
                    for m in r["messages"]
                ]
            }
            f.write(json.dumps(clean, ensure_ascii=False) + "\n")

    # Write with meta (for review tool)
    meta_path = OUTPUT_DIR / "executor_dataset_with_meta.jsonl"
    with open(meta_path, "w", encoding="utf-8") as f:
        for r in all_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\n{'='*50}")
    print(f"  TOTAL RECORDS: {len(all_records)}")
    print(f"  Needs review:  {sum(1 for r in all_records if r['_meta']['needs_review'])}")
    print(f"  Validation errors: {len(all_errors)}")
    print(f"\n  By family:")
    for fam, count in sorted(families.items(), key=lambda x: -x[1]):
        print(f"    {fam:<28}: {count}")
    print(f"\n  Output: {out_path}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
