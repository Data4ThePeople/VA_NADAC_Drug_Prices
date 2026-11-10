# Datasets

What this project compares: the price the VA pays for common brand-name drugs (the Big4 contract price)
against the price Medicare Part D plans pay pharmacies for the same drugs. The focus is the drugs with
Medicare negotiated prices starting January 1, 2026.

Raw files live in `data/raw/` (not in git). Built files live in `data/work/`. The method is at the end.

## VA pharmaceutical price list (VA National Acquisition Center)

**What it is.** Every FSS, Big4 and National Contract (NC) price on VA National Acquisition Center
contracts. One row is one contract, one NDC package and one price type. 43,206 rows; FSS 30,443,
Big4 10,853, NC 1,910.
- FSS: multi-year contracts any federal agency can use, with prices "negotiated based on how vendors do
  business with their commercial customers."
- Big4: the statutory price for VA, Defense, the Public Health Service (including the Indian Health
  Service) and the Coast Guard, set by Public Law 102-585 and 38 U.S.C. 8126. By law it may not exceed
  76% of the non-Federal average manufacturer price (non-FAMP), less an additional discount when the
  non-FAMP rises faster than inflation. The VA's 2027 guidance says the Federal Ceiling Price is the lower
  of that calculation and the September 30 FSS price raised by inflation.
- NC: national contracts that trade a volume commitment for prices below FSS.
Sources: FSS page https://department.va.gov/procurement-acquisition-and-logistics/national-acquisition-center/federal-supply-schedule-service/ ;
38 U.S.C. 8126 https://www.law.cornell.edu/uscode/text/38/8126 ;
2026-2027 Dear Manufacturer Letter https://department.va.gov/procurement-acquisition-and-logistics/wp-content/uploads/sites/56/2026/10/2026-2027FCP_Final-Annual-DML.pdf

**Where it comes from.** https://department.va.gov/procurement-acquisition-and-logistics/wp-content/uploads/sites/56/2026/11/TPharmPrices-11-01-2026.xlsx ,
linked from the FSS page. Excel, one sheet ("Prices"), 3.8 MB, no login. Local:
`data/raw/va/TPharmPrices-11-01-2026.xlsx`, converted to `data/raw/va/va_2026-11-01.csv`.

**Version and vintage.** Labeled "as of 11/01/2026." The VA updates the file around the 2nd and 16th of
each month. Federal Ceiling Prices are recalculated each year and take effect January 1. Past files are
in the VA FOIA library.

**Coverage.** All NAC programs, FSS and National Contracts. We use Big4 prices that are current on
November 1, 2026 (start date on or before, stop date on or after).

**Changes over time.** No publisher notes on layout changes were found. We use one file only.

**Suppressed, censored or masked values.** None documented.

**Missing data.** No codes documented. `SubItemIdentifier` is blank on every row; `VAClass` is blank on
35 rows. Some rows carry placeholder prices of $0.01; we drop prices of $0.01 or less.

**Revisions.** The VA flagged possible errors in the January to March 2019 files and posted corrected
files. No policy on restating later files was found. We pin the November 1, 2026 file.

**Units and rounding.** `Price` is per package (this is not stated by the VA; we read it from the
`PackageDescription` column, which holds the package size). Two decimals. `PackageDescription` is free
text: plain counts ("30"), unit-dose counts ("100UD"), multiples ("3X10", "5X3ML") and sizes ("18GM").
For some devices it says "1" for one inhaler.

**Known quirks.**
- The same NDC can appear on several rows (several contracts and price types). We take the lowest
  current Big4 price per NDC.
- `Covered` and `PrimeVendor` have no published definition. We do not use them.
- Big4 is a ceiling. The VA can pay less through national contracts or temporary price reductions. KFF
  also notes that the Big4 agencies can pay less through bulk purchase orders. The file has no
  temporary-price-reduction column.
- The VA counts Medicare negotiated-price sales as commercial sales in the non-FAMP that sets the 2027
  ceiling (Supplemental Dear Manufacturer Letter, October 1, 2025,
  https://www.va.gov/opal/docs/nac/fss/pl2025supplementaldml.pdf). That may lower 2027 Big4 prices for
  the negotiated drugs. How much is not known.

**Uncertainty.** None published.

**License and attribution.** No license stated. Federal government work. Credit: U.S. Department of
Veterans Affairs, National Acquisition Center.

## Medicare Part D plan pricing file (CMS)

**What it is.** The pricing table of the Quarterly Prescription Drug Plan Formulary, Pharmacy Network,
and Pricing Information files. One row is one plan (contract, plan, segment), one NDC and one days
supply. `UNIT_COST` is the "average unit cost (e.g. per pill) for the specified days supply at in-area
retail pharmacies." 5,496 plans and 6,170 NDCs in the 2026 Q3 file.
Sources: methodology https://data.cms.gov/sites/default/files/2025-10/cf6b8476-ca42-48c6-9fc4-281b08c6ea87/Methodology-SPUF-2026.pdf ;
record layout https://data.cms.gov/sites/default/files/2025-10/83da019f-fa24-483e-87de-cc089780a6a5/SPUFRecordLayout-2026.pdf ;
CY 2026 Pricing Data Guidelines https://www.cms.gov/files/zip/2026-pricing-data-guidelines-calendar.zip

**Where it comes from.** https://data.cms.gov/sites/default/files/2026-10/062e9434-ed9d-4e83-abbd-4d64eb375949/SPUF_2026_20261007.zip
(2.5 GB zip, pipe-delimited text, no login). We use only `pricing file PPUF_2026Q3.txt` (2.0 GB), at
`data/raw/spuf_2026q3/ex/`. Fields: `CONTRACT_ID`, `PLAN_ID`, `SEGMENT_ID`, `NDC`, `DAYS_SUPPLY`,
`UNIT_COST`.

**Version and vintage.** Quarterly. The 2026 Q3 file was posted October 7, 2026 and is built from the
first Medicare Plan Finder posting in the last month of the quarter. Plan Finder updates every two weeks,
so the file can differ from what Plan Finder shows today. Each file is a snapshot.

**Coverage.** Stand-alone drug plans and Medicare Advantage drug plans. Excludes non-Part D plans,
National PACE, employer plans and demonstrations (Medicare-Medicaid plans are included). Plans whose data CMS
suppressed (`PLAN_SUPPRESSED_YN` = Y in the plan file) are not in the pricing file. Retail pharmacies
in the plan's area only; long-term care, home infusion, limited-access and mail order are out.

**Changes over time.** New for 2026: a negotiated-drug flag in the formulary file and separate dispensing
fees for negotiated drugs in the pharmacy network file. We use one quarter only.

**Suppressed, censored or masked values.** Suppressed plans are left out entirely, as above.

**Missing data.** Not documented for the pricing file. A $0 unit cost is a real $0.

**Revisions.** No restatement policy found. We pin the 2026 Q3 file.

**Units and rounding.** Per unit. CMS tells plans to use the NCPDP billing unit, but also says a unit
"can be defined in several ways, such as one vial, syringe, or 1MG." In the data the unit matches
NADAC's billing unit (each, mL or gram): per tablet, per mL of insulin, per gram for a metered-dose
inhaler. For the negotiated drugs, the Part D median unit cost equals CMS's published negotiated price
per unit for every compared NDC (CMS negotiated price file, below). Four decimals. `UNIT_COST` excludes
the dispensing fee. It is net of
rebates only when a plan applies them at the point of sale; other rebates are not reflected. For the
2026 negotiated drugs, CMS checks that the unit cost does not exceed the negotiated price.

**Known quirks.**
- Plans price one "related NDC" per drug, strength and form, which CMS assigns. Other NDCs of the same
  product are not in the file. When our NDC is missing, we use the median over packages of the same
  product (same first 9 NDC digits).
- `DAYS_SUPPLY` is 30, 60 or 90. We use 30.
- CMS's validation checks "are not statements of the levels of permissible error."

**Uncertainty.** None published.

**License and attribution.** U.S. government work (https://www.usa.gov/government-works). The CMS
Agreement for Use asks users not to present the data in an inaccurate or misleading way. Credit: Centers
for Medicare & Medicaid Services.

## Medicare Part D Spending by Drug, annual, 2024 (CMS)

**What it is.** Part D claims, dosage units and gross spending by brand name and generic name, with one
row per manufacturer and an `Overall` row across manufacturers. Built from Part D prescription drug event
records. Wide columns for 2020 to 2024.
Sources: methodology https://data.cms.gov/sites/default/files/2026-06/d7e0a571-9d08-40ec-8278-1b2300f59424/DSD_PTD_RY26_20260603_Methodology_WDDSE_508.pdf ;
data dictionary https://data.cms.gov/sites/default/files/2026-06/Medicare%20Part%20D%20Spending%20by%20Drug%20Data%20Dictionary%2020260603_508.pdf

**Where it comes from.** https://data.cms.gov/sites/default/files/2026-06/98218f98-166c-4723-8438-c344a4ef96a6/DSD_PTD_RY26_P04_V10_DY24_BGM.csv
(CSV, 5.3 MB, no login). Local: `data/raw/partd_spending_2024/`. Fields used: `Brnd_Name`,
`Gnrc_Name`, `Mftr_Name`, `Tot_Clms_2024`.

**Version and vintage.** Annual. This release (June 2026; documents dated June 3, 2026) covers calendar
2024.

**Coverage.** Part D enrollees, about 81% of Medicare beneficiaries. Excludes over-the-counter drugs and
drugs with fewer than 11 claims.

**Changes over time.** We use 2024 only.

**Suppressed, censored or masked values.** Drugs with fewer than 11 claims are left out. Beneficiary
counts are blank on 782 rows that have claims; the rule is not documented. One top-100 row (Tivicay Pd)
has a blank beneficiary count. We do not use beneficiary counts.

**Missing data.** No codes documented; blanks as above.

**Revisions.** Each release rebuilds the five-year window. Whether past values change is not stated. We
pin this release.

**Units and rounding.** `Tot_Spndng` is gross drug cost: ingredient cost, dispensing fees, sales tax and
vaccine administration fees, paid by plans and enrollees. It does not include manufacturer rebates,
which CMS may not disclose.

**Known quirks.**
- `Brnd_Name` holds generic names too when a drug has no trademark name (for example "Clopidogrel").
  That is why we test brand status against FDA.
- Some brand-style names are generics approved under ANDAs (for example Klor-Con M10, M15 and M20,
  Ery-Tab, Dexedrine). We drop those rows using Drugs@FDA (see Method).
- 71 brand names appear on more than one `Overall` row with different generic names. None is in the
  top 100.
- An asterisk on a name means its spending mixes routes of administration (for example "Premarin*").

**Uncertainty.** An outlier flag marks drugs whose average spending per unit is strongly affected by
outlier records. We do not use spending per unit from this file.

**License and attribution.** U.S. government work. Credit: Centers for Medicare & Medicaid Services.

## Medicare Quarterly Part D Spending by Drug, 2026 Q1 (CMS)

**What it is.** Part D claims and gross spending by brand and generic name, for full-year 2025 and for
2026 Q1, with `Overall` rows across manufacturers. No dosage units.
Sources: methodology https://data.cms.gov/sites/default/files/2026-07/QDD_PTD_RQ2603_Methodology_20260716_508.pdf ;
data dictionary https://data.cms.gov/sites/default/files/2025-12/08c80ec8-e57c-4a2c-9470-5ff26e76dace/Medicare%20Quarterly%20Part%20D%20Spending%20by%20Drug%20Data%20Dictionary%20508.pdf

**Where it comes from.** https://data.cms.gov/sites/default/files/2026-07/QDD_PTD_RQ2603_P01_V10_DQT2601_20260708.csv
(CSV, 31 MB, no login). Local: `data/raw/partd_spending_2026q1/`. Fields used: `Brnd_Name`, `Mftr_Name`,
`Year` ("2026 (Q1)"), `Avg_Spnd_Per_Clm`.

**Version and vintage.** Quarterly, released July 2026.

**Coverage.** Same scope as the annual file. CMS gives Part D enrollees as about 82% of Medicare
beneficiaries here (81% in the annual methodology). Claims whose NDC does not match First Databank
MedKnowledge, a commercial drug database CMS uses, are excluded.

**Changes over time.** From July 2026, CMS pulls claims three months after the quarter ends.

**Suppressed, censored or masked values.** Drugs with fewer than 11 claims are left out. Beneficiary
counts are blank on 1,360 rows; rule not documented.

**Missing data.** No codes documented.

**Revisions.** Preliminary. Values "may change with each new release due to claims lag." CMS says the
three-month pull captures over 99% of records, but also that 84% of records are fully mature at three
months (88% at six), with payment details not final. It advises caution when comparing the quarterly
and annual files. We pin this release.

**Units and rounding.** Same spending definition as the annual file (includes dispensing fees and sales
tax, excludes rebates). The documentation does not say whether 2026 spending reflects negotiated prices.
The data shows it does: Eliquis spending per claim fell from $912 in 2025 to $399 in 2026 Q1.

**Known quirks.** 74 brand names appear on more than one `Overall` row; none is in our basket. Five
basket rows have no 2026 Q1 row (Humalog Mix 50-50, Repatha Pushtronex, Premarin*, Tivicay Pd, Abilify
Mycite) and are left out of the basket.

**Uncertainty.** Claims maturity as above. Nothing else published.

**License and attribution.** U.S. government work. Credit: Centers for Medicare & Medicaid Services.

## National Drug Code Directory (FDA)

**What it is.** FDA's listing of drug products (`product.txt`) and packages (`package.txt`), as
submitted by labelers. FDA has not verified the contents, and an NDC does not mean FDA approval.
Sources: https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory ;
product fields https://www.fda.gov/drugs/drug-approvals-and-databases/ndc-product-file-definitions ;
package fields https://www.fda.gov/drugs/drug-approvals-and-databases/ndc-package-file-definitions

**Where it comes from.** https://www.accessdata.fda.gov/cder/ndctext.zip (11 MB zip of tab-delimited
text, no login). Local: `data/raw/fda_ndc/`. Fields used: `PROPRIETARYNAME`, `NONPROPRIETARYNAME`,
`SUBSTANCENAME`, `MARKETINGCATEGORYNAME`, `APPLICATIONNUMBER`, `PRODUCTTYPENAME`, `DOSAGEFORMNAME`,
`NDCPACKAGECODE`, `PACKAGEDESCRIPTION`.

**Version and vintage.** Updated daily. Our copy's files are dated November 6, 2026 (a download on
November 9 had newer files; the independent tie-out used that one and got the same results). We found no
archive of past versions.

**Coverage.** Finished, marketed products, prescription and over the counter (Humulin R, N and 70/30 are
listed as over the counter). Excludes discontinued and inactive listings (those are in a separate file),
unfinished products and drugs sold only inside kits. A VA NDC missing from this file is
priced from the other package sources.

**Changes over time.** Not applicable; one download.

**Suppressed, censored or masked values.** None.

**Missing data.** Blank fields where a labeler did not supply them.

**Revisions.** Listings change as labelers update them; no history is kept.

**Units and rounding.** `NDCPACKAGECODE` is a 10-digit code with dashes (for example 0169-4517-14). We
convert it to the 11-digit form used by CMS and the VA by padding each part to 5, 4 and 2 digits. `PACKAGEDESCRIPTION` gives nested counts and sizes, for
example "4 SYRINGE in 1 CARTON / .75 mL in 1 SYRINGE."

**Known quirks.**
- Package text can be wrong. Wegovy 1.7 mg (0169-4517-14) is listed at 0.5 mL per pen; the product is
  0.75 mL, as the VA and CMS show. Kerendia 50419-540-06 is listed as 10 tablets; the VA and CMS show 30.
  This is why package counts are checked against three sources (see Method).
- Two-strip Ellipta inhalers list doses, not blisters.
- Respimat cartridges list puffs, not grams.

**Uncertainty.** None published.

**License and attribution.** Public domain. Credit to FDA appreciated.

## Medicaid Drug Rebate Program drug product file (CMS)

**What it is.** CMS's list of covered outpatient drug NDCs with unit type and "units per package size,"
the total units in the smallest dispensable amount.

**Where it comes from.** https://download.medicaid.gov/data/drugproducts-q2-2026.csv (CSV, 330 MB, no
login), from data.medicaid.gov dataset 0ad65fe5-3ad3-5d79-a3f9-7893ded7963a. Local: `data/raw/mdrp/`.
Fields used: `NDC`, `Year`, `Quarter`, `Unit Type`, `Units Per Pkg Size` (latest quarter per NDC).

**Version and vintage.** Quarterly; 2026 Q2 was the latest posted on November 9, 2026 (a Q3 file was
not yet at the expected address).

**Coverage.** Drugs from manufacturers in the Medicaid rebate program. 413 of the 414 compared NDCs
appear.

**Changes over time.** Rows repeat by quarter; we take the latest row per NDC.

**Suppressed, censored or masked values.** None.

**Missing data.** None in the fields we use.

**Revisions.** Manufacturers update their own entries.

**Units and rounding.** The data dictionary lists 8 unit types (AHF, CAP, SUP, GM, ML, TAB, TDP, EA);
the data also holds MCI. We use EA, ML and GM, and treat TAB and CAP as EA.

**Known quirks.** For tablets and capsules, `Units Per Pkg Size` is often 1 regardless of the bottle
count, so a 1 for an EA item is not used. For some multi-pen cartons it gives the volume of one pen
(for example 1 mL for a carton of five 3 mL Lantus pens, or 1 mL for four 1 mL Enbrel syringes). It
counts a 30-dose two-strip Ellipta inhaler as 60 EA and a Respimat cartridge as 4 GM.

**Uncertainty.** None published.

**License and attribution.** U.S. government work. Credit: Centers for Medicare & Medicaid Services.

## NADAC, 2026 (CMS)

**What it is.** National Average Drug Acquisition Cost: CMS's survey-based average of what retail
pharmacies pay for drugs, per billing unit, one row per NDC per weekly release.
Sources: methodology https://www.medicaid.gov/medicaid-chip-program-information/by-topics/prescription-drugs/ful-nadac-downloads/nadacmethodology.pdf ;
FAQ https://www.medicaid.gov/medicaid-chip-program-information/by-topics/prescription-drugs/ful-nadac-downloads/nadacqa.pdf

**Where it comes from.** https://data.medicaid.gov/api/1/datastore/query/fbb83258-11c7-47f5-8b18-5f8e79f7e704/0/download?format=csv
(CSV, 118 MB, no login). Local: `data/raw/nadac/`. Fields used: `NDC`, `Pricing Unit`, `NADAC Per Unit`,
`Effective Date` (latest row per NDC).

**Version and vintage.** Weekly; the 2026 file holds 44 weekly releases, January 7 to November 4, 2026.

**Coverage.** Covered outpatient drugs bought by retail community pharmacies. Not every NDC has a NADAC.

**Changes over time.** Not relevant to our use.

**Suppressed, censored or masked values.** A rate needs at least five cost observations.

**Missing data.** NDCs without a rate are simply absent.

**Revisions.** A rate carries forward until changed, for up to 12 months; then it is removed.

**Units and rounding.** `Pricing Unit` is EA, ML or GM. Five decimals. Ingredient cost only.

**Known quirks.** We do not use NADAC prices in the comparison. We use NADAC for each NDC's billing unit
and as a check on VA unit prices (see Method).

**Uncertainty.** CMS reports that 99.3% of brand rates have a margin of error under 5%.

**License and attribution.** Public domain. Credit: Centers for Medicare & Medicaid Services.

## Drugs@FDA (FDA)

**What it is.** FDA's database of approved drug applications: one row per application in
`Applications.txt` (type NDA, ANDA or BLA) and one row per approved product in `Products.txt` (drug name,
form, strength). An NDA or BLA is the application for a brand (or reference) product; an ANDA is a
generic.
Source: https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files

**Where it comes from.** https://www.fda.gov/media/89850/download (zip of tab-delimited text, no login).
Local: `data/raw/drugsatfda/ex/`. Fields used: `ApplNo`, `ApplType`, `DrugName`.

**Version and vintage.** Updated weekly. Files dated November 6, 2026, downloaded November 9, 2026.

**Coverage.** Drugs approved by FDA's Center for Drug Evaluation and Research, including the biologics
it regulates (insulins, etanercept).

**Changes over time.** Not applicable; one download.

**Suppressed, censored or masked values.** None.

**Missing data.** Not documented.

**Revisions.** Not documented; the files are replaced each week.

**Units and rounding.** Not applicable.

**Known quirks.** CMS brand names are often shortened, so only about three in four CMS brand rows near
the top 100 match a Drugs@FDA drug name exactly. Rows with no exact match are kept and checked at the
package level instead (see Method).

**Uncertainty.** None published.

**License and attribution.** Not checked. Federal government work. Credit: U.S. Food and Drug
Administration.

## Medicare negotiated price (MFP) data file (CMS)

**What it is.** CMS's list of the NDCs of each drug with a Medicare negotiated price ("maximum fair
price"), with the price per 30-day supply and per unit for each 9-digit NDC product and each effective
period. Used only to check the Part D prices (Claude tie-out).

**Where it comes from.** https://www.cms.gov/files/zip/cms-negotiation-program-selected-drug-list-maximum-fair-price-data-file-20261102.zip
(zip with CSV and Excel, no login). Local: `data/raw/cms_mfp/ex/`. Fields used: `NDC-9`, `MFP Effective
Date`, `MFP End Date`, `NDC-9 MFP per Unit Price`.

**Version and vintage.** Dated November 2, 2026. Holds 2026 prices and the inflation-adjusted prices that
start January 1, 2027.

**Coverage.** The 2026 drugs (Eliquis, Enbrel, Entresto, Farxiga, Imbruvica, Januvia, Jardiance,
NovoLog/Fiasp, Stelara, Xarelto) and later years' drugs. NovoLog Mix 70/30 is not on the list.

**Changes over time.** Rows are end-dated when a price changes; we use rows in effect on November 1, 2026.

**Suppressed, censored or masked values.** None.

**Missing data.** None in the fields we use.

**Revisions.** Each posting replaces the last.

**Units and rounding.** Per unit price has six decimals.

**Known quirks.** The per-unit price is not the 30-day price divided by a typical tablet count (Eliquis
is $4.145 per tablet, not $231 / 60 = $3.85).

**Uncertainty.** None.

**License and attribution.** Not checked. U.S. government work. Credit: Centers for Medicare & Medicaid
Services.

## Method

Scripts, run in order from the project root: `scripts/top100.py`, `scripts/basket.py`,
`scripts/tieout.py`. Python virtual environment `.venv` with `duckdb`, `pandas`, `openpyxl`.

### Which drugs: top 100 brands by 2024 Part D claims

1. Take the `Overall` rows of the 2024 annual spending file. Each row already totals claims across all
   NDCs and package sizes of that brand name.
2. Group rows into brand families by the first word of `Brnd_Name`, letters only, with hyphens, slashes
   and other symbols treated as spaces (Lantus and Lantus Solostar are one brand; Klor-Con is "klor").
   Each family is counted once.
3. Keep a row only if it is a brand:
   - the first word of `Brnd_Name` differs from the first word of `Gnrc_Name` (first words only;
     comparing full names would let 8 generics into the top 100);
   - the FDA NDC Directory lists a prescription product whose name starts with that word under an NDA or
     BLA, and whose first word differs from its generic name's first word;
   - those FDA products' active ingredients include the first word of the CMS generic name; and
   - Drugs@FDA does not list that exact drug name only under ANDAs. This drops Klor-Con M10, M15 and M20,
     Ery-Tab, E.E.S. 200 and 400, and Dexedrine. Klor-Con stays in the top 100 on its NDA products.
4. Rank families by total 2024 claims and keep the top 100.

### Per-unit prices (`scripts/top100.py`)

1. **NDCs for each brand:** FDA package NDCs of the brand's NDA/BLA products, plus VA NDCs whose
   `TradeName` starts with the brand name. Kits and starter, titration or initiation packs are dropped.
   FDA lists the long-acting injections Invega Sustenna, Invega Trinza and Abilify Maintena as kits
   (syringe plus needles), so they are not priced per unit; see the basket for how they are handled.
   Every compared NDC must trace to an NDA or BLA in Drugs@FDA, through the NDC Directory's application
   number. Result: 342 NDA, 72 BLA. Two Humulin R packages are no longer in the NDC Directory; Drugs@FDA
   lists every Humulin R product under Lilly's BLA 018780.
2. **VA price:** lowest current Big4 price per NDC (current on November 1, 2026; above $0.01).
3. **Part D price:** median `UNIT_COST` across plans for a 30-day supply, for the exact NDC, or, if the
   NDC is not in the file, the median across packages of the same product (first 9 digits).
4. **Billing unit:** NADAC's `Pricing Unit` for the NDC; if NADAC has none, the rebate file's unit type.
5. **Package quantity in that unit,** from three independent sources:
   - FDA package text (counts multiplied through; total mL or grams for ML and GM). Two rules: two-strip
     Ellipta inhalers (Breo, Anoro, Trelegy) count two blisters per dose; Respimat cartridges with 60 or
     120 puffs count 4 grams (10-puff samples are dropped).
   - VA `PackageDescription`, read in the billing unit ("30", "100UD", "3X10", "5X3ML", "18GM"; for
     single-use vials billed each, "30X0.4ML" is 30). A plain count with no size ("4") is read only for
     EA products; for mL and gram products it gives no value.
   - CMS rebate file units per package, when its unit type matches (a 1 for an EA item is not used).
   The quantity used is the value at least two sources agree on (within 1%). If only one source has a
   value, that value is used. If the sources disagree with no majority, the value that puts the VA Big4
   unit price between 0.3 and 1.1 times NADAC is used, when exactly one does; otherwise the NDC is dropped.
   Result for the 414 NDCs with both a Big4 and a Part D price: 187 agreed by all three sources, 225 by
   two, and 2 (Enbrel 4-syringe cartons, 4 mL) set by the NADAC tie-break. The Enbrel count is also
   consistent with CMS's negotiated price: four 1 mL syringes at the Part D unit cost of $583.6 per mL is
   $2,334, against $2,355 for a 30-day supply.
   The vote can lock in a wrong count when two sources make the same error. For Invega Trinza, FDA and the
   VA both show 1 mL, but the products hold 0.875 to 2.625 mL. Trinza is not priced per unit (kit rule).
6. **Unit check:** an NDC is dropped if its VA unit price is more than 2 times or less than 0.2 times its
   NADAC unit price. When NADAC has no rate, the Part D price is used instead, but only if the package
   count rests on one source. A count two sources agree on is not overridden by Part D, because for the
   negotiated drugs Part D is capped at the negotiated price and the check would drop the high VA prices
   being measured. The check drops none of the 414. All 414 NDCs are compared.
7. **Per NDC:** VA vs Part D = (Big4 / quantity) / Part D unit price - 1.
8. **Per brand:** median of that ratio across the brand's NDCs, with the minimum and maximum.

Outputs: `data/work/top100_ndc.csv`, `data/work/top100_brand.csv` (with a `status` column for brands that
could not be compared, and why).

### Basket cost (`scripts/basket.py`)

The basket prices a year of Part D use of the compared brands two ways. It compares two price lists. It
is not an estimate of what Medicare or the VA spends.

1. For each CMS brand row (for example "Spiriva Respimat" and "Spiriva Handihaler" separately):
   **Part D cost** = 2024 claims x 2026 Q1 average spending per claim.
2. **VA cost** = Part D cost x (1 + VA vs Part D ratio), where the ratio is the median over the NDCs that
   match the row:
   - every word after the first in the CMS name, of three or more letters, must appear as a whole word
     in the NDC's VA or FDA name (for example Respimat, Mix, Sustenna, Maintena), except these package
     words, which are ignored: Kwikpen, Flexpen, Flextouch, Solostar, Max, HFA, Pen, Sureclick, Penfill,
     Tempo, Junior, Vial, Inhub, Ellipta, Aerosphere, Pushtouch, Unoready, Syringe, Pak, Pushtronex,
     Diskus, Mini. Words of one or two letters (XR, PD) are ignored;
   - a CMS row with no such word excludes NDCs that carry another row's sub-brand word (plain "Spiriva"
     excludes Respimat NDCs);
   - insulin rows marked U-200, U-300 or U-500 match only NDCs of that strength, and other rows exclude
     concentrated NDCs.
   If no NDC matches, the brand's median ratio is used. Six rows use it: Invega Sustenna and Invega Trinza
   (Invega median, VA 25.2% lower), Abilify Maintena (Abilify median, 23.2% lower), Fiasp Pumpcart,
   Ingrezza Initiation Pk and Austedo XR Titration Kt. Together they are $3.21 billion, 2.9% of the Part D
   basket. The independent tie-out priced the Invega Sustenna and Abilify Maintena packages directly and got
   about 25% to 26% and 27% lower, close to the medians used.
3. Rows with no 2026 Q1 spending row are left out.
4. Totals: all brands, the 2026 negotiated drugs, and all other brands. A row counts as negotiated when
   its drug is on CMS's 2026 list. NovoLog Mix 70/30 rows are not (CMS's drug is insulin aspart, NovoLog
   and Fiasp), so they count with the other brands.

Output: `data/work/basket.csv`.

### 2026 negotiated drugs

Eliquis, Jardiance, Xarelto, Januvia, Farxiga, Entresto, Enbrel, Imbruvica, Stelara, and NovoLog/Fiasp
(insulin aspart). Source: CMS fact sheet,
https://www.cms.gov/files/document/fact-sheet-negotiated-prices-initial-price-applicability-year-2026.pdf .
Imbruvica and Stelara are not in the top 100 by claims.

### Limits

- **Rebates:** Part D prices and spending are before most manufacturer rebates, which are not public.
  For most brands Medicare's net cost is lower than shown, so the VA's advantage on those brands is
  smaller than the comparison shows. For negotiated drugs, the Part D price cannot exceed the negotiated
  price.
- **Big4 is a ceiling:** the VA may pay less on some drugs.
- **Timing:** VA prices as of November 1, 2026; Part D unit prices from 2026 Q3; basket claims from 2024
  and spending per claim from 2026 Q1.
- **Dispensing fees:** the basket's Part D cost per claim includes dispensing fees and sales tax, and the
  VA cost applies an ingredient-price ratio to that total.
- **Coverage:** brands with no current Big4 price, or with no NDC in the Part D pricing file, are not
  compared.
