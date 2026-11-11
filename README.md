# VA and Medicare Part D drug prices

Data 4 The People. This project compares the VA's prices for brand-name drugs with the prices Medicare Part D
plans pay, and compares what a patient pays for a month of a drug at the VA and in Part D. It covers 89 of the
100 brand-name drugs with the most Part D claims in 2024, using prices in effect in fall 2026.

Interactive charts:

- VA prices compared with Medicare Part D prices, by drug:
  https://data4thepeople.github.io/VA_NADAC_Drug_Prices/dist/index.html
- What a 30-day supply costs, Medicare's negotiated price and the VA's price:
  https://data4thepeople.github.io/VA_NADAC_Drug_Prices/dist/negotiated-30day.html
- Rebates and other payments to Part D plans, as a share of drug costs, 2016 to 2026:
  https://data4thepeople.github.io/VA_NADAC_Drug_Prices/dist/part-d-rebates.html
- How often Part D plans put generic drugs on brand-level tiers:
  https://data4thepeople.github.io/VA_NADAC_Drug_Prices/dist/generic-tiers.html
- What a patient pays for a month of each drug, VA and a standard Part D plan:
  https://data4thepeople.github.io/VA_NADAC_Drug_Prices/dist/patient-cost.html

## Where to look

| File | What it holds |
|---|---|
| `DATASETS.md` | Every data source, where it comes from, its limits and quirks, and the method in full |
| `TIEOUT.md` | Every number and claim we check, with the result |
| `posts/va-vs-medicare-drug-prices/POST.md` | The post |
| `data/work/` | The per-drug and per-package tables the charts are built from, and the tie-out results |
| `dist/` | The built charts, one self-contained HTML file each |
| `scripts/` | The code that builds the tables, the charts and the tie-out |

## Method in brief

- **Prices.** The VA price is its Big4 price, the most the VA can be charged; the VA can pay less. The
  Medicare price is the median unit price across Part D plans in CMS's pricing file for 2026 Q3. Both are
  before rebates and discounts, which are not public. Prices are compared per tablet, mL or gram, so
  package counts are checked against FDA, VA and CMS records.
- **Patient costs.** The VA charges a flat copay of up to $11 for a 30-day supply of a brand-name drug, and
  some veterans pay nothing. The Part D standard plan for 2026 has a $615 deductible, then 25% coinsurance,
  up to $2,100 for the year. Real plans' tiers, copays and coinsurance come from CMS's Part D plan files for
  2026 Q3.
- **Generic tiers.** A drug is counted as generic when the FDA lists it under an abbreviated new drug
  application (ANDA). Each strength and form of a drug counts once per plan, for the 5,295 plans whose drug
  lists use five or six tiers.

`DATASETS.md` has the full method and its limits.

## Rebuild

Python 3 with `duckdb`, `pandas`, `openpyxl` and `pypdf`. Raw data is not in the repo: download each source
from the address in `DATASETS.md` into `data/raw/`. Then, from the project root:

```
python scripts/top100.py         # drugs, packages and per-unit prices
python scripts/basket.py         # basket cost
python scripts/generic_tiers.py  # generic tiers table and dist/generic-tiers.html
python scripts/lenalidomide.py   # generic lenalidomide in real plans
python scripts/viz.py            # dist/index.html
python scripts/viz30.py          # dist/negotiated-30day.html
python scripts/viz19.py          # dist/part-d-rebates.html
python scripts/viz21.py          # dist/patient-cost.html
python scripts/tieout.py         # data/work/tieout_claude.csv
```

Sources: U.S. Department of Veterans Affairs; Centers for Medicare & Medicaid Services; U.S. Food and Drug
Administration; 2026 Medicare Trustees Report. U.S. government works.
