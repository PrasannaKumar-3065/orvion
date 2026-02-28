import re
import json
import math


DOM_JS = """
(function () {
    const TAGS = ['a','button','input','select','textarea',
                  'h1','h2','h3','p','span','div','form','label'];
    const vw = window.innerWidth, vh = window.innerHeight;
    const results = [];
    TAGS.forEach(tag => {
        document.querySelectorAll(tag).forEach(el => {
            const r = el.getBoundingClientRect();
            if (r.width === 0 && r.height === 0) return;
            const inVP = r.top < vh && r.bottom > 0 && r.left < vw && r.right > 0;
            const text = (el.innerText || el.value || el.placeholder || '').trim().slice(0, 120);
            const sel  = el.id ? '#' + el.id :
                         el.name ? '[name="' + el.name + '"]' :
                         el.className ? '.' + el.className.trim().split(/\\s+/)[0] : tag;
            results.push({
                tag:         tag,
                selector:    sel,
                text:        text,
                type:        el.type  || null,
                value:       el.value || null,
                in_viewport: inVP,
                vp_top:      r.top,
            });
        });
    });
    return JSON.stringify(results);
})();
"""


def _tokenize(text: str) -> list:
    return re.findall(r'[a-z0-9]+', text.lower())


def _bm25_score(query_tokens, doc_tokens, k1=1.5, b=0.75, avg_dl=8.0):
    if not doc_tokens:
        return 0.0
    dl   = len(doc_tokens)
    freq = {}
    for t in doc_tokens:
        freq[t] = freq.get(t, 0) + 1
    score = 0.0
    for qt in query_tokens:
        f = freq.get(qt, 0)
        if f == 0:
            continue
        idf = math.log(2.0)
        tf  = (f * (k1 + 1)) / (f + k1 * (1 - b + b * dl / avg_dl))
        score += idf * tf
    return score


def retrieve_dom_context(dom, goal, top_k=12, viewport_bonus=2.0):
    if not dom:
        return []
    query_tokens = _tokenize(goal)
    scored = []
    for el in dom:
        doc_text = " ".join(filter(None, [
            el.get("text", ""), el.get("tag", ""),
            el.get("type", ""), el.get("selector", ""),
        ]))
        score = _bm25_score(query_tokens, _tokenize(doc_text))
        if el.get("in_viewport"):
            score *= viewport_bonus
        scored.append((score, el))
    scored.sort(key=lambda x: (-x[0], x[1].get("vp_top", 9999)))
    results = [el for s, el in scored if s > 0][:top_k]
    if len(results) < top_k:
        extras = [el for _, el in scored if el.get("in_viewport") and el not in results]
        results += extras[:top_k - len(results)]
    return [{
        "tag": el.get("tag"), "selector": el.get("selector"),
        "text": el.get("text"), "type": el.get("type"), "value": el.get("value"),
    } for el in results]


def extract_first_action(text: str):
    m = re.search(r"Action:\s*(.+?)(?:\n(?:Final Answer:|Thought:)|\Z)", text, re.DOTALL)
    if not m:
        return None
    raw = m.group(1).strip()
    if raw.lower() in ("none", "null", ""):
        return None
    raw = (raw.replace("\u2018", "'").replace("\u2019", "'")
              .replace("\u201c", '"').replace("\u201d", '"'))
    raw_json = raw.replace("'", '"')
    raw_json = re.sub(r'([}\]])\s*[^}\]]*$', r'\1', raw_json, count=1)
    raw_json = re.sub(r'[^\x00-\x7F]+', '', raw_json)
    VALID_TOOLS = ("click", "type", "open_url", "scroll", "wait")

    def _try(s):
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return None

    parsed = _try(raw_json)
    if isinstance(parsed, list):
        valid = [a for a in parsed if isinstance(a, dict) and a.get("tool") in VALID_TOOLS]
        return valid[0] if valid else {"tool": "__parse_error__", "args": {}}
    if isinstance(parsed, dict) and parsed.get("tool") in VALID_TOOLS:
        return parsed
    for match in re.finditer(
        r'\{[^{}]*?"tool"\s*:\s*"(click|type|open_url|scroll|wait)"[^{}]*?\}', text, re.DOTALL
    ):
        candidate = _try(match.group(0).replace("'", '"'))
        if candidate and candidate.get("tool") in VALID_TOOLS:
            return candidate
    return {"tool": "__parse_error__", "args": {}}
