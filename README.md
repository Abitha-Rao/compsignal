# CompSignal

Evidence-based account discovery for a sales-compensation software team.

CompSignal reads the public job boards of target companies and flags explicit signs that a company's
sales-commission operation is in motion: open comp-specific roles, named compensation platforms, and
spreadsheet-based commission work. Each flag links to the original posting so a person can check it.

It was built as a take-home for a Growth Engineer role. It is a working prototype, not a finished product.

## What it found (collected 16 Nov 2026)

- 150 of 250 company job boards were reachable through the official Greenhouse, Lever and Ashby APIs.
- 14 of those 150 companies have at least one strict signal.
- Examples with a specific platform named: Okta, MongoDB, Elastic and Collibra (Xactly).
- Notion, a known Everstage customer, is flagged as mentioning Everstage, and its brief says not to cold-prospect it.

A missing signal means no evidence was found. It does not mean the company has no need.

## How it works

```
companies.txt -> collect (job-board APIs) -> DuckDB -> signals (rules) -> score -> brief -> report / Slack
```

1. **Collect.** `python -m compsignal collect` reads open postings and stores them in DuckDB (`data/`).
2. **Signals.** Pattern rules find evidence. No AI decides anything here.
3. **Score.** Two separate outputs per company, deliberately not blended into one number.
4. **Brief.** A short Markdown brief per company with a suggested angle and linked evidence.
5. **Deliver.** `reports/<date>.md`, and optionally Slack.

### Scoring rules

| Evidence | Effect |
|---|---|
| Comp-specific role title (Commissions Manager, Sales Compensation Analyst) | 40 points, +10 per extra role (max +20) |
| Commission duties in another role's description | +10 each (max +30) |
| Spreadsheet and commissions in the same sentence | +20 |
| One platform named (for example "plan logic in Xactly") | incumbent signal: **specific** |
| Platforms named only in a "such as A, B or C" list | incumbent signal: **listed** |

"Comp activity" (0 to 100) and "incumbent signal" are reported separately. A platform named in a
posting means candidates should know it. It does not prove the company runs it.

## Accuracy

I labelled a random sample of 40 flagged items from the first version of the rules, reading each
posting. This was one labeller (me, with AI help), so spot-check `eval/sheet.md`.

| Check | Result |
|---|---|
| Extraction correct, all signals | 35/40 = 88% (95% range 74-95%) |
| Comp-role titles | 5/5 |
| Tool mentions that point to a specific platform | 9/25 = 36% (95% range 20-55%) |

The last row drove a design change: most tool mentions are lists of acceptable experience, so the
scoring now separates "specific" from "listed". Those fixes were tuned on the same 40 items, so the
88% describes the earlier rules. Measure again on a fresh sample before relying on the new ones:

```
.venv/bin/python -m compsignal sample --n 40 --seed 11   # then fill eval/labels.json
.venv/bin/python -m compsignal score-labels
```

## Limits

- Coverage depends on the company using a supported job board. 40% of my starter list was unreachable.
- Job postings show who is hiring now, not who is buying.
- A small starter list of known customers is only a sanity check, not validation, and I did not test
  whether the score separates customers from non-customers. Job boards show current postings only,
  so a before-purchase comparison is not possible.
- Large companies dominate the hits and often already run a platform.

## Run it

```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m compsignal collect            # about 5 minutes for 250 companies
.venv/bin/python -m compsignal report             # writes reports/<date>.md
.venv/bin/python -m pytest -q
```

Edit `companies.txt` to change targets. Slack is optional: set `SLACK_WEBHOOK_URL` in your shell and add
`--slack` to `report`. Never commit the webhook.

### Weekly automation with n8n

`n8n/compsignal-weekly.json` runs collect and report every Monday and posts the top accounts to Slack.
It uses the Execute Command node, which recent n8n versions disable by default, so enable it
(see the n8n docs) and update the folder path in the workflow. I have not run this workflow inside n8n yet.

## Responsible use

- Uses only the official public job-board APIs, identifies itself, and waits between requests.
- Stores company names and public posting text only. No personal data.
- A flag is a lead to check by hand, not a verdict about a company.
