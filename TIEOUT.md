# Tie-out

Status of every number and claim that may appear in a chart, table or headline.
Claude's own tie-out: `scripts/tieout.py`, full results in `data/work/tieout_claude.csv` (latest run: 2,065
OK, 2 REVIEW, 0 DIFF; the 2 REVIEW rows are the Enbrel cartons in M2).
Independent tie-out: a fresh agent given the sources, `DATASETS.md` and the built files (not Claude's
numbers), November 9, 2026. It pulled every source again (its FDA files were dated November 9, ours
November 6) and recomputed with its own code. Its results are against the build before the fixes of
November 9 (M8 to M10); rows those fixes changed say so.

## Numbers

| # | Number | Value | Built in | Claude tie-out | Independent |
|---|---|---|---|---|---|
| 1 | Top 100 brands, 2024 Part D claims per brand | 100 values | `top100_brand.csv` | OK, all 100 recomputed from raw annual file; one row per brand, no CMS row counted twice | Matched all 100 exactly, using the first-word rule. Klor-Con has since dropped to 252,932 claims (M8), not re-checked independently |
| 2 | Brands compared | 90 | `top100_brand.csv` | OK | Matched |
| 3 | Brands not compared: no Big4 price / not in Part D pricing file | 7 / 3 | `top100_brand.csv` | OK | Matched |
| 4 | Brands where VA Big4 is above Part D | 9 (Eliquis, Enbrel, Entresto, Farxiga, Fiasp, Januvia, Jardiance, Tresiba, Xarelto) | `top100_brand.csv` | OK | Matched |
| 5 | Of those 9, drugs with 2026 negotiated prices | 8 (all but Tresiba) | CMS MFP data file | OK | Matched |
| 6 | Median brand, VA Big4 vs Part D | 27.1% lower | `top100_brand.csv` | OK | Matched |
| 7 | Per-NDC VA Big4 package price (current Nov 1, 2026) | every compared NDC (414) | `top100_ndc.csv` | OK, recomputed from the xlsx | Matched all 514 NDC rows |
| 8 | Per-NDC Part D median unit cost (30-day) | every compared NDC | `top100_ndc.csv` | OK, recomputed from raw pricing file | Matched |
| 9 | Per-brand VA vs Part D medians | 90 values | `top100_brand.csv` | OK | Matched. Enbrel has since moved from +130.0% to +131.4% (M10); the agent computed +131.4% for this case |
| 10 | Negotiated drugs, VA vs Part D: Enbrel +131%, Januvia +127%, Farxiga +105%, Xarelto +101%, Entresto +65%, Jardiance +54%, Eliquis +38%, Fiasp +2% | | `top100_brand.csv` | OK | Matched (Enbrel as in row 9) |
| 11 | Basket, all priced brands: Part D $112.46B, VA $100.26B, VA 10.8% lower | 89 brands | `basket.csv` | OK, rows recomputed from raw annual and 2026 Q1 files | Part D total matched exactly. VA total by its own row matching: $100.23B (10.87% lower), before M10 |
| 12 | Basket, negotiated drugs: Part D $22.00B, VA $35.69B, VA 62.2% higher | 9 brands (NovoLog Mix rows excluded, M9) | `basket.csv` | OK | Matched before M9 and M10 ($22.08B, $35.73B); new values not re-checked independently |
| 13 | Basket, all other brands: Part D $90.45B, VA $64.57B, VA 28.6% lower | 80 brands plus the NovoLog Mix rows | `basket.csv` | OK | Its row matching gave a figure 0.02 points different, before M9 |
| 14 | Basket gap, VA minus Part D: Eliquis $3.67B, Xarelto $2.52B, Jardiance $2.36B, Farxiga $1.94B, Enbrel $1.36B, Januvia $1.10B, Entresto $0.84B | | `basket.csv` | OK | Not checked separately |
| 15 | Part D unit price vs CMS per-unit negotiated price | Equal (within 4-decimal rounding) for every compared NDC of the negotiated drugs; none above it | `tieout_claude.csv` | OK. Replaces an earlier check that divided the 30-day fact-sheet price by a tablet count, which was wrong | Found this: Part D medians equal CMS's per-unit file to 4 decimals |
| 16 | 30-day chart (`dist/negotiated-30day.html`): Part D / VA per 30-day supply. Januvia $113 / $257, Farxiga $179 / $366, Xarelto $197 / $396, Entresto $295 / $488, Jardiance $197 / $303, Eliquis $231 / $319, Fiasp $119 / $122, NovoLog $119 / $83, Enbrel $2,355 / $5,449 | 9 drugs | `scripts/viz30.py` | OK: Part D equals CMS 30-day negotiated price; VA recomputed from the xlsx Big4 x CMS 30-day units, median across packages | Not checked (built after the independent tie-out) |

## Method checks

| # | Check | Result |
|---|---|---|
| M1 | No top-100 brand name is duplicated across `Overall` rows in the annual or 2026 Q1 CMS files (71 and 74 names are duplicated elsewhere) | OK |
| M2 | Package quantities, all 414 NDCs with both prices: count from FDA text, VA package text and the CMS Medicaid rebate file, taking the value two sources agree on | 187 agreed by 3 sources, 225 by 2; 2 (Enbrel 4-syringe cartons) by NADAC tie-break, consistent with CMS's negotiated price (4 mL x $583.6 = $2,334 vs $2,355 per 30 days). Independent: no unit errors; checked labels for insulins, GLP-1 pens, Enbrel, inhalers, Respimat, Ellipta and eye drops |
| M3 | Error found and fixed: Wegovy 1.7 mg pen (00169-4517-14). FDA lists 0.5 mL per pen; VA and CMS show 0.75 mL. Was VA +20% vs Part D, now about -20%. Wegovy brand median unchanged (-21.5%); brand max now -18.4% | Fixed |
| M4 | FDA package text wrong for Kerendia 50419-540-06 (10 tablets vs 30 per VA and CMS) | Fixed by the three-source rule |
| M5 | Two-strip Ellipta per blister (30-dose = 60) and Respimat 4 g per cartridge | Supported: CMS Medicaid rebate file units per package (Breo, Trelegy, Anoro 30-dose = 60 EA; Respimat = 4 GM) |
| M6 | The vote can lock in a shared error: Invega Trinza FDA and VA both say 1 mL (real 0.875 to 2.625 mL) | Found by independent tie-out. Trinza is not priced per unit (kit rule); basket uses the Invega median. Disclosed in DATASETS.md |
| M7 | Low VA prices on Toujeo (VA Big4 0.25x NADAC) and Alvesco (0.23-0.26x), Alphagan P | Package counts agreed by two sources; independent tie-out checked labels and also judged them real. Prices taken as published. Not explained |
| M8 | Brand vs generic cross-check with Drugs@FDA (added November 9) | CMS rows whose exact name Drugs@FDA lists only under ANDAs are dropped: Klor-Con M10, M15, M20, Ery-Tab, E.E.S. 200 and 400, Dexedrine. Klor-Con stays at rank 85 (no Big4 price). No brand enters or leaves the top 100. All 414 compared NDCs trace to an NDA (342) or BLA (72) |
| M9 | NovoLog Mix 70/30 is not on CMS's negotiated list (no MFP row) | Error found and fixed: its basket rows ($75M Part D) were counted as negotiated; now counted with other brands |
| M10 | Unit check dropped an Enbrel 25 mg vial with no NADAC, by comparing to Part D (which is capped at the negotiated price) | Found by independent tie-out. Fixed: Part D is the fallback benchmark only when the count rests on one source. 414 NDCs now compared; Enbrel +131.4% |
| M11 | Kit rule drops Invega Sustenna, Invega Trinza, Abilify Maintena from per-unit pricing; basket uses brand medians ($3.21B, 2.9% of the basket) | Found by independent tie-out (its direct estimates: about -25% to -26% and -27%, vs medians used of -25.2% and -23.2%). Kept and disclosed |

## Claims (words)

| # | Claim | Source | Status |
|---|---|---|---|
| W1 | Negotiated prices apply to people in Part D or Medicare Advantage drug plans (and Part B for provider-given drugs); the VA is not in the definition | 42 U.S.C. 1320f(c)(2), https://www.law.cornell.edu/uscode/text/42/1320f | Supported (read by Claude) |
| W2 | 2026 negotiated prices per 30-day supply: Januvia $113, Fiasp/NovoLog $119, Farxiga $178.50, Enbrel $2,355, Jardiance $197, Stelara $4,695, Xarelto $197, Eliquis $231, Entresto $295, Imbruvica $9,319 | CMS fact sheet, https://www.cms.gov/files/document/fact-sheet-negotiated-prices-initial-price-applicability-year-2026.pdf | Supported (read by Claude; independent agent also supported) |
| W2a | Negotiated price per unit (for example Eliquis $4.145 per tablet in 2026, $4.257 from January 1, 2027) | CMS MFP data file, November 2, 2026 (DATASETS.md) | Supported (read by Claude from the file) |
| W3 | VA told manufacturers that negotiated-price sales count in 2027 non-FAMP (due November 2026) | VA Supplemental Dear Manufacturer Letter, October 1, 2025, https://www.va.gov/opal/docs/nac/fss/pl2025supplementaldml.pdf | Supported (read by Claude) |
| W4 | The IRA did not amend VA, DoD or FSS pricing law | P.L. 117-169 text | Checked by research agent only; Claude has not read the full act |
| W5 | KFF (December 19, 2024) found Big4 prices above the negotiated price for all 10 drugs | https://www.healthsystemtracker.org/brief/how-medicare-negotiated-drug-prices-compare-to-other-countries/ | Supported (read by Claude): "Big Four drug prices were higher than the new Medicare negotiated prices for all 10 drugs." The article also notes Big4 agencies can pay less through temporary discounts or bulk purchase orders. |
| W6 | H.R. 8667 (MISSION Rx Act, May 7, 2026) would cap Big4 at the negotiated price | https://www.govinfo.gov/content/pkg/BILLS-119hr8667ih/xhtml/BILLS-119hr8667ih.html | Supported (read by Claude): new 38 U.S.C. 8126(j) bars a master-agreement maximum price "exceeding the maximum fair price" while the drug is in the program. Introduced May 7, 2026. Committee status not checked. |
| W7 | Part D unit costs exclude dispensing fees and most rebates (net only of point-of-sale rebates); for negotiated drugs CMS checks unit cost does not exceed the negotiated price | SPUF record layout and CY 2026 Pricing Data Guidelines (URLs in DATASETS.md) | Supported (documentation agent and independent agent read sources; Claude has not read them directly). Confirmed in the data: Part D unit cost equals the negotiated price per unit (row 15) |
| W8 | Big4 is a ceiling; VA can pay less through national contracts or temporary price reductions | VA FSS page; KFF note | Supported |
| W9 | The 2026 negotiated drugs were not simply the 10 highest-spending Part D drugs. They were the 10 highest by Part D spending among drugs that qualified: at least 7 years since FDA approval (11 years for a biologic), no generic or biosimilar of the drug approved and marketed, minus certain orphan drugs, drugs with less than $200 million in Medicare spending, plasma-derived products, and small biotech drugs | 42 U.S.C. 1320f-1(a)(1), (d)(1)(A), (d)(2), (e)(1)(A)(iii), (e)(1)(B)(iii), (e)(3), https://www.law.cornell.edu/uscode/text/42/1320f-1 ; CMS fact sheet "Selected Drugs for Initial Price Applicability Year 2026," August 2023, https://www.cms.gov/files/document/fact-sheet-medicare-selected-drug-negotiation-list-ipay-2026.pdf (local copy `data/raw/cms_selected/`) | Supported. Statute read by a research agent (verbatim quotes); fact sheet text read by Claude. Fact sheet: CMS selected "the 10 drugs with the highest total Part D gross covered prescription drug costs" after steps 1 to 3 above, also excluding biologics qualifying for the biosimilar delay (zero drugs affected for 2026). Four drugs qualified for the small biotech exception. The orphan exclusion was amended in 2025 per the agent's page summary; not verified, and it does not affect the 2026 list |
| W10 | Spending period used for 2026 selection: June 1, 2022 to May 31, 2023 (Part D gross covered prescription drug costs) | CMS fact sheet, above; statute (e)(3)(B) uses the same dates for the low-spend test | Supported (read by Claude) |
| W11 | Enbrel in the selection period: $2,791,105,000 in Part D gross covered prescription drug costs, about 48,000 Part D enrollees (7th of the 10 by spending). All 10 drugs: $50.5 billion, about 20% of Part D gross costs, about 8,247,000 enrollees | CMS fact sheet, above | Supported (read by Claude) |
| W12 | Enbrel has two FDA-licensed biosimilars, Erelzi (Sandoz, BLA 761042) and Eticovo (Samsung Bioepis, BLA 761066); neither appears in the 2024 Part D spending file | Drugs@FDA (DATASETS.md); annual Part D Spending by Drug 2024 | Supported (data). Why they are not marketed (patents, said to run to 2029) is not verified |

## Could not check (independent tie-out)

- The annual Part D spending file's exact release date (documents are dated June 3, 2026).
- Whether FDA keeps an archive of past NDC Directory files.
- Any published definition of the VA file's `Covered` and `PrimeVendor` columns (not used).
- License statements other than the Medicaid rebate file's.
