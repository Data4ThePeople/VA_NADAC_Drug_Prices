# Status

Project: VA_NADAC_Drug_Prices
Process: ~/.claude/d4tp-process/PROCESS.md

## Current

Post: va-vs-medicare-drug-prices
Step: 2a
Since: 2026-11-10

## Steps

| Step | What | Confirmed | Notes |
|---|---|---|---|
| 1  | Exploration and analysis | 2026-11-10 | 90 brands, 414 NDCs; dist/index.html, dist/negotiated-30day.html |
| 2a | Draft with brackets resolved | | |
| 2b | Eric's edit, Claude's look-over | | |
| 2c | Slice markup | | |
| 2d | Hero 1680x1080 + alt text | | |
| 2e | SEO | | |
| 2f | Pushed to Prismic (draft) | | |
| 2g | Mailchimp teaser | | |

## Stale

None.

## Log

- 2026-11-08 Step 1 opened. Topic: VA drug prices (FSS, Big4, National Contract) compared
  with NADAC, for Veterans Day, with a focus on common brand drugs. Feasibility check in
  FEASIBILITY.md: the November 1, 2026 VA file carries an NDC on every row; 59 of 66 common
  brands match NADAC by exact NDC. Repo created private in Data4ThePeople.
- 2026-11-09 Scope changed: benchmark is Medicare Part D (2026 Q3 SPUF pricing file, median plan
  unit cost), not NADAC. Angle: VA does not get Medicare negotiated prices. Top 100 brands by 2024
  Part D claims priced vs VA Big4 in `scripts/top100.py`; 88 compared. Not tied out.
- 2026-11-09 Both tie-outs run (TIEOUT.md). Fixes after independent tie-out: Drugs@FDA brand cross-check
  (ANDA-only CMS rows dropped; Klor-Con claims down, top 100 unchanged), NovoLog Mix not negotiated in
  basket, unit check no longer drops Enbrel vial, MFP check uses CMS per-unit file. 90 brands compared,
  414 NDCs; basket $112.46B Part D vs $100.26B VA. Awaiting Eric to close Step 1.
- 2026-11-09 Negotiation selection rules verified (statute, CMS fact sheet) and added to TIEOUT W9-W12. Bar chart
  second order changed to 2024 Part D spending. 30-day chart built for the negotiated drugs.
- 2026-11-10 Step 1 confirmed by Eric.
- 2026-11-10 Step 2a opened. Slug va-vs-medicare-drug-prices. Beats agreed (outline in POST.md); awaiting Eric's draft.
- 2026-11-11 Eric's opinion draft in POST.md with accepted edits 1-17 and 22-24. New charts built and tied out:
  part-d-rebates (Trustees DIR), generic-tiers (ANDA products by tier and years since first generic),
  patient-cost (VA copay vs 2026 standard benefit, plus real-plan medians). Revlimid/lenalidomide paragraph.
  Enbrel 4-syringe cartons confirmed (VA count x FDA mL; per-mL price vs agreed packages); own tie-out
  2,224 OK, 0 REVIEW, 0 DIFF. Medicaid rule (42 CFR 447.53) and SNAP claim checked (TIEOUT W24, W25).
- 2026-11-11 Post laid out: four iframes (heights measured at 360 to 1280px in a real iframe), disclaimer in a
  blurb, drop cap on the first story paragraph, chart 21 block moved below "But the 58 million ... do."
  Notes in every viz folded into "Show notes and disclaimers". README.md drafted. Iframes point at GitHub
  Pages, which needs the repo made public. Independent tie-out of the new charts running.
