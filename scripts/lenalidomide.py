"""Generic lenalidomide (Revlimid's generic) in real Part D plans, for the post's Revlimid paragraph.

Plans on five- or six-tier formularies (SPUF 2026 Q3), as in scripts/generic_tiers.py. Per plan:
- coverage and tier: formulary rows whose proxy NDC is a lenalidomide ANDA product in the FDA NDC Directory
  (package code, else product code); the plan's lowest tier among them;
- cost sharing: that tier in the initial coverage phase, 30-day retail fill, preferred pharmacy if offered,
  else standard; deductible applies when DED_APPLIES_YN = Y and the plan's deductible is above $0;
- price: the plan's own unit cost per capsule (pricing file, 30-day), median across its lenalidomide ANDA
  products; the national median if the plan lists none. One cycle = 21 capsules (28 days).
- patient cost for the first and second cycle of the year, with only this drug, capped at $2,100.
Also: plans covering brand Revlimid (NDA products). Output: data/work/lenalidomide.csv (one row per plan).
"""
import re
import duckdb
import pandas as pd

SP = 'data/raw/spuf_2026q3/ex/'
CAP, CAPS = 2100.0, 21

prod = pd.read_csv('data/raw/fda_ndc/product.txt', sep='\t', dtype=str, encoding='latin-1')
pkg = pd.read_csv('data/raw/fda_ndc/package.txt', sep='\t', dtype=str, encoding='latin-1')
pkg = pkg.merge(prod[['PRODUCTID', 'NONPROPRIETARYNAME', 'PROPRIETARYNAME', 'MARKETINGCATEGORYNAME']], on='PRODUCTID')


def ndc11(dashed):
    a, b, c = dashed.split('-')
    return a.zfill(5) + b.zfill(4) + c.zfill(2)


pkg['NDC'] = pkg.NDCPACKAGECODE.map(ndc11)
len_ = pkg[pkg.NONPROPRIETARYNAME.str.contains('lenalidomide', case=False, na=False)]
gen9 = set(len_.loc[len_.MARKETINGCATEGORYNAME == 'ANDA', 'NDC'].str[:9])
brand9 = set(len_.loc[len_.MARKETINGCATEGORYNAME == 'NDA', 'NDC'].str[:9])
gen11 = set(len_.loc[len_.MARKETINGCATEGORYNAME == 'ANDA', 'NDC'])
brand11 = set(len_.loc[len_.MARKETINGCATEGORYNAME == 'NDA', 'NDC'])


def kind(ndc):
    """Package code first, then product code (first 9 digits)."""
    if ndc in gen11:
        return 'generic'
    if ndc in brand11:
        return 'brand'
    return 'generic' if ndc[:9] in gen9 else 'brand' if ndc[:9] in brand9 else None


con = duckdb.connect()
con.sql(f"""create table f as select FORMULARY_ID, NDC, cast(TIER_LEVEL_VALUE as int) as tier
            from read_csv('{SP}basic drugs formulary file  PPUF_2026Q3.txt', delim='|', header=true, all_varchar=true)""")
con.sql("create table fm as select FORMULARY_ID from f group by 1 having max(tier) in (5, 6)")
p = con.sql(f"""select distinct CONTRACT_ID, PLAN_ID, SEGMENT_ID, FORMULARY_ID, cast(DEDUCTIBLE as double) as ded
                from read_csv('{SP}plan information  PPUF_2026Q3.txt', delim='|', header=true, all_varchar=true)
                where FORMULARY_ID in (select FORMULARY_ID from fm)""").df()
fr = con.sql("""select FORMULARY_ID, NDC, tier from f
                where FORMULARY_ID in (select FORMULARY_ID from fm) and NDC like '%'""").df()
fr = fr[fr.NDC.str[:9].isin(gen9 | brand9)]
fr['kind'] = fr.NDC.map(kind)
keys = ['CONTRACT_ID', 'PLAN_ID', 'SEGMENT_ID']
pb = p.merge(fr[fr.kind == 'brand'], on='FORMULARY_ID')[keys].drop_duplicates()
d = (p.merge(fr[fr.kind == 'generic'], on='FORMULARY_ID')
      .groupby(keys + ['ded'], as_index=False).tier.min())
c = con.sql(f"""select CONTRACT_ID, PLAN_ID, SEGMENT_ID, cast(TIER as int) as tier,
                case when COST_TYPE_PREF <> '0' then COST_TYPE_PREF else COST_TYPE_NONPREF end as typ,
                cast(case when COST_TYPE_PREF <> '0' then COST_AMT_PREF else COST_AMT_NONPREF end as double) as amt,
                cast(case when COST_TYPE_PREF <> '0' then COST_MIN_AMT_PREF else COST_MIN_AMT_NONPREF end as double) as mn,
                cast(case when COST_TYPE_PREF <> '0' then COST_MAX_AMT_PREF else COST_MAX_AMT_NONPREF end as double) as mx,
                DED_APPLIES_YN as dap
                from read_csv('{SP}beneficiary cost file  PPUF_2026Q3.txt', delim='|', header=true, all_varchar=true)
                where COVERAGE_LEVEL = '1' and DAYS_SUPPLY = '1'""").df()
d = d.merge(c, on=keys + ['tier'], how='left')
g9 = pd.DataFrame({'p9': sorted(gen9)})
con.register('g9', g9)
pr = con.sql(f"""select CONTRACT_ID, PLAN_ID, SEGMENT_ID, NDC, cast(UNIT_COST as double) as u
                 from read_csv('{SP}pricing file PPUF_2026Q3.txt', delim='|', header=true, all_varchar=true) x
                 join g9 on substr(x.NDC, 1, 9) = g9.p9 where DAYS_SUPPLY = '30'""").df()
national = pr.groupby('NDC').u.median()
own = pr.groupby(keys, as_index=False).u.median().rename(columns={'u': 'own_unit'})
d = d.merge(own, on=keys, how='left')
d['unit'] = d.own_unit.fillna(float(national.median()))
d['cycle'] = d.unit * CAPS


def share(cost, r):
    """Cost sharing on `cost` dollars after the deductible, by the plan's tier rule."""
    if r.typ == '1':
        return min(r.amt, cost)
    if r.typ == '2':
        x = r.amt * cost
        if r.mx > 0:
            x = min(x, r.mx)
        if r.mn > 0:
            x = max(x, r.mn)
        return min(x, cost)
    return float('nan')


def fills(r):
    ded = r.ded if (r.dap == 'Y' and r.ded > 0) else 0.0
    paid, out = 0.0, []
    left_ded = ded
    for _ in range(2):
        in_d = min(r.cycle, left_ded)
        left_ded -= in_d
        pay = in_d + (share(r.cycle - in_d, r) if r.cycle > in_d else 0.0)
        pay = min(pay, CAP - paid)
        paid += pay
        out.append(pay)
    return pd.Series({'fill1': out[0], 'fill2': out[1], 'two_fills': paid})


d = pd.concat([d, d.apply(fills, axis=1)], axis=1)
d.to_csv('data/work/lenalidomide.csv', index=False)

cs = d[d.typ.notna()]
co = cs[cs.typ == '2']
print(f"plans on 5/6-tier formularies: {len(p):,}; cover brand Revlimid: {len(pb):,}; cover generic: {len(d):,}")
print('lowest tier per plan:', d.tier.value_counts().sort_index().to_dict())
print(f"plans with cost rows: {len(cs):,}; coinsurance: {100 * (cs.typ == '2').mean():.1f}%; "
      f"copay: {(cs.typ == '1').sum()} (amounts {sorted(cs.loc[cs.typ == '1', 'amt'].unique())[:5]})")
print('coinsurance rates:', (co.amt.round(2).value_counts(normalize=True).sort_index() * 100).round(1).to_dict())
print(f"deductible applies: {100 * ((cs.dap == 'Y') & (cs.ded > 0)).mean():.1f}%")
print(f"own price for {100 * d.own_unit.notna().mean():.1f}% of plans; unit price median {d.unit.median():.2f}, "
      f"p10 {d.unit.quantile(.1):.2f}, p90 {d.unit.quantile(.9):.2f}")
print(f"national medians per NDC: {national.min():.2f} to {national.max():.2f}")
print(f"21-capsule cycle at each plan's price: median {d.cycle.median():,.0f}, p10 {d.cycle.quantile(.1):,.0f}, "
      f"p90 {d.cycle.quantile(.9):,.0f}")
print(f"first fill: median {cs.fill1.median():,.2f}, p10 {cs.fill1.quantile(.1):,.2f}, p90 {cs.fill1.quantile(.9):,.2f}; "
      f"under $1,600 in {100 * (cs.fill1 < 1600).mean():.1f}% of plans")
print(f"reach $2,100 by the second fill: {100 * (cs.two_fills >= CAP - 0.005).mean():.1f}% of plans; "
      f"by the first: {100 * (cs.fill1 >= CAP - 0.005).mean():.1f}%")
