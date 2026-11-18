"""CLI:  python -m compsignal collect | report | sample"""
import argparse
import datetime as dt
import json
import os
import random

from . import brief, collect, evaluate, notify, score, signals, store


def read_companies(path):
    out = []
    for line in open(path, encoding="utf8"):
        line = line.split("#")[0].strip()
        if line:
            out.append(line.lower())
    return list(dict.fromkeys(out))


def cmd_collect(a):
    con = store.connect()
    slugs = read_companies(a.companies)[: a.limit]
    hit = 0
    for i, slug in enumerate(slugs, 1):
        source, jobs = collect.fetch_company(slug)
        if jobs:
            store.save_company(con, slug, source, jobs)
            hit += 1
        print(f"[{i}/{len(slugs)}] {slug:18} {source or 'not found':10} {len(jobs):4} postings", flush=True)
    print(f"\nReachable: {hit}/{len(slugs)}")


def analyse_all(con, since_days=7):
    cutoff = dt.date.today() - dt.timedelta(days=since_days)
    # The first collection marks everything as "first seen"; only flag postings that appeared after it.
    baseline = con.execute("SELECT MIN(first_seen) FROM jobs").fetchone()[0]
    cutoff = max(cutoff, baseline + dt.timedelta(days=1)) if baseline else cutoff
    rows = []
    for company in store.collected_companies(con):
        jobs = store.current_jobs(con, company)
        sigs = [s for j in jobs for s in signals.analyze_job(j)]
        if not sigs:
            continue
        new_urls = {j["url"] for j in jobs if j["first_seen"] >= cutoff}
        rows.append((score.summarize(company, sigs), sigs, new_urls))
    rows.sort(key=lambda r: (-r[0]["comp_activity"], r[0]["incumbent_signal"] != "specific", r[0]["company"]))
    return rows


def cmd_report(a):
    con = store.connect()
    rows = [r for r in analyse_all(con) if r[0]["comp_activity"] >= a.min_score or r[0]["incumbent_signal"] != "none"]
    total = len(store.collected_companies(con))
    today = dt.date.today().isoformat()
    md = [f"# CompSignal report - {today}",
          f"{len(rows)} of {total} reachable companies have at least one strict signal. "
          "A missing signal means no evidence found, not no need.\n"]
    md += [brief.make_brief(s, sg, nu) + "\n" for s, sg, nu in rows]
    os.makedirs("reports", exist_ok=True)
    path = f"reports/{today}.md"
    open(path, "w", encoding="utf8").write("\n".join(md))
    json.dump([s for s, _, _ in rows], open("reports/latest.json", "w"), indent=1)
    print(f"{len(rows)} flagged of {total}. Wrote {path}")
    for s, _, _ in rows[:15]:
        print(f"  {s['name']:14} comp={s['comp_activity']:3} tools={s['incumbent_signal']:8} {','.join(s['tools'])}")
    if a.slack:
        print(notify.post_slack(rows[:10], today))


def cmd_sample(a):
    """Draw a random sample of evidence items for hand-labelling (precision check)."""
    con = store.connect()
    items = []
    for s, sg, _ in analyse_all(con):
        for x in sg:
            items.append((s["company"], x))
    seen, uniq = set(), []
    for company, x in items:  # the same text often appears in several postings of one company
        k = (company, x.kind, x.detail, x.snippet[:80])
        if k not in seen:
            seen.add(k); uniq.append((company, x))
    items = uniq
    if a.exclude:  # keep a fresh sample independent of items already labelled
        done = {(r["company"], r["kind"], r["detail"], r["url"]) for r in json.load(open(a.exclude))}
        items = [(c, x) for c, x in items if (c, x.kind, x.detail, x.job_url) not in done]
    random.Random(a.seed).shuffle(items)
    os.makedirs("eval", exist_ok=True)
    sheet, key = [], []
    for i, (company, x) in enumerate(items[: a.n], 1):
        sheet.append(f"{i}. [{company}] {x.kind}/{x.detail} - {x.job_title}\n   \"{x.snippet[:300]}\"\n   {x.job_url}\n")
        key.append({"n": i, "company": company, "kind": x.kind, "detail": x.detail, "url": x.job_url, "label": None, "sys_specific": (x.specific if x.kind == "tool" else None)})
    open("eval/sheet.md", "w", encoding="utf8").write("\n".join(sheet))
    json.dump(key, open("eval/labels.json", "w"), indent=1)
    print(f"Sampled {len(key)} of {len(items)} evidence items -> eval/sheet.md, eval/labels.json")


def cmd_draft(a):
    """Claude writes first-touch emails for the top accounts from their linked evidence."""
    from . import draft
    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        raise SystemExit("Set ANTHROPIC_API_KEY first (https://console.anthropic.com/). Keep it out of the repo.")
    con = store.connect()
    rows = [r for r in analyse_all(con) if r[0]["comp_activity"] >= 40 or r[0]["incumbent_signal"] != "none"]
    kept, md = draft.make_drafts(rows[: a.top])
    today = dt.date.today().isoformat()
    os.makedirs("reports", exist_ok=True)
    path = f"reports/{today}-drafts.md"
    open(path, "w", encoding="utf8").write(
        f"# CompSignal first-touch drafts - {today}\n"
        f"Written by Claude ({draft.MODEL}) from linked evidence only; each draft passed the evidence checks. "
        "Review before sending.\n\n" + md)
    print(f"{kept} drafts passed checks. Wrote {path}")


def main():
    p = argparse.ArgumentParser(prog="compsignal")
    sub = p.add_subparsers(required=True)
    c = sub.add_parser("collect"); c.add_argument("--companies", default="companies.txt")
    c.add_argument("--limit", type=int, default=10_000); c.set_defaults(fn=cmd_collect)
    r = sub.add_parser("report"); r.add_argument("--min-score", type=int, default=40)
    r.add_argument("--slack", action="store_true"); r.set_defaults(fn=cmd_report)
    s = sub.add_parser("sample"); s.add_argument("--n", type=int, default=40)
    s.add_argument("--seed", type=int, default=7); s.add_argument("--exclude"); s.set_defaults(fn=cmd_sample)
    d = sub.add_parser("draft"); d.add_argument("--top", type=int, default=10); d.set_defaults(fn=cmd_draft)
    l = sub.add_parser("score-labels"); l.set_defaults(fn=lambda a: print(evaluate.score()))
    a = p.parse_args(); a.fn(a)


main()
