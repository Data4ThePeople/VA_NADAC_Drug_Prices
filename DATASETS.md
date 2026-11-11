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
(2.5 GB zip, pipe-delimited text, no login). This section covers `pricing file PPUF_2026Q3.txt` (2.0 GB),
at `data/raw/spuf_2026q3/ex/`. Fields: `CONTRACT_ID`, `PLAN_ID`, `SEGMENT_ID`, `NDC`, `DAYS_SUPPLY`,
`UNIT_COST`. The formulary, plan information and beneficiary cost files from the same zip are described
in the next section.

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

## Medicare Part D plan formulary, plan information and beneficiary cost files (CMS)

**What it is.** Three more tables from the same quarterly file as the pricing file above (same zip, same
methodology and record layout).
- `basic drugs formulary file  PPUF_2026Q3.txt`: one row per formulary and covered drug product. Fields
  used: `FORMULARY_ID`, `RXCUI` ("RxNorm concept unique identifier"), `NDC` ("11-digit proxy National Drug
  Code (NDC) associated with the drug product"), `TIER_LEVEL_VALUE` ("Cost share tier level associated
  with the NDC"). 1,129,364 rows, 328 formularies, 6,170 drug products; each product has exactly one proxy
  NDC and one tier per formulary.
- `plan information  PPUF_2026Q3.txt`: one row per plan and county. Fields used: `CONTRACT_ID`,
  `PLAN_ID`, `SEGMENT_ID`, `FORMULARY_ID`, `PREMIUM` ("Monthly premium amount"), `DEDUCTIBLE` ("Annual
  deductible amount"). 5,518 distinct plans (contract-plan-segment).
- `beneficiary cost file  PPUF_2026Q3.txt`: cost sharing by plan, coverage level, tier and days supply.
  Fields used and codes, from the record layout: `COVERAGE_LEVEL` (0 = pre-deductible, 1 = initial
  coverage, 3 = catastrophic), `TIER`, `DAYS_SUPPLY` (1 = 30 days, 2 = 90, 3 = other, 4 = 60),
  `COST_TYPE_PREF` and `COST_TYPE_NONPREF` (preferred and standard retail pharmacies; 0 = not offered,
  1 = copay, 2 = coinsurance), `COST_AMT_PREF` and `COST_AMT_NONPREF` (dollars for a copay; a decimal for
  coinsurance, ".25 is interpreted as 25%"), `TIER_SPECIALTY_YN`, `DED_APPLIES_YN` ("Does the deductible
  apply to this tier?").

**Where it comes from.** Same zip as the pricing file. Local: `data/raw/spuf_2026q3/ex/` (the beneficiary
cost file was extracted November 11, 2026).

**Version and vintage.** 2026 Q3, posted October 7, 2026; same Plan Finder snapshot as the pricing file.

**Coverage.** Same plans as the pricing file. The plan information file lists 5,518 plans; the pricing
file has 5,496. Counts here are of plans, not enrollees; the files have no enrollment.

**Changes over time.** One quarter only.

**Suppressed, censored or masked values.** Suppressed plans are flagged in the plan information file.

**Missing data.** 19 of the 5,295 plans on five- or six-tier formularies have no initial-coverage,
30-day rows in the beneficiary cost file.

**Revisions.** None found. We pin the 2026 Q3 file.

**Units and rounding.** Tiers are numbers only; the files do not name them. The usual Plan Finder labels
are tier 1 preferred generic, 2 generic, 3 preferred brand, 4 non-preferred drug, 5 specialty and 6 select
care. The data fits those labels: tier 5 is flagged as the specialty tier in 96.5% of five-tier plans and
99.1% of six-tier plans, and tier 6 holds low-cost generics (lisinopril, glipizide, atorvastatin) with a
median copay of $0.

**Known quirks.**
- Tier structures vary: of the 5,518 plans, 3,921 use five tiers, 1,374 six, 37 four, 20 seven and 165
  one or two; 1 plan's formulary (00026194) has no rows in the formulary file.
- The formulary lists one proxy NDC per drug product, not every NDC. A product's generic or brand status
  is read from that NDC.

**Uncertainty.** None published.

**License and attribution.** As for the pricing file.

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
`NDCPACKAGECODE`, `PACKAGEDESCRIPTION`. For the generic tier analysis, `MARKETINGCATEGORYNAME` and
`APPLICATIONNUMBER` of each formulary proxy NDC, matched by package code, or by product code (first 9
digits) when the package is no longer listed.

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
- Of the 6,170 formulary proxy NDCs, 6,040 match a listed package and 49 more match a listed product
  by product code. 81 match neither, so their generic or brand status is unknown and they are left out
  of the generic tier analysis.

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
Local: `data/raw/drugsatfda/ex/`. Fields used: `ApplNo`, `ApplType`, `DrugName` (brand check);
`ActiveIngredient`, `Form` from `Products.txt` and `SubmissionType`, `SubmissionStatus`,
`SubmissionStatusDate` from `Submissions.txt` (first generic approval date, generic tier analysis).

**Version and vintage.** Updated weekly. Files dated November 6, 2026, downloaded November 9, 2026.

**Coverage.** Drugs approved by FDA's Center for Drug Evaluation and Research, including the biologics
it regulates (insulins, etanercept).

**Changes over time.** Not applicable; one download.

**Suppressed, censored or masked values.** None.

**Missing data.** Not documented.

**Revisions.** Not documented; the files are replaced each week.

**Units and rounding.** Not applicable.

**Known quirks.**
- CMS brand names are often shortened, so only about three in four CMS brand rows near the top 100 match
  a Drugs@FDA drug name exactly. Rows with no exact match are kept and checked at the package level
  instead (see Method).
- An original approval is a `SubmissionType` of ORIG with status AP. Approval is not the same as the date
  a generic reached the market.

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

## Medicare Trustees Report, 2026 (CMS Office of the Actuary)

**What it is.** The 2026 Annual Report of the Boards of Trustees of the Federal Hospital Insurance and
Federal Supplementary Medical Insurance Trust Funds. We use Table IV.B8, "Key Factors for Part D
Expenditure Estimates" (printed page 150), column "Direct and indirect remuneration," footnote 2:
"Expressed as a percentage of total drug costs." DIR, in the report's glossary: "Payments primarily
consisting of drug manufacturer rebates and pharmacy rebates that Part D plans negotiate." Also Table
IV.B7 (Part D enrollment).
Source: https://www.cms.gov/oact/tr/2026

**Where it comes from.** The URL above serves the full report as a PDF (2.8 MB, no login). Local:
`data/raw/trustees_2026/2026-medicare-trustees-report.pdf`.

**Version and vintage.** 2026 report. 2016 to 2024 are historical data; 2025 onward are intermediate
estimates.

**Coverage.** All Part D drugs, generic and brand. Footnote 76: these are averages across all
prescription drugs, including employer group waiver plans; generics, "about 88 percent of all Part D drugs
dispensed and 12 percent of drug spending in 2025, typically carry little to no rebates."

**Changes over time.** Since January 1, 2024, pharmacy price concessions are applied at the point of sale
(CMS final rule of May 9, 2022) and are no longer in DIR, so 2024 onward is mostly manufacturer rebates.
The Trustees expect negotiated prices and inflation rebates to reduce DIR from 2026.

**Suppressed, censored or masked values.** None. Rebates for individual drugs are not published.

**Missing data.** None in the table.

**Revisions.** Each year's report can restate history and estimates. We pin the 2026 report.

**Units and rounding.** Percent of total drug costs, one decimal.

**Known quirks.** 2025 appears as an estimate in the 2026 report.

**Uncertainty.** The report's high- and low-cost scenarios move the average rebate by 2 percentage points.

**License and attribution.** U.S. government work. Credit: Boards of Trustees, Medicare trust funds.

## VA health care copay rates (VA)

**What it is.** The VA's published copays for outpatient medications: $5 (Tier 1, preferred generic), $8
(Tier 2) and $11 (Tier 3, brand-name) for a 1- to 30-day supply, $700 yearly cap for Priority Groups 2 to
8, and no medication copay for Priority Group 1 and other exempt veterans.
Sources: https://www.va.gov/health-care/copay-rates/ (updated October 26, 2026; "Effective January 1,
2026"); VA Health Care Benefits Overview 2026, pages 19 to 20,
https://www.va.gov/HEALTHBENEFITS/resources/publications/10-185_HCBO_2026.pdf

**Where it comes from.** Web page and PDF, no login. Read November 11, 2026.

**Version and vintage.** 2026 rates.

**Coverage.** Outpatient medications from VA pharmacies. Medications given during a hospital stay are
covered by the inpatient copay.

**Changes over time, suppressed values, missing data, revisions.** Not applicable.

**Units and rounding.** Dollars per prescription by days supply.

**Known quirks.** Copays do not depend on the drug's price.

**Uncertainty.** None.

**License and attribution.** U.S. government work. Credit: U.S. Department of Veterans Affairs.

## Part D standard benefit, 2026 (CMS)

**What it is.** The 2026 defined standard Part D benefit: "The enrollee pays 100% of their gross covered
prescription drug costs (GCPDC) until the deductible of $615 for CY 2026 is met," then "25% coinsurance,"
until the "annual out-of-pocket (OOP) threshold of $2,100," after which "The enrollee pays no cost
sharing for covered Part D drugs."
Sources: https://www.cms.gov/newsroom/fact-sheets/final-cy-2026-part-d-redesign-program-instructions
(April 7, 2025); https://www.medicare.gov/health-drug-plans/part-d/basics/costs

**Where it comes from.** Web pages, no login. Read November 11, 2026.

**Coverage.** The standard benefit is a model. Plans can use other designs of equal value, such as flat
copays by tier and lower deductibles (see the beneficiary cost file above).

**Other fields.** Not applicable.

**License and attribution.** U.S. government work. Credit: Centers for Medicare & Medicaid Services.

## Medicaid cost sharing rules (federal regulation)

**What it is.** The federal limits on what Medicaid enrollees can be charged for prescription drugs.
42 CFR 447.53(b): for preferred drugs, at most $4; for non-preferred drugs, at most $8 for people with
family income at or below 150% of the federal poverty level, and "20% of the cost the agency pays" above
it. The dollar amounts rise each year from October 1, 2015, with the medical care part of the CPI-U; the
20% limit does not. 42 CFR 447.56(a) bars cost sharing for children, pregnant women (for pregnancy-related
care), people in hospice and other groups, and 447.56(f) caps all premiums and cost sharing at 5% of family
income. Under 447.52(e), a pharmacy can require the copay before filling only for people with income above
100% of the poverty level who are not in an exempt group.
Sources: https://www.law.cornell.edu/cfr/text/42/447.53 ; https://www.law.cornell.edu/cfr/text/42/447.52 ;
https://www.law.cornell.edu/cfr/text/42/447.56 (Cornell LII copies of the eCFR; the eCFR site redirected
automated reads).

**Where it comes from.** Web pages, no login. Read November 11, 2026.

**Coverage.** Federal limits only. Each state sets its own amounts within them; this post does not count
which states charge what.

**Known quirks.** The 20% limit is a share of what the state pays the pharmacy, not of a list price. The
current indexed dollar amounts were not checked.

**License and attribution.** U.S. government work.

## Method

Scripts, run in order from the project root: `scripts/top100.py`, `scripts/basket.py`,
`scripts/generic_tiers.py`, `scripts/tieout.py`. Charts: `scripts/viz.py` (`dist/index.html`),
`scripts/viz30.py` (`dist/negotiated-30day.html`), `scripts/viz19.py` (`dist/part-d-rebates.html`),
`scripts/viz21.py` (`dist/patient-cost.html`); `scripts/generic_tiers.py` also writes
`dist/generic-tiers.html`. Python virtual environment `.venv` with `duckdb`, `pandas`, `openpyxl`.

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

### Generic drugs on brand-level tiers (`scripts/generic_tiers.py`)

The question: how often do Part D plans put generic drugs on the tiers used for brand-name drugs? Counted
by drug product, not weighted by prescriptions, so every covered strength and form of a generic counts
the same.

1. **Plans:** distinct contract-plan-segment in the plan information file, each with its `FORMULARY_ID`.
   Only plans whose formulary has five or six tiers (highest `TIER_LEVEL_VALUE` 5 or 6) are counted:
   5,295 of 5,518 plans. Plans with one, two, four or seven tiers are left out because their tier numbers
   do not line up with the standard labels.
2. **Drug products:** each formulary row is one product (RxNorm ID) with one proxy NDC and a tier.
3. **Generic:** the proxy NDC's `MARKETINGCATEGORYNAME` in the FDA NDC Directory is ANDA, matched by
   package code or, when the package is no longer listed, by product code (first 9 digits). 3,074 generic
   products are on at least one of the counted formularies. Authorized generics (sold under the brand's
   NDA, 152 products) and NDCs not in the directory (81) are not counted as generic. Brand-name drugs, for
   comparison, are NDA or BLA products.
4. **Placement:** one plan covering one product. 12,335,512 generic placements.
5. **Brand-level tier:** tier 3 (preferred brand), 4 (non-preferred drug) or 5 (specialty). Tiers 1 and 2
   (generic) and 6 (select care, low-cost generics) are not.
6. **Measures:** share of placements on tiers 3 to 5, split into tier 3 and tiers 4 and 5; and the number
   of products on tiers 3 to 5 in at least half of the plans that cover them.
7. **Years since the first generic:** the product's ANDA number (from the NDC Directory) gives its active
   ingredient and form in Drugs@FDA `Products.txt`. The first generic date is the earliest original ANDA
   approval (`Submissions.txt`, ORIG, AP) for that active ingredient and form across all ANDAs. Years are
   counted to October 1, 2026. Groups: under 2, 2 to 5, 5 to 10, 10 to 20, 20 or more. A date was found
   for 3,070 of the 3,074 products.
8. **Patient cost by tier:** from the beneficiary cost file, for the same plans: initial coverage
   (`COVERAGE_LEVEL` 1), 30-day supply (`DAYS_SUPPLY` 1), at a preferred retail pharmacy when the plan
   offers one (`COST_TYPE_PREF` not 0), otherwise a standard retail pharmacy. Measures: share of plans
   charging coinsurance (type 2) on each tier, and share where the deductible applies.

Results: 52.7% of generic placements are on tiers 3 to 5 (tier 3 18.2%, tier 4 27.9%, tier 5 6.6%),
against 94% for brand-name drugs. 1,873 of the 3,074 generic products are on tiers 3 to 5 in at least half
of the plans that cover them. The share falls with time since the first generic: 87% under 2 years, 94%
at 2 to 5, 83% at 5 to 10, 57% at 10 to 20, and 42% at 20 years or more. Plans charge coinsurance on tier 3
in 70% of plans, tier 4 in 91% and tier 5 in 99%, against 4% and 10% on tiers 1 and 2; the deductible
applies on tiers 3 to 5 in 81% to 87% of plans, against 11% and 22% on tiers 1 and 2.

Output: `data/work/generic_tiers.csv` (one row per generic product: plans covering it, placements by tier,
first generic date).

### Rebate chart (`scripts/viz19.py`)

DIR as a share of total Part D drug costs, 2016 to 2026, transcribed from the Trustees Report Table IV.B8.
2025 and 2026 are marked as estimates. `scripts/tieout.py` re-reads the values from the PDF.

### Patient cost chart (`scripts/viz21.py`)

What a patient pays for a 30-day supply of each of the 10 compared brands with the most 2024 Part D
spending, under the 2026 standard benefit, compared with the VA copay.

1. **30-day price, Part D, before the dispensing fee.**
   - Drugs with a 2026 negotiated price (Eliquis, Jardiance, Xarelto, Farxiga, Entresto): CMS's negotiated
     price per 30-day equivalent supply (MFP data file, in effect November 1, 2026).
   - Others: the Part D median unit cost times the units in the package that lasts about a month at the
     labeled maintenance dose, median across that drug's packages, then times 30 divided by the days the
     package lasts. Ozempic: one 3 mL pen, 4 weekly maintenance doses, 28 days. Mounjaro and Trulicity: a
     carton of 4 weekly pens, 28 days. Trelegy: one 30-dose inhaler, one dose a day, 30 days. Revlimid: 21
     capsules, one 28-day cycle. A 28-day package is scaled to 30 days, the same basis as CMS's prices.
2. **Patient cost, standard benefit, one drug only.** A fill while in the deductible = the price up to the
   deductible still owed plus 25% of the rest; a fill after the deductible = 25% of the price; a year =
   twelve fills, with the deductible of $615 applied first, capped at $2,100. If the first fill reaches
   the cap, later fills cost $0 (Revlimid).
3. **VA:** $11 per 30-day supply (Tier 3, brand-name), $132 for a year; $0 for exempt veterans.
4. **Real plans (hover and table):** for plans on five- or six-tier formularies that cover the drug
   (any of its products, matched by the first 9 NDC digits), the drug's tier is the lowest tier among its
   products on that formulary. That tier's cost sharing for a 30-day retail fill in the initial coverage
   phase (preferred pharmacy if offered, else standard) gives the cost after the deductible: the copay, or
   the coinsurance rate times the 30-day price above, within any minimum or maximum the plan sets, capped
   at $2,100. Reported: plans covering the drug, share on tier 3 or higher, share charging coinsurance,
   share where the deductible applies (the tier's `DED_APPLIES_YN` is Y and the plan deductible is above
   $0), and the median and 10th and 90th percentile cost after the deductible. Only 225 plans cover brand
   Revlimid.

`scripts/tieout.py` checks the prices against the MFP file by drug name and the package rule,
recomputes the patient costs by simulating twelve fills, and recomputes the real-plan figures with pandas.

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
- **Generic tier counts:** counted by product and plan, not by prescriptions or enrollees. Common generics
  (lisinopril, amlodipine, metformin tablets) sit on tiers 1 and 2 in nearly every plan, so a count
  weighted by prescriptions would show a much lower share. Tier labels are the usual Plan Finder names,
  not fields in the file. A tier is not a price: what a patient pays depends on the plan's cost sharing
  for that tier and where the patient is in the benefit year.
- **Patient cost chart:** a model, not what any one plan charges. Real plans often use flat copays on
  some tiers and lower deductibles, and many enrollees take more than one drug, so they reach the
  deductible and the cap sooner. Prices exclude the dispensing fee. The 30-day package rule uses the
  labeled maintenance dose; starting doses (Ozempic) and other dosing schedules (Revlimid has 28-capsule
  regimens) would change the price.
