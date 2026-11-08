"""Tier 3: name match for generics. Key = (ingredient words, strengths, form, release).
Validated on NDC-matched rows: does the name key point to the same NADAC price?"""
import re, sys
import pandas as pd

matched_path, nadac_path, out_path = sys.argv[1:4]
m = pd.read_csv(matched_path, dtype={"ndc11": str, "NDC": str}, low_memory=False)
na = pd.read_csv(nadac_path, dtype={"NDC": str})
na["as_of"] = pd.to_datetime(na["As of Date"])
na = na[na.as_of == na.as_of.max()].drop_duplicates("NDC")

FORMS = [("TAB", r"\bTAB"), ("CAP", r"\bCAP"), ("INJ", r"\b(INJ|VIAL|SYRINGE|SYRG|SYR|PEN|CARTRIDGE|CART)\b"),
         ("SOLN", r"\b(SOLN|SOL|SOLUTION|LIQUID|LIQ|ELIXIR|SYRUP|ORAL SOLN)\b"), ("SUSP", r"\bSUSP"),
         ("CREAM", r"\bCREAM|\bCRM\b"), ("OINT", r"\bOINT"), ("GEL", r"\bGEL\b"), ("PATCH", r"\bPATCH|\bFILM,TD|\bTD FILM"),
         ("INHL", r"\b(INHL|INHALER|INH|AER|NEB)"), ("DROP", r"\b(OPH|DROP|OTIC)"), ("SUPP", r"\bSUPP")]
REL = [("ER", r"\b(ER|SA|XL|XR|24HR|12HR|EXT|SR|CR|LA|ER24H|ER12H)\b"), ("DR", r"\b(DR|EC)\b"), ("ODT", r"\b(ODT|DISINTEGRAT)")]
STOP = {"HCL", "HYDROCHLORIDE", "SODIUM", "NA", "CALCIUM", "CA", "POTASSIUM", "K", "MESYLATE", "MALEATE", "SUCCINATE",
        "TARTRATE", "ACETATE", "BESYLATE", "CITRATE", "SULFATE", "FUMARATE", "MAGNESIUM", "MG", "HBR", "HYCLATE",
        "MONOHYDRATE", "DIHYDRATE", "TROMETHAMINE", "DISODIUM", "BROMIDE", "PHOSPHATE", "OLAMINE", "DIPROPIONATE", "AND", "W"}

def norm(desc):
    d = str(desc).upper().replace(",", " ").replace("/", " / ")
    d = re.sub(r"\(.*?\)", " ", d)
    d = re.sub(r"(\d)\s+(MG|MCG|GM|G|ML|UNT|UNIT|%|MEQ)\b", r"\1\2", d)
    strengths = tuple(sorted(re.findall(r"\d+(?:\.\d+)?(?:MG|MCG|GM|G|UNT|UNIT|%|MEQ)", d)))
    strengths = tuple(s.replace("UNIT", "UNT").replace("GM", "G") for s in strengths)
    form = next((f for f, p in FORMS if re.search(p, d)), "OTHER")
    rel = next((r for r, p in REL if re.search(p, d)), "")
    first = re.split(r"\d", d, 1)[0]
    words = tuple(sorted(w for w in re.findall(r"[A-Z]{3,}", first) if w not in STOP and w not in {f for f, _ in FORMS}))
    return (words, strengths, form, rel)

na["key"] = na["NDC Description"].map(norm)
g = na[na["Classification for Rate Setting"] == "G"]
# one price per key; drop keys where NADAC generic prices disagree a lot (key is ambiguous)
agg = g.groupby("key").agg(nadac_k=("NADAC Per Unit", "median"), lo=("NADAC Per Unit", "min"),
                           hi=("NADAC Per Unit", "max"), unit_k=("Pricing Unit", "first"),
                           desc_k=("NDC Description", "first"), n=("NDC", "size")).reset_index()
agg = agg[agg.hi <= agg.lo * 1.5]
lookup = agg.set_index("key")

m["key"] = m.Generic.map(norm)
m["key_hit"] = m.key.isin(lookup.index)

# Validation on generic rows that matched by exact NDC
v = m[(m.tier == "ndc11") & (m["Classification for Rate Setting"] == "G") & m.key_hit].copy()
v["pred"] = v.key.map(lookup.nadac_k)
v["err"] = (v.pred / v["NADAC Per Unit"] - 1).abs()
base = m[(m.tier == "ndc11") & (m["Classification for Rate Setting"] == "G")]
print(f"validation: name key found for {len(v)/len(base):.1%} of NDC-matched generic rows")
print(f"  name price within 10% of true NDC price: {(v.err <= .10).mean():.1%}; within 25%: {(v.err <= .25).mean():.1%}")
bad = v[v.err > .25].drop_duplicates("Generic").head(12)
print(bad[["Generic", "NDC Description", "NADAC Per Unit", "pred"]].to_string())

# Apply to unmatched rows, only where VA package unit agrees with NADAC unit
u = m.tier.isna() & m.key_hit
m.loc[u, "NADAC Per Unit"] = m.loc[u, "key"].map(lookup.nadac_k)
m.loc[u, "Pricing Unit"] = m.loc[u, "key"].map(lookup.unit_k)
m.loc[u, "NDC Description"] = m.loc[u, "key"].map(lookup.desc_k)
m.loc[u, "Classification for Rate Setting"] = "G"
m.loc[u, "tier"] = "name_generic"
m["unit_ok"] = m.pkg_unit == m["Pricing Unit"]
m["ratio"] = m.va_unit_price / m["NADAC Per Unit"].astype(float)
m.to_csv(out_path, index=False)

ndcs = m.ndc11.nunique()
print("\nmatch by tier (unique VA NDCs):")
first = m.dropna(subset=["tier"]).drop_duplicates("ndc11")
print((first.tier.value_counts() / ndcs).round(3).to_dict(), "total", round(len(first) / ndcs, 3))
usable = m[m.tier.notna() & m.unit_ok]
print("usable (units agree) NDCs:", round(usable.ndc11.nunique() / ndcs, 3))
