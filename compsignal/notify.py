"""Optional Slack delivery. Needs SLACK_WEBHOOK_URL in the environment (never commit it)."""
import json
import os
import urllib.request


def post_slack(rows, today):
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        return "Slack skipped: SLACK_WEBHOOK_URL is not set."
    lines = [f"*CompSignal {today}: top {len(rows)} accounts*"]
    for s, sig, _ in rows:
        first = next((x for x in sig if x.kind == "comp_role_title"), sig[0])
        lines.append(f"- *{s['name']}* comp {s['comp_activity']}/100, tools: {s['incumbent_signal']} "
                     f"<{first.job_url}|{first.job_title}>")
    req = urllib.request.Request(url, data=json.dumps({"text": "\n".join(lines)}).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return f"Slack: {r.status}"
