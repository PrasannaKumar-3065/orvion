"""
inference_helpers.py  (v4)
──────────────────────────
Shared DOM pipeline used by agent_worker (live app) and the stress-tester
notebook. Everything is module-level so it can be imported without
instantiating any class.

Public API
──────────
  DOM_JS               JS injected into QWebEngineView / Playwright
  SYSTEM_PROMPT        Verbatim match to training data
  score_and_select     Cosine / TF-IDF scoring with v4 multipliers
  format_dom_for_model Compact JSON string for the prompt
  build_prompt         Message list for local Qwen2.5-VL inference
  build_space_prompt   Plain-text prompt for the HF Space API
  parse_output         Thought / Action / Answer extractor + index clamping
"""

import json
import re
from typing import Any, Dict, List, Optional

# ─────────────────────────────────────────────────────────────────────────────
# DOM_JS  (v4 — viewport-capped, shadow-DOM-piercing)
# ─────────────────────────────────────────────────────────────────────────────

DOM_JS = r"""
() => {
    const VH    = window.innerHeight;
    const MAX_Y = VH * 4;

    function visible(el) {
        const r = el.getBoundingClientRect();
        return r.width > 0 && r.height > 0 && el.offsetParent !== null;
    }
    function inRange(el) { return el.getBoundingClientRect().top < MAX_Y; }
    function box(el) {
        const r = el.getBoundingClientRect();
        return { cx: Math.round(r.left + r.width/2),
                 cy: Math.round(r.top  + r.height/2),
                 w:  Math.round(r.width), h: Math.round(r.height) };
    }
    function elText(el) {
        return (el.innerText || el.value || el.placeholder ||
                el.getAttribute('aria-label') || el.getAttribute('name') ||
                el.getAttribute('title') || el.getAttribute('alt') ||
                el.getAttribute('autocomplete') || ''
               ).slice(0,80).trim().replace(/\s+/g,' ');
    }
    function iconInfo(el) {
        return { cls:   Array.from(el.classList).join(' ').slice(0,60),
                 title: (el.getAttribute('title')||el.getAttribute('aria-label')||'').trim() };
    }
    function rowBodyText(tr) {
        return Array.from(tr.querySelectorAll('td')).map(td => {
            const c = td.cloneNode(true);
            c.querySelectorAll('button,a,input,select').forEach(n=>n.remove());
            return c.innerText.replace(/\s+/g,' ').trim();
        }).filter(Boolean).join(' | ');
    }
    function rowIndex(tr) {
        const tb = tr.closest('tbody');
        return tb ? Array.from(tb.querySelectorAll('tr')).indexOf(tr)+1 : '?';
    }
    function collectFromRoot(root, pool, seen) {
        const SELS = ['input','button','a','select','textarea',
                      '[role="button"]','[onclick]','[role="link"]'];
        SELS.forEach(sel => {
            let els; try { els = root.querySelectorAll(sel); } catch(e){return;}
            els.forEach(el => {
                if (seen.has(el) || !visible(el) || !inRange(el)) return;
                if (el.closest('tr')) return;
                seen.add(el);
                pool.push({ kind:'interactive', tag:el.tagName.toLowerCase(),
                            text:elText(el), type:el.getAttribute('type')||'',
                            value:(el.value||'').slice(0,40), box:box(el),
                            id:   (el.id||'').trim(),
                            name: (el.getAttribute('name')||'').trim(),
                            cls:  Array.from(el.classList).join(' ').trim() });
            });
        });
        root.querySelectorAll('*').forEach(el => {
            if (el.shadowRoot) collectFromRoot(el.shadowRoot, pool, seen);
        });
    }
    const pool = [], seen = new Set();
    collectFromRoot(document, pool, seen);
    document.querySelectorAll('tbody tr').forEach(tr => {
        if (!visible(tr) || !inRange(tr)) return;
        const body = rowBodyText(tr), rIdx = rowIndex(tr);
        if (!body) return;
        const actions = Array.from(
            tr.querySelectorAll('button,a,[role="button"],[onclick],svg,i[class],span[class]')
        ).filter(el => visible(el) && !seen.has(el));
        if (actions.length === 0) {
            pool.push({ kind:'table-row', tag:'tr', text:`row-${rIdx}: ${body}`,
                        type:'', value:'', box:box(tr) });
        } else {
            actions.forEach(aEl => {
                seen.add(aEl);
                const {cls,title}=iconInfo(aEl), aText=elText(aEl);
                const parts=[`row-${rIdx}: ${body}`];
                if(aText) parts.push(`then ${aText}`);
                if(cls)   parts.push(`[${cls}]`);
                if(title) parts.push(`(${title})`);
                pool.push({ kind:'table-action', tag:aEl.tagName.toLowerCase(),
                            text:parts.join(' '), type:aEl.getAttribute('type')||'',
                            value:'', box:box(aEl) });
            });
        }
    });
    return pool;
}
"""

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT  (verbatim match to training data)
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are Aegis — a browser QA agent. "
    "You see a screenshot and a 5-element DOM list (0-indexed).\n"
    "Selectors are hidden — interact only by index.\n"
    "\n"
    'Tools: click(idx) | type(idx,"text") | scroll("down"|"up",px) | select(idx,"value") '
    '| upload_file(idx,"path") | bug_report("reason") | search_emails("query")\n'
    "Long text: type(idx,##300##) for ~300 chars, ##3000## for ~3000 chars.\n"
    "\n"
    "Format:\n"
    "  Thought: <visual observation + DOM match + confidence>\n"
    "  Action: <one tool call>\n"
    "-- or for visual checks --\n"
    "  Thought: <what you see>\n"
    "  Answer: <observation>\n"
    "-- or for missing elements --\n"
    "  Thought: <element absent>\n"
    '  Action: bug_report("reason")\n'
    '  Answer: Bug filed -- <summary>'
)

# ─────────────────────────────────────────────────────────────────────────────
# Scoring constants & regexes
# ─────────────────────────────────────────────────────────────────────────────

VIEWPORT_H   = 800

_USERNAME_RE = re.compile(r'\b(username|user name|email|login|sign.?in)\b', re.I)
_PASSWORD_RE = re.compile(r'\bpassword\b', re.I)
_TYPING_RE   = re.compile(r'\b(type|fill|enter|write|input|search)\b', re.I)

_TYPE_LABELS: Dict[str, str] = {
    "password": "password-field",
    "email":    "email-field",
    "tel":      "phone-number-field",
    "search":   "search-field",
    "number":   "number-input-field",
    "checkbox": "checkbox",
    "radio":    "radio-button",
    "submit":   "submit-button",
    "file":     "file-upload-button",
}

_ACTION_RE = re.compile(
    r'Action:\s*(?P<tool>click|type|scroll|select|upload_file|bug_report|search_emails)'
    r'\((?P<args>[^)]*)\)',
    re.IGNORECASE,
)
_ANSWER_RE  = re.compile(r'Answer:\s*(.+)', re.DOTALL)
_THOUGHT_RE = re.compile(r'Thought:\s*(.+?)(?=\nAction:|\nAnswer:|$)', re.DOTALL)

# ─────────────────────────────────────────────────────────────────────────────
# Lazy scorer — sentence-transformers or TF-IDF fallback
# sentence-transformers needs PyTorch; the API build falls back to TF-IDF.
# ─────────────────────────────────────────────────────────────────────────────

_SCORER = None


def _get_scorer():
    global _SCORER
    if _SCORER is None:
        try:
            from sentence_transformers import SentenceTransformer
            _SCORER = SentenceTransformer("all-MiniLM-L6-v2")
        except ImportError:
            _SCORER = "tfidf"
    return _SCORER


def warmup_scorer():
    """
    Force the sentence-transformer to load immediately.
    Call once at worker startup so the model is ready before the first query.
    Returns the scorer so callers can log what was loaded.
    """
    scorer = _get_scorer()
    return "sentence-transformers" if scorer != "tfidf" else "tfidf"


def _tfidf_score(task: str, sentence: str) -> float:
    def tok(s): return set(re.findall(r'\w+', s.lower()))
    t, s = tok(task), tok(sentence)
    return len(t & s) / len(t | s) if (t and s) else 0.0


def _build_sentence(raw: Dict[str, Any]) -> str:
    kind   = raw.get("kind", "interactive")
    tag    = raw.get("tag", "?")
    text   = raw.get("text", "").strip()
    typ    = raw.get("type", "")
    val    = raw.get("value", "")
    b      = raw.get("box", {})
    cx, cy = b.get("cx", 0), b.get("cy", 0)
    w,  h  = b.get("w", 0), b.get("h", 0)

    if kind in ("table-row", "table-action"):
        return f'{kind}: {text} at ({cx},{cy})'

    type_label   = _TYPE_LABELS.get(typ, "")
    display_text = text or val or type_label

    parts = [tag + (f'[type={typ}]' if typ else '')]
    if display_text:
        parts.append(f'"{display_text}"')
    parts.append(f'at ({cx},{cy}) size {w}x{h}')
    return ' '.join(parts)


def _to_model_element(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Strip scoring metadata — only send fields the model was trained on."""
    return {
        "tag":   raw.get("tag",   ""),
        "text":  raw.get("text",  ""),
        "type":  raw.get("type",  ""),
        "value": raw.get("value", ""),
        "box":   raw.get("box",   {"cx": 0, "cy": 0, "w": 0, "h": 0}),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def score_and_select(
    raw_elements: List[Dict[str, Any]],
    task: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Score raw DOM elements against the task, apply v4 multipliers, return top-k.

    Multipliers:
      x1.20  element cy is within the rendered viewport
      x0.60  submit button when task requires text input
      x1.15 / x0.85  text-vs-password bias for username / password tasks
    """
    if not raw_elements:
        return []

    sentences = [_build_sentence(el) for el in raw_elements]
    scorer    = _get_scorer()

    if scorer == "tfidf":
        scores = [_tfidf_score(task, s) for s in sentences]
    else:
        from sentence_transformers import util as stu
        t_emb  = scorer.encode(task,      convert_to_tensor=True, show_progress_bar=False)
        s_emb  = scorer.encode(sentences, convert_to_tensor=True, show_progress_bar=False)
        scores = stu.cos_sim(t_emb, s_emb)[0].cpu().tolist()

    want_user   = bool(_USERNAME_RE.search(task))
    want_pass   = bool(_PASSWORD_RE.search(task))
    want_typing = bool(_TYPING_RE.search(task))

    for i, el in enumerate(raw_elements):
        cy  = el.get("box", {}).get("cy", 9999)
        typ = el.get("type", "")
        knd = el.get("kind", "interactive")
        m   = 1.0

        if knd == "interactive" and 0 <= cy <= VIEWPORT_H:
            m *= 1.20
        if want_typing and typ == "submit":
            m *= 0.60
        if knd == "interactive":
            if want_user and not want_pass:
                if typ == "text":     m *= 1.15
                if typ == "password": m *= 0.85
            elif want_pass and not want_user:
                if typ == "password": m *= 1.15
                if typ == "text":     m *= 0.85

        scores[i] = float(scores[i]) * m

    ranked = sorted(zip(scores, range(len(raw_elements))), key=lambda x: -x[0])

    out = []
    for rank, (score, oi) in enumerate(ranked[:top_k]):
        e              = dict(raw_elements[oi])
        e["_score"]    = round(float(score), 4)
        e["_sentence"] = sentences[oi]
        e["_rank"]     = rank
        out.append(e)
    return out


def format_dom_for_model(scored: List[Dict[str, Any]]) -> str:
    """Indented JSON string of top-k elements, stripped of scoring metadata."""
    return json.dumps([_to_model_element(e) for e in scored],
                      ensure_ascii=False, indent=2)


def build_prompt(
    task: str,
    scored: List[Dict[str, Any]],
    image_path: str,
) -> List[Dict[str, Any]]:
    """
    Message list for local Qwen2.5-VL inference via
    tokenizer.apply_chat_template().
    image_path is a local filesystem path accepted by qwen_vl_utils.
    """
    dom_json  = json.dumps([_to_model_element(e) for e in scored],
                           ensure_ascii=False, separators=(", ", ": "))
    user_text = f"DOM: [{dom_json}]\n\nTask: {task}"
    return [
        {"role": "system", "content": [{"type": "text", "text": SYSTEM_PROMPT}]},
        {"role": "user",   "content": [
            {"type": "image", "image": image_path},
            {"type": "text",  "text": user_text},
        ]},
    ]


def build_space_prompt(task: str, scored: List[Dict[str, Any]]) -> str:
    """
    Plain-text prompt for the HuggingFace Space API.
    The screenshot is sent separately as image_bytes; this is the text part only.
    """
    dom_json = json.dumps([_to_model_element(e) for e in scored],
                          ensure_ascii=False, separators=(", ", ": "))
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"DOM: [{dom_json}]\n\n"
        f"Task: {task}"
    )


def parse_output(raw: str, pool_size: int = 5) -> tuple:
    """
    Parse a raw model response into structured fields.

    Returns
    -------
    (action_type, element_index, action_value, thought, answer)

    element_index is clamped to [0, pool_size-1] to handle hallucinated
    out-of-range indices (e.g. DOM[4] on a 4-element pool).
    """
    th_m = _THOUGHT_RE.search(raw)
    an_m = _ANSWER_RE.search(raw)
    am   = _ACTION_RE.search(raw)

    th = th_m.group(1).strip() if th_m else ""
    an = an_m.group(1).strip() if an_m else ""

    if not am:
        return ("answer" if an else ""), None, an, th, an

    tool     = am.group("tool").lower()
    args_str = am.group("args")

    m_idx = re.search(r'\b(\d+)\b', args_str)
    ei    = int(m_idx.group(1)) if m_idx else None
    m_val = re.search(r'"([^"]*)"', args_str)
    val   = m_val.group(1) if m_val else args_str.strip()

    if ei is not None and pool_size > 0 and ei >= pool_size:
        ei = pool_size - 1   # clamp hallucinated out-of-range indices

    return tool, ei, val, th, an