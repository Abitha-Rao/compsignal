"""First-touch email drafts written by Claude from the linked evidence only.

The rules decide which accounts are flagged and how they score. Claude only writes the draft, and every draft
is checked before it reaches a rep: it must cite at least one evidence URL, every URL it cites must come from
that account's evidence, and it may not claim a platform is in use unless the incumbent signal is "specific".
Drafts that fail a check are dropped and the reason is recorded.
"""
import json

MODEL = "claude-opus-5-5"

SYSTEM = """You write first-touch outbound emails for Everstage, a sales-commission software company.
You receive public job-posting evidence about one company. Write a short, plain email to the person who
would own sales compensation there.

Rules:
- Use only facts in the evidence. Do not invent numbers, names, pain points or results.
- Refer to the evidence naturally (for example "saw you're hiring a Senior Commissions Manager").
- Only mention a compensation platform by name if incumbent_signal is "specific". If it is "listed" or
  "none", platforms in the evidence are only skills a posting accepts, so do not name any platform.
- 70 to 110 words in the body, one clear question at the end, no flattery, no exclamation marks.
- In evidence_urls, list the URLs of the evidence items the email relies on, copied exactly."""

SCHEMA = {
    "type": "object",
    "properties": {
        "subject": {"type": "string"},
        "body": {"type": "string"},
        "evidence_urls": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["subject", "body", "evidence_urls"],
    "additionalProperties": False,
}

PLATFORMS = ["CaptivateIQ", "Xactly", "Varicent", "Spiff", "QuotaPath", "Performio", "Callidus"]


def evidence_for(signals):
    seen, items = set(), []
    for s in signals:
        key = (s.kind, s.detail, s.job_url)
        if key not in seen:
            seen.add(key)
            items.append({"type": s.kind, "detail": s.detail, "job_title": s.job_title.strip(),
                          "url": s.job_url, "snippet": s.snippet[:300]})
    return items


def check(draft, summary, evidence):
    """Return a list of problems; empty means the draft can go to a rep."""
    problems = []
    urls = {e["url"] for e in evidence}
    if not draft["evidence_urls"]:
        problems.append("cites no evidence")
    bad = [u for u in draft["evidence_urls"] if u not in urls]
    if bad:
        problems.append(f"cites URLs not in the evidence: {bad}")
    if summary["incumbent_signal"] != "specific":
        named = [p for p in PLATFORMS if p.lower() in draft["body"].lower()]
        if named:
            problems.append(f"names {named} without a specific-platform signal")
    words = len(draft["body"].split())
    if not 40 <= words <= 160:
        problems.append(f"body is {words} words")
    return problems


def write_draft(client, summary, signals):
    """Return (draft or None, problems)."""
    evidence = evidence_for(signals)
    payload = {"company": summary["name"], "comp_activity": summary["comp_activity"],
               "incumbent_signal": summary["incumbent_signal"], "platforms": summary["tools"],
               "evidence": evidence}
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=4000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
        system=SYSTEM,
        messages=[{"role": "user", "content": json.dumps(payload, indent=1)}],
    )
    if response.stop_reason != "end_turn":
        return None, [f"model stopped: {response.stop_reason}"]
    text = next(b.text for b in response.content if b.type == "text")
    draft = json.loads(text)
    problems = check(draft, summary, evidence)
    return (None if problems else draft), problems


def skip_reason(summary):
    if "Everstage" in summary["tools"]:
        return "mentions Everstage: likely customer, no cold email"
    if summary["comp_activity"] < 40:
        return "signal too weak for outreach"
    return None


def make_drafts(rows, client=None):
    """rows are (summary, signals, new_urls) from analyse_all. Returns Markdown."""
    if client is None:
        import anthropic
        client = anthropic.Anthropic()
    out, kept = [], 0
    for summary, signals, _ in rows:
        reason = skip_reason(summary)
        if reason:
            out.append(f"### {summary['name']}\n_Skipped: {reason}._\n")
            continue
        draft, problems = write_draft(client, summary, signals)
        if draft is None:
            out.append(f"### {summary['name']}\n_Draft rejected by checks: {'; '.join(problems)}._\n")
            continue
        kept += 1
        cites = "\n".join(f"  - {u}" for u in draft["evidence_urls"])
        out.append(f"### {summary['name']}\n**Subject:** {draft['subject']}\n\n{draft['body']}\n\n"
                   f"Evidence used:\n{cites}\n")
    return kept, "\n".join(out)
