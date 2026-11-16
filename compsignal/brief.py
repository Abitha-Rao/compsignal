"""Evidence-backed account briefs. Deterministic: every sentence traces to a posting link."""


def _angle(summary, signals):
    tools = summary["tools"]
    has_title = any(s.kind == "comp_role_title" for s in signals)
    if "Everstage" in tools:
        return ("Postings mention Everstage, so this is likely an existing customer or an evaluator. "
                "Do not cold-prospect; check CRM before any outreach.")
    if has_title and summary["incumbent_signal"] == "specific":
        return (f"Hiring a comp specialist whose posting expects {', '.join(tools)} experience. "
                "Open by asking what is driving the hire (plan changes outpacing tooling?) and offer a "
                "side-by-side on admin time and payout accuracy. The tool may be a skill the company "
                "wants, not what it runs: verify before assuming displacement.")
    if has_title and summary["incumbent_signal"] == "listed":
        return ("Hiring a comp-specific role; the posting lists several ICM platforms as acceptable experience, "
                "so it does not reveal which one they run. Ask rather than assume.")
    if has_title:
        return ("Hiring a comp-specific role with no platform named. Likely building or scaling the "
                "function: open with how teams get to accurate payouts without adding headcount.")
    if any(s.kind == "excel_commission" for s in signals):
        return ("A posting ties commissions to spreadsheets. Open with the cost of manual commission "
                "runs and a month-end close walkthrough.")
    return "Commission duties appear in role descriptions only. Weak signal: monitor, do not prioritise."


def make_brief(summary, signals, new_urls=()):
    lines = [f"### {summary['company']}",
             f"- Comp activity: **{summary['comp_activity']}/100** | Incumbent-tool signal: "
             f"**{summary['incumbent_signal']}**" + (f" ({', '.join(summary['tools'])})" if summary["tools"] else ""),
             f"- Suggested angle: {_angle(summary, signals)}",
             "- Evidence:"]
    seen = set()
    for s in sorted(signals, key=lambda x: (x.kind != "comp_role_title", x.kind)):
        key = (s.kind, s.detail, s.job_url)
        if key in seen:
            continue
        seen.add(key)
        flag = " **(new)**" if s.job_url in new_urls else ""
        label = {"comp_role_title": "Comp role", "comp_duty": "Commission duty",
                 "excel_commission": "Spreadsheet + commissions", "tool": f"Names {s.detail}"}[s.kind]
        lines.append(f"  - {label}{flag}: [{s.job_title}]({s.job_url}) - \"{s.snippet[:220]}\"")
    return "\n".join(lines)
