"""Draft checks, with a fake Claude client (no API key or network needed)."""
import json
from types import SimpleNamespace

from compsignal import draft
from compsignal.signals import Signal

URL = "https://example.com/jobs/1"
SIGS = [Signal("comp_role_title", "Commissions Manager", "Commissions Manager", "Commissions Manager", URL, True, False),
        Signal("tool", "Xactly", "...such as Xactly, Spiff or CaptivateIQ...", "Commissions Manager", URL, True, False)]
LISTED = {"company": "acme", "name": "Acme", "comp_activity": 40, "incumbent_signal": "listed", "tools": ["Xactly", "Spiff"]}
BODY = ("Saw you're hiring a Commissions Manager. Teams that add that role are often scaling plans faster "
        "than their payout process. Everstage helps comp teams run commissions without spreadsheets, so new "
        "plans go live in days and reps can see what they will earn. Would it be useful to compare how your "
        "team calculates payouts today with how other companies at your stage handle it? Happy to share notes.")


class FakeClient:
    def __init__(self, out, stop="end_turn"):
        msg = SimpleNamespace(stop_reason=stop, content=[SimpleNamespace(type="text", text=json.dumps(out))])
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: msg))


def test_good_draft_passes():
    d, problems = draft.write_draft(FakeClient({"subject": "Commissions hire", "body": BODY, "evidence_urls": [URL]}), LISTED, SIGS)
    assert d and not problems


def test_invented_url_rejected():
    d, problems = draft.write_draft(FakeClient({"subject": "x", "body": BODY, "evidence_urls": ["https://made.up"]}), LISTED, SIGS)
    assert d is None and "not in the evidence" in problems[0]


def test_platform_named_without_specific_signal_rejected():
    body = BODY.replace("Everstage helps", "Since you run Xactly, Everstage helps")
    d, problems = draft.write_draft(FakeClient({"subject": "x", "body": body, "evidence_urls": [URL]}), LISTED, SIGS)
    assert d is None and "specific-platform" in problems[0]


def test_specific_signal_may_name_platform():
    summary = dict(LISTED, incumbent_signal="specific", tools=["Xactly"])
    body = BODY.replace("Everstage helps", "Since the role works in Xactly, Everstage helps")
    d, _ = draft.write_draft(FakeClient({"subject": "x", "body": body, "evidence_urls": [URL]}), summary, SIGS)
    assert d


def test_refusal_or_cutoff_dropped():
    d, problems = draft.write_draft(FakeClient({}, stop="max_tokens"), LISTED, SIGS)
    assert d is None and "max_tokens" in problems[0]


def test_customer_skipped_without_calling_claude():
    kept, md = draft.make_drafts([(dict(LISTED, tools=["Everstage"]), SIGS, set())], client=object())
    assert kept == 0 and "likely customer" in md
