"""Rule-based signal extraction. No AI here: every signal is a pattern match with its evidence.

Two separate families, deliberately not merged into one score:
  * comp activity: is this company running or building a sales-compensation operation?
  * incumbent tool: does a posting name a compensation platform?
"""
import html
import re
from dataclasses import dataclass

# --- comp activity -----------------------------------------------------------------------
COMP_ROLE_TITLE = re.compile(
    r"\b(sales|incentive|commissions?|gtm)\W+(compensation|comp)\b"
    r"|\bcommissions?\s+(analyst|manager|specialist|administrator|accountant|lead)\b"
    r"|\bincentive\s+compensation\b",
    re.I,
)
# Day-to-day commission administration described in a posting for any role.
COMP_DUTY = re.compile(
    r"\b(calculat\w*|administ\w*|process\w*|audit\w*|reconcil\w*|validat\w*|support\w*|own\w*)\W+(?:\w+\W+){0,3}?"
    r"(commissions?|incentive\s+comp\w*|incentive\s+plans?"
    r"|sales\s+comp\w*\s+(?:plans?|payouts?|processes|administration))\b",
    re.I,
)
# Accounting for commissions (ASC 340-40 etc.) is not commission operations.
ACCOUNTING_CONTEXT = re.compile(r"ASC\s*340|deferred commission|capitaliz\w*|amortiz\w*", re.I)
# Must sit in the same sentence ([^.!?]), so "...bonus and commissions. Proficient with Excel" is not a hit.
EXCEL_COMMISSION = re.compile(
    r"\b(excel|spreadsheets?|google\s+sheets)\b[^.!?]{0,80}\bcommissions?\b"
    r"|\bcommissions?\b[^.!?]{0,80}\b(excel|spreadsheets?|google\s+sheets)\b",
    re.I,
)

# --- incumbent tools ---------------------------------------------------------------------
# Case-sensitive on purpose where the word has a generic meaning: "SPIFF" is a sales bonus,
# "Spiff" is the vendor; "exactly" contains "xactly".
TOOLS = {
    "CaptivateIQ": re.compile(r"\bCaptivateIQ\b", re.I),
    "Xactly": re.compile(r"\bXactly\b"),
    "Varicent": re.compile(r"\bVaricent\b", re.I),
    "Spiff": re.compile(r"\bSpiff\b"),
    "QuotaPath": re.compile(r"\bQuotaPath\b", re.I),
    "Performio": re.compile(r"\bPerformio\b", re.I),
    "Callidus": re.compile(r"\bCallidus\b", re.I),
    "Everstage": re.compile(r"\bEverstage\b", re.I),
}


COMP_CONTEXT = re.compile(r"commission|incentive|compensation|\bICM\b|\bSPM\b|sales performance|quota|payout", re.I)


@dataclass
class Signal:
    kind: str  # comp_role_title | comp_duty | excel_commission | tool
    detail: str  # e.g. tool name, or the matched phrase
    snippet: str
    job_title: str
    job_url: str
    in_comp_role: bool = False  # for tools: was it named inside a comp-specific role?
    specific: bool = False  # for tools: a single platform named, not a 'such as A, B or C' list


def _snippet(text, m, width=110):
    s = max(0, m.start() - width)
    e = min(len(text), m.end() + width)
    return ("..." if s else "") + text[s:e].strip() + ("..." if e < len(text) else "")


def analyze_job(job):
    """Return a list of Signal for one posting dict (title, text, url)."""
    title, url = job["title"], job["url"]
    # Some boards double-escape HTML; clean twice and drop non-breaking spaces.
    text = html.unescape(html.unescape(job["text"])).replace("\xa0", " ")
    out = []
    title_hit = COMP_ROLE_TITLE.search(title)
    if title_hit:
        out.append(Signal("comp_role_title", title_hit.group(0), title, title, url))
    else:
        m = COMP_DUTY.search(text)
        if m and not ACCOUNTING_CONTEXT.search(text[max(0, m.start() - 200): m.end() + 200]):
            out.append(Signal("comp_duty", m.group(0), _snippet(text, m), title, url))
    m = EXCEL_COMMISSION.search(text)
    if m:
        out.append(Signal("excel_commission", "spreadsheet + commissions", _snippet(text, m), title, url))
    for name, rx in TOOLS.items():
        m = rx.search(text)
        src = text
        if not m:
            m = rx.search(title)
            src = title
        if not m:
            continue
        window = src[max(0, m.start() - 150): m.end() + 150]
        # Outside a comp role the mention must sit in a comp context, otherwise it is noise
        # (e.g. a vendor listed as a customer reference in a BDR posting).
        if not title_hit and not COMP_CONTEXT.search(src[max(0, m.start() - 250): m.end() + 250]):
            continue
        n_tools = sum(1 for r2 in TOOLS.values() if r2.search(window))
        out.append(Signal("tool", name, _snippet(src, m), title, url,
                          in_comp_role=bool(title_hit), specific=(n_tools == 1)))
    return out
