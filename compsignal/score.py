"""Deterministic, explainable scoring. Two separate outputs per company; no blended number."""
from collections import defaultdict


def comp_activity_score(signals):
    """0-100. Weights are explicit so anyone can challenge them."""
    n_title = sum(1 for s in signals if s.kind == "comp_role_title")
    n_duty = sum(1 for s in signals if s.kind == "comp_duty")
    excel = any(s.kind == "excel_commission" for s in signals)
    score = 0
    if n_title:
        score += 40 + 10 * min(n_title - 1, 2)  # first comp role 40, +10 per extra (max +20)
    score += 10 * min(n_duty, 3)  # commission duties in other roles, max 30
    if excel:
        score += 20
    return min(score, 100)


def incumbent_tool_signal(signals):
    """Return (strength, tools). strength: specific | listed | none.

    specific = a single platform is named (e.g. "plan logic in Xactly"), which suggests the company runs it
    listed   = platforms appear only in "such as A, B or C" lists of acceptable experience: they tell you
               what candidates should know, not what the company runs
    """
    tools, specific = set(), set()
    for s in signals:
        if s.kind == "tool":
            tools.add(s.detail)
            if s.specific:
                specific.add(s.detail)
    if specific:
        return "specific", sorted(specific)
    if tools:
        return "listed", sorted(tools)
    return "none", []


def summarize(company, signals):
    strength, tools = incumbent_tool_signal(signals)
    return {
        "company": company,
        "comp_activity": comp_activity_score(signals),
        "incumbent_signal": strength,
        "tools": tools,
        "n_signals": len(signals),
    }
