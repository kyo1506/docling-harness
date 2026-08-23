import re

_RULE_ID_RE = re.compile(r"RQ\d+-(?:RN|RQ)\d+|RN\d+", re.I)
_START_RE = re.compile(r"^\s*[-•]\s*(RQ\d+-(?:RN|RQ)\d+|RN\d+|RQ\d+-CA\d+)\s*[-–—]?\s*(.*)$", re.I)
_BULLET_RE = re.compile(r"^[-•]\s*o\s*")
_NOISE_RE = re.compile(r"Formul[áa]rio|P[áa]gina|Classifica[çc][ãa]o", re.I)
_RQ_HEADING_RE = re.compile(r"\d+\.\d+\s+(RQ\d+)\s*:\s*(.+)")

_STOPWORDS = {
    "a", "o", "os", "as", "de", "do", "da", "dos", "das", "e", "em", "no", "na", "nos", "nas",
    "que", "um", "uma", "uns", "umas", "para", "com", "por", "ao", "aos", "à", "às", "se",
    "é", "já", "não", "mais", "menos", "ser", "ter", "seu", "sua", "seus", "suas", "este",
    "esta", "esse", "essa", "isto", "isso", "como", "quando", "onde", "cada", "qual", "quais",
    "entre", "sobre", "sob", "sem", "até", "após", "antes", "depois", "pela", "pelas", "pelo",
    "pelos", "ou", "the", "and", "of", "to", "in", "is", "for", "on", "an",
}


def structured_extract(text: str, heading_path: str = "", source: str = "") -> dict:
    """Deterministically extract structured RN/CA rules and criteria from section text.

    Returns items in the classified shape (specs.business_rules / specs.acceptance_criteria),
    with the rule id preserved and a source derived from heading_path.
    """
    rules = []
    criteria = []
    lines = text.splitlines()

    counts = {}
    for line in lines:
        s = line.strip()
        if s and len(s) > 5 and not _START_RE.match(s) and not _BULLET_RE.match(s) and not _NOISE_RE.search(s):
            counts[s] = counts.get(s, 0) + 1

    current = None
    for raw in lines:
        line = raw.strip()
        if not line or _NOISE_RE.search(line) or counts.get(line, 0) > 1:
            continue
        m = _START_RE.match(line)
        if m:
            if current:
                _flush(current, rules, criteria)
            rid = m.group(1).upper()
            kind = "ca" if re.search(r"-CA\d+$", rid) else "rule"
            current = [kind, rid, [m.group(2).strip()]]
        elif current is not None:
            current[2].append(_BULLET_RE.sub("", line).strip())

    if current:
        _flush(current, rules, criteria)

    loc = f"{source}§{heading_path}" if heading_path else source
    for r in rules:
        r["source"] = loc
    for a in criteria:
        a["source"] = loc

    return {
        "specs": {
            "business_rules": rules,
            "acceptance_criteria": criteria,
        }
    }


def _flush(current, rules, criteria):
    kind, rid, parts = current
    body = " ".join(p for p in parts if p).strip()
    if not body:
        return
    item = {"id": rid, "rule": f"{rid} - {body}"}
    if kind == "ca":
        criteria.append({**item, "description": item.pop("rule")})
    else:
        rules.append(item)


def rule_id_in(text: str) -> str:
    m = _RULE_ID_RE.search(text or "")
    return m.group(0).upper() if m else ""


def _tokens(text: str) -> set:
    return {t for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if t not in _STOPWORDS}


def _overlaps(a: str, b: str) -> bool:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return False
    return len(ta & tb) >= 3


def _redundant(text: str, det_items: list, text_key: str) -> bool:
    tid = rule_id_in(text)
    for d in det_items:
        if tid and tid == d.get("id", ""):
            return True
        if _overlaps(text, d.get(text_key, "")):
            return True
    return False


def merge_deterministic(body: dict, det: dict) -> dict:
    """Union deterministic items into the LLM-classified body, deduping by rule id or near-duplicate.

    Deterministic (verbatim) items win over the LLM's paraphrase for the same rule.
    """
    if not isinstance(body, dict):
        body = {}
    det_specs = det.get("specs") if isinstance(det.get("specs"), dict) else {}
    det_rules = det_specs.get("business_rules") if isinstance(det_specs.get("business_rules"), list) else []
    det_acs = det_specs.get("acceptance_criteria") if isinstance(det_specs.get("acceptance_criteria"), list) else []
    specs = body.setdefault("specs", {})
    if not isinstance(specs, dict):
        specs = body["specs"] = {}

    llm_rules = specs.get("business_rules") if isinstance(specs.get("business_rules"), list) else []
    llm_acs = specs.get("acceptance_criteria") if isinstance(specs.get("acceptance_criteria"), list) else []

    out_rules = list(det_rules)
    for r in llm_rules:
        if not isinstance(r, dict):
            continue
        if not _redundant(r.get("rule", ""), det_rules, "rule"):
            out_rules.append(r)
    specs["business_rules"] = out_rules

    out_acs = list(det_acs)
    for a in llm_acs:
        if not isinstance(a, dict):
            continue
        if not _redundant(a.get("description", ""), det_acs, "description"):
            out_acs.append(a)
    specs["acceptance_criteria"] = out_acs

    return body


def requirements_from_headings(heading_path: str, source: str, fallback_text: str = "") -> list:
    """Derive requirement items from `7.N RQxx: <TITLE>` section headings.

    Falls back to the first rule's RQ prefix when the heading does not match.
    """
    reqs = []
    loc = f"{source}§{heading_path}" if heading_path else source
    m = _RQ_HEADING_RE.search(heading_path or "")
    if m:
        reqs.append({"id": m.group(1).upper(), "description": m.group(2).strip(), "source": loc})
    elif fallback_text:
        rid = rule_id_in(fallback_text)
        rq = re.match(r"(RQ\d+)", rid or "")
        if rq:
            reqs.append({"id": rq.group(1), "description": rq.group(1), "source": loc})
    return reqs


def apply_requirements(body: dict, heading_path: str, source: str, fallback_text: str = "") -> dict:
    """Replace LLM-provided requirements with heading-derived requirements."""
    if not isinstance(body, dict):
        body = {}
    specs = body.setdefault("specs", {})
    if not isinstance(specs, dict):
        specs = body["specs"] = {}
    specs["requirements"] = requirements_from_headings(heading_path, source, fallback_text)
    return body
