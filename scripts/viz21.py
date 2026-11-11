"""Build dist/patient-cost.html: what a patient pays for a month (30-day supply) of each drug, VA vs a
standard Part D plan, for the 10 compared brands with the most 2024 Part D spending.

30-day price (Part D, before the dispensing fee):
- negotiated drugs: CMS's negotiated price per 30-day equivalent supply (MFP data file, rows in effect
  November 1, 2026), as in scripts/viz30.py;
- other drugs: Part D median unit cost (SPUF 2026 Q3) x the units in the package that lasts about a month
  at the labeled maintenance dose, median across that drug's packages, x 30 / the days that package
  lasts (MONTH below). A 28-day package is scaled to 30 days, the same 30-day basis as CMS's prices.
Patient cost, 2026 Part D standard benefit: $615 deductible, then 25% coinsurance, $2,100 yearly
out-of-pocket cap; one drug only, no other spending that year.
VA: $11 per 30-day supply of a brand-name drug (Tier 3), $0 for veterans exempt from copays.
Run after scripts/top100.py.
"""
import json
import pandas as pd

DED, COINS, CAP, VA = 615.0, 0.25, 2100.0, 11.0
MFP = 'data/raw/cms_mfp/ex/CMS_Negotiation_Program_Selected_Drug_List_and_Maximum_Fair_Price_Data_File_20261102.csv'
NEG = {'eliquis', 'jardiance', 'xarelto', 'januvia', 'farxiga', 'entresto', 'enbrel', 'novolog', 'fiasp'}
# (package rule on quantity in the billing unit, days the package lasts at the labeled maintenance dose, note)
MONTH = {
    'ozempic':   (lambda d: (d.unit == 'ML') & (d.qty == 3), 28,
                  'one pen, 4 weekly maintenance doses (28 days), scaled to 30 days'),
    'mounjaro':  (lambda d: (d.qty == 2) & ~d.va_name.str.contains(r'\b2\.5 ?MG', na=False), 28,
                  'carton of 4 weekly pens (28 days), scaled to 30 days; the 2.5 mg starting dose is left out'),
    'trulicity': (lambda d: d.qty == 2, 28, 'carton of 4 weekly pens (28 days), scaled to 30 days'),
    'trelegy':   (lambda d: d.qty == 60, 30, 'one 30-dose inhaler, one dose a day (30 days)'),
    'revlimid':  (lambda d: d.qty == 21, 28, '21 capsules, one 28-day cycle, scaled to 30 days'),
    'humira':    (lambda d: d.va_name.str.contains('40MG', na=False) & (d.qty == 2), 28,
                  'carton of 2 pens or syringes of 40 mg, one every other week (28 days), scaled to 30 days'),
}

b = pd.read_csv('data/work/top100_brand.csv')
b = b[b.status == 'compared'].sort_values('spending_2024', ascending=False).head(10)
n = pd.read_csv('data/work/top100_ndc.csv', dtype={'NDC': str})
n = n[n.big4_vs_partd.notna() & ~n.unit_flag]

money = lambda s: s.str.replace(r'[$,]', '', regex=True).astype(float)
mf = pd.read_csv(MFP, dtype=str)
mf = mf[(pd.to_datetime(mf['MFP Effective Date']) <= '2026-11-01')
        & (pd.to_datetime(mf['MFP End Date']).fillna(pd.Timestamp('2099-12-31')) >= '2026-11-01')]
mf = mf.assign(p9=mf['NDC-9'].str.replace('-', ''), m30=money(mf['Single MFP per 30 DES'])).drop_duplicates('p9')


def phases(price):
    """Standard benefit: a 30-day fill while in the deductible, one after it, and a year of this drug."""
    in_ded = min(CAP, min(price, DED) + COINS * max(0.0, price - DED))
    after = 0.0 if in_ded >= CAP else min(COINS * price, CAP)
    year = min(CAP, min(12 * price, DED) + COINS * max(0.0, 12 * price - DED))
    return in_ded, after, year


# ---------- real plans (SPUF 2026 Q3), plans on five- or six-tier formularies ----------
# Per plan: the drug's tier (lowest tier among its products on that formulary), that tier's cost sharing in
# the initial coverage phase for a 30-day retail fill (preferred pharmacy if offered, else standard), and
# whether the deductible applies (DED_APPLIES_YN = Y and a plan deductible above $0). Coinsurance is applied
# to the 30-day price above, within any minimum or maximum the plan sets; capped at the $2,100 limit.
import duckdb
SP = 'data/raw/spuf_2026q3/ex/'
con = duckdb.connect()
con.sql(f"""create table f as select FORMULARY_ID, NDC, cast(TIER_LEVEL_VALUE as int) as tier
            from read_csv('{SP}basic drugs formulary file  PPUF_2026Q3.txt', delim='|', header=true, all_varchar=true)""")
con.sql("create table fm as select FORMULARY_ID from f group by 1 having max(tier) in (5, 6)")
con.sql(f"""create table p as select distinct CONTRACT_ID, PLAN_ID, SEGMENT_ID, FORMULARY_ID, cast(DEDUCTIBLE as double) as ded
            from read_csv('{SP}plan information  PPUF_2026Q3.txt', delim='|', header=true, all_varchar=true)
            where FORMULARY_ID in (select FORMULARY_ID from fm)""")
con.sql(f"""create table c as select CONTRACT_ID, PLAN_ID, SEGMENT_ID, cast(TIER as int) as tier,
            case when COST_TYPE_PREF <> '0' then COST_TYPE_PREF else COST_TYPE_NONPREF end as typ,
            cast(case when COST_TYPE_PREF <> '0' then COST_AMT_PREF else COST_AMT_NONPREF end as double) as amt,
            cast(case when COST_TYPE_PREF <> '0' then COST_MIN_AMT_PREF else COST_MIN_AMT_NONPREF end as double) as mn,
            cast(case when COST_TYPE_PREF <> '0' then COST_MAX_AMT_PREF else COST_MAX_AMT_NONPREF end as double) as mx,
            DED_APPLIES_YN as dap
            from read_csv('{SP}beneficiary cost file  PPUF_2026Q3.txt', delim='|', header=true, all_varchar=true)
            where COVERAGE_LEVEL = '1' and DAYS_SUPPLY = '1'""")


def plan_prices(pk, days):
    """Each plan's own 30-day price: its unit cost (pricing file, 30-day) for the month packages' products
    (first 9 digits of the NDC), times the package quantity, x 30 / days; median across its rows."""
    q = pk.assign(p9=pk.NDC.str[:9]).groupby('p9').qty.median().reset_index()
    con.register('q', q)
    r = con.sql(f"""select CONTRACT_ID, PLAN_ID, SEGMENT_ID,
                          median(cast(UNIT_COST as double) * q.qty * 30 / {days}) as own
                   from read_csv('{SP}pricing file PPUF_2026Q3.txt', delim='|', header=true, all_varchar=true) x
                   join q on substr(x.NDC, 1, 9) = q.p9
                   where DAYS_SUPPLY = '30' group by all""").df()
    return r


def real_plans(fam, price, own=None):
    p9 = pd.DataFrame({'p9': n.loc[n.family == fam, 'NDC'].str[:9].unique()})
    con.register('p9', p9)
    d = con.sql("""select p.CONTRACT_ID, p.PLAN_ID, p.SEGMENT_ID, p.ded, min(f.tier) as tier
                   from f join p9 on substr(f.NDC, 1, 9) = p9.p9 join p using (FORMULARY_ID) group by all""").df()
    d = d.merge(con.sql('select * from c').df(), on=['CONTRACT_ID', 'PLAN_ID', 'SEGMENT_ID', 'tier'], how='inner')
    # each plan's own price where the pricing file has one; negotiated drugs: every plan pays the negotiated price
    if own is not None:
        d = d.merge(own, on=['CONTRACT_ID', 'PLAN_ID', 'SEGMENT_ID'], how='left')
        d['px'] = d.own.fillna(price)
    else:
        d['own'], d['px'] = price, price
    coins = d.amt * d.px
    coins = coins.where(~(d.mx > 0), coins.clip(upper=d.mx)).where(~(d.mn > 0), coins.clip(lower=d.mn))
    d['after'] = d.amt.where(d.typ == '1', coins.where(d.typ == '2')).clip(upper=CAP)
    return dict(rp_plans=len(d), rp_tier3=round(100 * d.tier.between(3, 5).mean(), 1),
                rp_coins=round(100 * (d.typ == '2').mean(), 1),
                rp_ded=round(100 * ((d.dap == 'Y') & (d.ded > 0)).mean(), 1),
                rp_after=round(float(d.after.median()), 2), rp_p10=round(float(d.after.quantile(.1)), 2),
                rp_p90=round(float(d.after.quantile(.9)), 2), rp_own=round(100 * d.own.notna().mean(), 1),
                rp_px=round(float(d.px.median()), 2))


rows = []
for r in b.itertuples():
    sub = n[n.family == r.family]
    if r.family in NEG:
        m30 = sub.assign(p9=sub.NDC.str[:9]).merge(mf[['p9', 'm30']], on='p9').m30
        assert m30.nunique() == 1, r.family
        price, basis = float(m30.iloc[0]), 'CMS negotiated price for a 30-day supply'
        own = None
    else:
        rule, days, basis = MONTH[r.family]
        pk = sub[rule(sub)]
        assert len(pk), r.family
        price = float((pk.partd_unit * pk.qty).median()) * 30 / days
        own = plan_prices(pk, days)
    in_ded, after, year = phases(price)
    name = min(r.brand_names.split('; '), key=len).split()[0].rstrip('*')
    rows.append(dict(name=name, generic=r.generic.lower(), neg=r.family in NEG, spend=round(r.spending_2024 / 1e9, 2),
                     price=round(price, 2), basis=basis, in_ded=round(in_ded, 2), after=round(after, 2),
                     year=round(year, 2), va=VA, va_year=VA * 12, **real_plans(r.family, price, own)))

neg = [r['name'] for r in rows if r['neg']]
neg_list = ', '.join(neg[:-1]) + ' and ' + neg[-1] if len(neg) > 1 else ''.join(neg)
tpl = open('scripts/viz21_template.html').read()
html = (tpl.replace('/*__DATA__*/[]', json.dumps(rows, separators=(',', ':')))
           .replace('__NEGLIST__', neg_list).replace('__NNEG__', {4: 'four', 5: 'five', 6: 'six'}.get(len(neg), str(len(neg))))
           .replace('__LOGO__', open('assets/d4tp-logo.datauri').read().strip()))
open('dist/patient-cost.html', 'w').write(html)
pd.set_option('display.width', 220)
print(pd.DataFrame(rows).drop(columns=['generic']).to_string(index=False))
