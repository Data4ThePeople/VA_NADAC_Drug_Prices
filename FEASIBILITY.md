# VA drug prices vs NADAC: feasibility check (November 8, 2026)

Pre-Step 1 check. These numbers are not tied out and should not be used in a post.

## Sources pulled

- VA National Acquisition Center pharmaceutical prices, `TPharmPrices-11-01-2026.xlsx`
  (department.va.gov, FSS Service page). 43,206 rows, 16,501 unique NDCs.
  Price types: FSS 30,443 rows, Big4 10,853, National Contract (NC) 1,910.
- NADAC 2026 from data.medicaid.gov (dataset `fbb83258-11c7-47f5-8b18-5f8e79f7e704`),
  latest week as of November 4, 2026. 30,102 NDCs.

## The key finding

The current VA file has an `NDCWithDashes` column, with a full 11-digit NDC on every row.
So the main match is on NDC, not drug name. Name matching is only a backup for repackaged generics.

## Match results (unique VA NDCs)

| Tier | Method | Share of VA NDCs |
|---|---|---|
| 1 | Exact 11-digit NDC | 41.6% |
| 2 | Same labeler and product, different package (first 9 digits) | 1.2% |
| 3 | Generic name + strength + form + release type | 15.0% |
| | Total | 57.7% |

- 24% of VA NDCs are for drugs that NADAC does not price at all: hospital injectables, IV fluids,
  clinic-given and specialty drugs, vaccines, vitamins. NADAC covers only retail pharmacy drugs.
- Of the VA NDCs whose drug appears in NADAC, 73% matched with units that agree.
  For tablets and capsules it is 85%.
- Tier 3 check: on rows where the NDC match gives the true answer, the name match lands within 10%
  of the true NADAC price 95.5% of the time. Misses are mostly liquids and injectables.

## Common brands

Of 66 common brands checked, 59 matched, all by exact NDC: Eliquis, Xarelto, Jardiance, Farxiga,
Ozempic, Mounjaro, Wegovy, Zepbound, Trulicity, Entresto, Januvia, Humira, Trelegy, Symbicort,
Lantus, Humalog, Biktarvy, Dupixent, Skyrizi, Vraylar, Rexulti, Repatha, and more.
Not matched: Taltz, Xiidra, Shingrix, ProAir, Leqvio, Camzyos, Cabenuva (not in NADAC or no
usable unit match).

## Problems to fix in Step 1

1. Package units. VA's `PackageDescription` is not always a unit count. One Ellipta inhaler is "1",
   but NADAC prices Ellipta per blister. Use FDA's NDC directory package file for unit counts.
2. Brand rows listed under the generic name. VA's `Generic` column holds the generic name on brand
   rows too, so tier 3 priced some brands against the generic (for example a $477.88 quetiapine row).
   Limit tier 3 to rows with no brand name in `TradeName`.
3. Placeholder prices of $0.01 on some rows. Drop them.
4. Many NDCs have several rows (FSS, Big4, NC, several contracts). Decide which VA price stands
   for "the VA price": Big4 for brands, NC where it exists for generics, FSS as the ceiling for
   other agencies.

## Early patterns (not tied out)

- Most brand Big4 prices sit about 25% below NADAC, close to the 24% minimum federal discount.
- A few brands have Big4 equal to FSS and slightly above NADAC: Eliquis and Farxiga about 3%,
  also Tresiba and Dupixent. Worth looking into.
- Many generic FSS prices are well above NADAC (for example bupropion SR, propranolol, valacyclovir).

## Scripts

- `scripts/match.py <va.xlsx> <nadac.csv> <out.csv>`: tiers 1 and 2.
- `scripts/namematch.py <tier12.csv> <nadac.csv> <out.csv>`: tier 3 and its check.
