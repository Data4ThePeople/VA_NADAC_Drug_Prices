# Status

Project: VA_NADAC_Drug_Prices
Process: ~/.claude/d4tp-process/PROCESS.md

## Current

Post: va-vs-medicare-drug-prices
Step: 2g
Since: 2026-11-11

## Steps

| Step | What | Confirmed | Notes |
|---|---|---|---|
| 1  | Exploration and analysis | 2026-11-11 | Re-confirmed after the Humira fix (first confirmed 2026-11-10). 89 brands, 415 NDCs; dist/index.html, dist/negotiated-30day.html, dist/part-d-rebates.html, dist/generic-tiers.html, dist/patient-cost.html |
| 2a | Draft with brackets resolved | 2026-11-11 | Edits 1-17, 22-30 accepted; four chart embeds; repo public, Pages on |
| 2b | Eric's edit, Claude's look-over | 2026-11-11 | Edits 31-40, 42, 43 accepted (41 folded into 40); section headers; 46brooklyn link; new CMS enrollment source |
| 2c | Slice markup | 2026-11-11 | 41 slices; no markup changes needed |
| 2d | Hero 1680x1080 + alt text | 2026-11-11 | Re-done: new hero, veteran paying $11 in cash (Gemini, prompt 1), crop window shifted right; alt 352 characters |
| 2e | SEO | 2026-11-11 | Re-checked with the new hero, no changes. Six target searches; meta title, description, 8 keywords; Article schema; edit 44 (How we built this); date 2026-11-11 9:30 a.m. ET |
| 2f | Pushed to Prismic (draft) | 2026-11-11 | Re-pushed with the new hero and edit 46. Draft in the Migration Release, 45 slices; Eric's Marshalls edit made in Prismic and mirrored in POST.md |
| 2g | Mailchimp teaser | | Reopened 2026-11-11. EMAIL.md in Eric's words; static generic tier chart (images/01-generic-tiers.png); hero email JPG 216KB; edits 45 and 47 |

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
- 2026-11-11 Eric accepted edits 25 (Medicaid "mostly") and 26 (SNAP post link). Repo made public at Eric's
  request; GitHub Pages on from main, root. All four embeds load from data4thepeople.github.io (HTTP 200).
- 2026-11-11 Second independent tie-out (charts 19-21, 30-day chart, post claims): nearly all matched. It found
  a Step 1 bug: FDA leaves SUBSTANCENAME blank for Humira and Paxlovid, so the brand filter dropped them.
  Fixed (NONPROPRIETARYNAME fallback; Drugs@FDA application-name rule drops the generic "PEG 3350-Electrolyte").
  Humira priced per kit (cartons of single-syringe kits); Paxlovid out (kit dose packs). Top 100 now has
  Humira and Paxlovid; Admelog and Rinvoq drop out. 89 brands compared, 415 NDCs; basket Part D $116.55B,
  VA $103.43B (11.3% lower). Patient-cost chart: Humira replaces Entresto; real plans priced at each plan's own
  price; tiers 3 to 5. New scripts/lenalidomide.py; Revlimid paragraph corrected (at least $1,600 was wrong
  for 28% of plans). Own tie-out 2,235 OK, 0 DIFF. Step 1 results changed, so Step 1 needs re-confirming
  with 2a. Third independent check of the fixes running. Not yet pushed: live Pages charts are the old build.
- 2026-11-11 Third independent check of the fixes: every chart value matched. Fixed what it found: Premarin
  now in the basket (asterisk name mismatch; basket 89 brands, $116.79B vs $103.61B, $13.18B or 11.3% lower),
  Mounjaro 2.5 mg starting pens left out of the 30-day price, chart 18 "not shown" note built from data (11).
  Disclosed Ozempic tablets, vaccines, source-agreement counts. Own tie-out 2,236 OK, 0 DIFF.
- 2026-11-11 Eric accepted edits 27-30 (basket now "89 ... about $13 billion, or 11%", "89 top brand-name
  drugs", "rarely see a dime", "tiers usually used for"). Step 1 re-confirmed and Step 2a confirmed by Eric.
  Next: 2b, Eric edits POST.md and asks for a look-over.
- 2026-11-11 Step 2b. Eric's edits plus accepted edits 31-40, 42 and 43: title and subtitle, six section headers,
  46brooklyn link on plan pricing, "tiers usually used for more expensive brand-name drugs", basket totals in
  the opening ($104B VA vs $117B Part D, 2024 prescriptions at 2026 prices). New source: CMS Monthly Enrollment
  by Plan, October 2026 (`scripts/parent_orgs.py`): the 5,295 plans cover about 48 million people, 76% in plans
  of the five largest parent companies. Own tie-out 2,243 OK, 0 DIFF; fourth independent tie-out matched the new
  claim. Step 2b confirmed by Eric. Next: 2c, slice markup.
- 2026-11-11 Step 2c: convert-only run, 41 slices (blurb, drop cap, four embeds at measured heights, six
  headings with 5px spacers, 20px after embeds and 40px before a heading). No markup changes needed. Step 2c
  confirmed by Eric. Next: 2d, hero. Eric's idea: Korean War soldiers walking through a large pharmacy. The
  memorial's statues are under copyright (Gaylord v. United States, 2010), so the prompt uses new figures.
- 2026-11-11 Step 2d: Eric generated prompt 1 in Gemini (2752x1536, no visible watermark); `hero fit` center
  crop to 1680x1080; source kept; alt text 341 characters. Step 2d confirmed by Eric. Next: 2e, SEO.
- 2026-11-11 Step 2e: target searches (VA drug prices vs Medicare; VA prescription copay; Medicare Part D drug
  tiers; generics on a brand tier in Part D; Medicare negotiated drug prices and the VA; Part D coinsurance vs
  copay). meta_title, description, keywords written; Article schema; edit 44 accepted (How we built this, after
  divider dots, GitHub link); sterile water post not linked (Eric). Date 2026-11-11, time 09:30 EST. Step 2e
  confirmed by Eric. Next: 2f, Prismic draft.
- 2026-11-11 After the Prismic push, Eric changed "To be fair, it’s not fair to Marshalls" to "But it’s not fair to
  Marshalls" in the Prismic draft himself; POST.md updated to match, not pushed again.
- 2026-11-11 Step 2f: dry run clean, then pushed. Draft created in the Migration Release (not live), 45 slices,
  hero uploaded as featured and meta image, tags and author empty. Not read back (no Content API read token).
  Step 2f confirmed by Eric. Next: 2g, Mailchimp teaser with a static image of the generic tier chart.
- 2026-11-11 Step 2g: edits 45 and 46 accepted ("Before that, they pay the plan’s full price for the drug." in the
  email and the post). Draft re-pushed to Prismic (same document, Migration Release); Eric's only Prismic edit was
  the Marshalls sentence, already in POST.md.
- 2026-11-11 Back to 2d: Eric asked for a new hero, a veteran at a pharmacy counter paying the copay in cash
  ($11). 2e and 2f marked stale; 2g's email hero needs re-exporting. EMAIL.md, the static generic tier chart
  and edits 45 and 46 are kept.
- 2026-11-11 New hero from Eric (Gemini, prompt 1): veteran paying a $10 and a $1 at a pharmacy counter, register
  reads $11.00. Cropped from x = 272 to 2661 so the register keeps a margin, then `hero fit`; alt text 352
  characters. On Eric's instruction ran 2e (no SEO changes) and 2f again: hero ledger entry cleared, new hero
  uploaded, same draft updated in the Migration Release. Email hero JPG re-exported (216KB) and EMAIL.md alt
  updated. Stale cleared. Next: Eric confirms 2g.
- 2026-11-11 Step 2g: edit 47 accepted ("inflated pre-rebate prices" in place of "Compare at" in the email, which
  has no Marshalls example). Step 2g confirmed by Eric. Post complete: draft in the Prismic Migration Release,
  EMAIL.md ready for Mailchimp.
- 2026-11-11 Back to 2g (Eric): the "Because here our elderly pay..." sentence in the email becomes Eric's
  three-item list. Email only; the post keeps the sentence. No later steps to mark stale.
