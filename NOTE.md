# Half-page note: what I would automate first

*Draft. Replace anything below that does not match your own experience before sending.*

**The process: deciding which accounts an outbound rep researches next.**

A rep starts the week with a long list of companies and little reason to pick one over another.
Research is slow, so reps either guess or spend hours reading career pages and news. For a
sales-compensation vendor this is worse than usual, because the buyer is rare: usually one person
in a company runs commissions, and their problems rarely show up in ads or social posts.

**What I would automate first: the evidence-gathering, not the outreach.**

I built CompSignal to do one narrow thing. Every week it reads the public job boards of target
companies and flags explicit signs that a commission operation is in motion: a Commissions Manager
role is open, a posting names one compensation platform, or commission work is tied to spreadsheets.
It gives the rep a short brief with the evidence linked, so the rep can disagree with it. I kept the
scoring rule-based and used no AI for judgement, so every number can be challenged.

**What I found while testing it.** Of 150 reachable companies, 14 had a strict signal. In a hand-labelled
sample of 40 flags, 88% were extracted correctly (range 74 to 95%). The more useful result was a
failure: only 36% of platform mentions pointed to a platform the company actually runs. Most were
"experience with A, B or C" lists. I changed the scoring to separate the two.

**How I would know it worked.**
1. Accuracy: at least 80% of flagged evidence confirmed on a fresh labelled sample, every month.
2. Usefulness: reps judge at least half of the weekly briefs worth a first touch.
3. Speed: research time per account falls, measured against a few accounts researched by hand.
4. Outcome: reply and meeting rates for flagged accounts against a comparable unflagged group.

If accuracy falls below the bar or reps ignore the briefs for a month, I would narrow the signals or
retire it. A missing signal never means "no need", and a flag never means "will buy".
