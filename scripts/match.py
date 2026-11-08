"""Feasibility: match VA pharma prices (Nov 1 2026) to NADAC (latest week) by NDC.
Tier 1: exact 11-digit NDC.  Tier 2: same labeler+product (first 9 digits), different pack size.
VA price is per package; convert to per unit by parsing PackageDescription.
"""
import re, sys
import pandas as pd

va_path, nadac_path, out_path = sys.argv[1:4]

va = pd.read_excel(va_path, dtype={"NDCWithDashes": str, "PackageDescription": str})
va["ndc11"] = va.NDCWithDashes.str.replace("-", "")
va["ndc9"] = va.ndc11.str[:9]

def parse_pkg(s):
    s = str(s).strip().upper()
    m = re.fullmatch(r"(?:(\d+(?:\.\d+)?)X)?(\d+(?:\.\d+)?)\s*(ML|GM|G|UD|EA)?", s)
    if not m:
        return None, None
    a = float(m.group(1)) if m.group(1) else 1.0
    b = float(m.group(2))
    u = m.group(3) or "EA"
    u = {"G": "GM", "UD": "EA"}.get(u, u)
    return a * b, u

parsed = va.PackageDescription.map(parse_pkg)
va["pkg_qty"] = [p[0] for p in parsed]
va["pkg_unit"] = [p[1] for p in parsed]
va["va_unit_price"] = va.Price / va.pkg_qty

na = pd.read_csv(nadac_path, dtype={"NDC": str})
na["NDC"] = na.NDC.str.zfill(11)
na["as_of"] = pd.to_datetime(na["As of Date"])
latest = na.as_of.max()
na = na[na.as_of == latest].drop_duplicates("NDC")
na["ndc9"] = na.NDC.str[:9]
print("NADAC as-of", latest.date(), "rows", len(na))

# Tier 1
m1 = va.merge(na.drop(columns="ndc9"), left_on="ndc11", right_on="NDC", how="left")
m1["tier"] = m1["NADAC Per Unit"].notna().map({True: "ndc11", False: None})

# Tier 2: same product, different package. Take the median NADAC per unit across packages.
p9 = (na.groupby(["ndc9", "Pricing Unit"])
        .agg(nadac9=("NADAC Per Unit", "median"), desc9=("NDC Description", "first"),
             cls9=("Classification for Rate Setting", "first"))
        .reset_index())
p9 = p9.drop_duplicates("ndc9", keep=False)  # drop ambiguous units
miss = m1.tier.isna()
t2 = m1.loc[miss, ["ndc9"]].merge(p9, on="ndc9", how="left")
t2.index = m1.index[miss]
has = t2.nadac9.notna()
idx = t2.index[has]
m1.loc[idx, "NADAC Per Unit"] = t2.loc[has, "nadac9"].values
m1.loc[idx, "NDC Description"] = t2.loc[has, "desc9"].values
m1.loc[idx, "Pricing Unit"] = t2.loc[has, "Pricing Unit"].values
m1.loc[idx, "Classification for Rate Setting"] = t2.loc[has, "cls9"].values
m1.loc[idx, "tier"] = "ndc9"

m1["unit_ok"] = m1.pkg_unit == m1["Pricing Unit"]
m1["ratio"] = m1.va_unit_price / m1["NADAC Per Unit"]
m1.to_csv(out_path, index=False)

rows = len(m1); ndcs = m1.ndc11.nunique()
print(f"VA rows {rows:,}  unique NDCs {ndcs:,}")
for t in ["ndc11", "ndc9"]:
    s = m1[m1.tier == t]
    print(f"  {t}: rows {len(s):,} ({len(s)/rows:.1%}), NDCs {s.ndc11.nunique():,} ({s.ndc11.nunique()/ndcs:.1%})")
matched = m1[m1.tier.notna()]
print(f"  any match: NDCs {matched.ndc11.nunique()/ndcs:.1%}; units agree on {matched.unit_ok.mean():.1%} of matched rows")
print("  unmatched VA rows by Covered flag:", m1[m1.tier.isna()].Covered.value_counts().to_dict())
