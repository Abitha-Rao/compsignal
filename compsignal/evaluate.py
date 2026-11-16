"""Precision from hand labels, with a 95% Wilson range (same method as painpoint-finder)."""
import json
import math


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def score(path="eval/labels.json"):
    rows = [r for r in json.load(open(path)) if r["label"] is not None]
    out = []
    def line(name, k, n):
        lo, hi = wilson(k, n)
        out.append(f"{name}: {k}/{n} = {k/n:.0%} (95% range {lo:.0%}-{hi:.0%})")
    line("Extraction correct, all signals", sum(r["label"] for r in rows), len(rows))
    for kind in sorted({r["kind"] for r in rows}):
        sub = [r for r in rows if r["kind"] == kind]
        line(f"  {kind}", sum(r["label"] for r in sub), len(sub))
    tools = [r for r in rows if r["kind"] == "tool" and r["label"] == 1]
    line("Tool mentions that point to a specific platform", sum(r.get("specific", 0) for r in tools), len(tools))
    both = [r for r in tools if "sys_specific" in r]
    if both:
        agree = sum(1 for r in both if bool(r["sys_specific"]) == bool(r.get("specific", 0)))
        line("Specific-vs-listed flag matches my reading", agree, len(both))
    return "\n".join(out)
