"""Generic drugs (ANDA) on Part D brand-level tiers, by count.

CMS's 2026 Q3 basic drugs formulary file lists each covered drug product once per formulary by RxNorm ID
(RXCUI), with one representative NDC and a tier. A product is generic here when its representative NDC is
an ANDA product in the FDA NDC Directory. Plans: distinct contract-plan-segment in the plan information file,
each using one formulary. Only plans on 5- or 6-tier formularies are counted, where CMS's standard layout is
1 preferred generic, 2 generic, 3 preferred brand, 4 non-preferred drug, 5 specialty, 6 select care (the
tier-6 list here is low-cost generics such as lisinopril). "Brand-level tier" = tier 3, 4 or 5.
First generic approval: the earliest original ANDA approval in Drugs@FDA for the same active ingredient
and dosage form.
Writes data/work/generic_tiers.csv (one row per generic product).
"""
import duckdb
import pandas as pd

E = 'data/raw/spuf_2026q3/ex/'
D = 'data/raw/drugsatfda/ex/'
AS_OF = pd.Timestamp('2026-10-01')

con = duckdb.connect()
con.sql(f"""create table f as select FORMULARY_ID, RXCUI, NDC, cast(TIER_LEVEL_VALUE as int) as tier
            from read_csv('{E}basic drugs formulary file  PPUF_2026Q3.txt', delim='|', header=true, all_varchar=true)""")
con.sql(f"""create table p as select distinct CONTRACT_ID, PLAN_ID, SEGMENT_ID, FORMULARY_ID
            from read_csv('{E}plan information  PPUF_2026Q3.txt', delim='|', header=true, all_varchar=true)""")
con.sql("create table fm as select FORMULARY_ID, max(tier) as n_tiers from f group by 1")

# FDA NDC Directory: marketing category of each representative NDC
prod = pd.read_csv('data/raw/fda_ndc/product.txt', sep='\t', dtype=str, encoding='latin-1')
pkg = pd.read_csv('data/raw/fda_ndc/package.txt', sep='\t', dtype=str, encoding='latin-1')
pkg['NDC'] = pkg.NDCPACKAGECODE.map(lambda d: (lambda a, b, c: a.zfill(5) + b.zfill(4) + c.zfill(2))(*d.split('-')))
COLS = ['MARKETINGCATEGORYNAME', 'APPLICATIONNUMBER', 'NONPROPRIETARYNAME', 'DOSAGEFORMNAME']
exact = pkg.merge(prod[['PRODUCTID'] + COLS], on='PRODUCTID').drop_duplicates('NDC').set_index('NDC')[COLS]
# fallback: a proxy NDC whose package is no longer listed takes its product's listing (first 9 digits)
prod['p9'] = prod.PRODUCTNDC.map(lambda s: s.split('-')[0].zfill(5) + s.split('-')[1].zfill(4))
by9 = prod.drop_duplicates('p9').set_index('p9')[COLS]
fndc = con.sql("select distinct NDC from f").df().NDC
m = exact.reindex(fndc)
miss = m.MARKETINGCATEGORYNAME.isna()
m.loc[miss] = by9.reindex(fndc[miss.values].str[:9]).values
print(f'proxy NDCs: {len(fndc):,}; by package {(~miss).sum():,}; by product code {m.MARKETINGCATEGORYNAME.notna().sum() - (~miss).sum():,}; '
      f'not in directory {m.MARKETINGCATEGORYNAME.isna().sum():,}')
m = m.rename_axis('NDC').reset_index()

# Drugs@FDA: first original ANDA approval per active ingredient + form
app = pd.read_csv(D + 'Applications.txt', sep='\t', dtype=str, encoding='latin-1')
sub = pd.read_csv(D + 'Submissions.txt', sep='\t', dtype=str, encoding='latin-1')
dp = pd.read_csv(D + 'Products.txt', sep='\t', dtype=str, encoding='latin-1', on_bad_lines='skip')
anda = set(app.loc[app.ApplType == 'ANDA', 'ApplNo'])
orig = sub[(sub.SubmissionType == 'ORIG') & (sub.SubmissionStatus == 'AP') & sub.ApplNo.isin(anda)]
orig = orig.assign(appr=pd.to_datetime(orig.SubmissionStatusDate)).groupby('ApplNo').appr.min()
dp = dp[dp.ApplNo.isin(anda)][['ApplNo', 'ActiveIngredient', 'Form']].drop_duplicates()
dp['appr'] = dp.ApplNo.map(orig)
first = dp.groupby(['ActiveIngredient', 'Form']).appr.min().rename('first_generic')
appl_first = dp.join(first, on=['ActiveIngredient', 'Form']).groupby('ApplNo').first_generic.min()

# placements: plan x generic product, 5- and 6-tier formularies only
con.register('m', m[['NDC', 'MARKETINGCATEGORYNAME', 'APPLICATIONNUMBER', 'NONPROPRIETARYNAME', 'DOSAGEFORMNAME']])
pl = con.sql("""select p.CONTRACT_ID, p.PLAN_ID, p.SEGMENT_ID, f.RXCUI, f.NDC, f.tier, fm.n_tiers
                from p join fm using (FORMULARY_ID) join f using (FORMULARY_ID) join m using (NDC)
                where fm.n_tiers in (5, 6) and m.MARKETINGCATEGORYNAME = 'ANDA'""").df()
pl['brand_tier'] = pl.tier.isin([3, 4, 5])
n_plans = con.sql("select count(*) from p join fm using (FORMULARY_ID) where n_tiers in (5, 6)").fetchone()[0]

g = (pl.groupby(['RXCUI', 'NDC'])
       .agg(plans=('tier', 'size'), t3=('tier', lambda s: (s == 3).sum()), t4=('tier', lambda s: (s == 4).sum()),
            t5=('tier', lambda s: (s == 5).sum()), brand=('brand_tier', 'sum')).reset_index())
g = g.merge(m[['NDC', 'APPLICATIONNUMBER', 'NONPROPRIETARYNAME', 'DOSAGEFORMNAME']], on='NDC', how='left')
g['first_generic'] = g.APPLICATIONNUMBER.str.replace('ANDA', '').map(appl_first)
g['yrs'] = (AS_OF - g.first_generic).dt.days / 365.25
g['share_brand'] = g.brand / g.plans
g.to_csv('data/work/generic_tiers.csv', index=False)

print(f'plans on 5- or 6-tier formularies: {n_plans:,}')
print(f'generic (ANDA) products on at least one of those formularies: {len(g):,}')
print(f'plan placements: {len(pl):,}; on tier 3-5: {pl.brand_tier.sum():,} ({pl.brand_tier.mean():.1%})')
print('  by tier:', pl.tier.value_counts().sort_index().to_dict())
for cut in (0.5, 0.9):
    print(f'products on tier 3-5 in at least {cut:.0%} of the plans that cover them: '
          f'{(g.share_brand >= cut).sum():,} ({(g.share_brand >= cut).mean():.1%})')
print(f'products on tier 3-5 in at least one plan: {(g.brand > 0).sum():,}')
print(f'first generic date found for {g.first_generic.notna().sum():,} of {len(g):,} products')
bins = [0, 2, 5, 10, 20, 100]
lab = ['under 2 years', '2 to 5', '5 to 10', '10 to 20', '20 or more']
g['age'] = pd.cut(g.yrs, bins, labels=lab, right=False)
t = g.groupby('age', observed=False).agg(products=('NDC', 'size'), placements=('plans', 'sum'), brand=('brand', 'sum'),
                                         majority=('share_brand', lambda s: (s >= 0.5).sum()))
t['pct_placements_brand'] = (100 * t.brand / t.placements).round(1)
t['pct_products_majority'] = (100 * t.majority / t.products).round(1)
print(t.to_string())

# ---------- chart data: dist/generic-tiers.html ----------
import json
brand = con.sql("""select count(distinct f.RXCUI) as products, count(*) as placements,
                   sum((f.tier = 3)::int) as t3, sum((f.tier in (4, 5))::int) as t45
                   from p join fm using (FORMULARY_ID) join f using (FORMULARY_ID) join m using (NDC)
                   where fm.n_tiers in (5, 6) and m.MARKETINGCATEGORYNAME in ('NDA', 'BLA')""").df().iloc[0]


def row(label, sub, gg, plc):
    return dict(label=label, sub=sub, products=int(len(gg)), placements=int(len(plc)),
                t3=round(100 * (plc.tier == 3).mean(), 2), t45=round(100 * plc.tier.isin([4, 5]).mean(), 2),
                majority=int((gg.share_brand >= 0.5).sum()))


pl = pl.merge(g[['RXCUI', 'age']], on='RXCUI', how='left')
rows = [dict(label='Brand-name drugs', sub='for comparison', products=int(brand.products), placements=int(brand.placements),
             t3=round(100 * brand.t3 / brand.placements, 2), t45=round(100 * brand.t45 / brand.placements, 2), majority=None, ref=True),
        row('All generic drugs', '', g, pl)]
for a in lab:
    rows.append(row(a if a != 'under 2 years' else 'Under 2 years', '',
                    g[g.age == a], pl[pl.age == a]))
for r in rows[2:]:
    r['label'] = {'2 to 5': '2 to 5 years', '5 to 10': '5 to 10 years', '10 to 20': '10 to 20 years',
                  '20 or more': '20 years or more'}.get(r['label'], r['label'])

# cost sharing by tier: initial coverage, 1-month retail (preferred pharmacy where offered), same plans
con.sql(f"""create table c as select b.CONTRACT_ID, b.PLAN_ID, b.SEGMENT_ID, cast(TIER as int) as tier,
            case when COST_TYPE_PREF <> '0' then COST_TYPE_PREF else COST_TYPE_NONPREF end as typ, DED_APPLIES_YN as ded
            from read_csv('{E}beneficiary cost file  PPUF_2026Q3.txt', delim='|', header=true, all_varchar=true) b
            where COVERAGE_LEVEL = '1' and DAYS_SUPPLY = '1'""")
cs = con.sql("""select c.tier, count(*) as plans, 100 * avg((typ = '2')::int) as pct_coins, 100 * avg((ded = 'Y')::int) as pct_ded
                from c join p using (CONTRACT_ID, PLAN_ID, SEGMENT_ID) join fm using (FORMULARY_ID)
                where n_tiers in (5, 6) group by 1 order by 1""").df()
print(cs.round(1).to_string(index=False))
cost = {int(r.tier): dict(coins=round(r.pct_coins), ded=round(r.pct_ded)) for r in cs.itertuples()}

tpl = open('scripts/viz20_template.html').read()
html = (tpl.replace('/*__DATA__*/[]', json.dumps(rows, separators=(',', ':')))
           .replace('/*__COST__*/{}', json.dumps(cost, separators=(',', ':')))
           .replace('__NPLANS__', f'{n_plans:,}')
           .replace('__LOGO__', open('assets/d4tp-logo.datauri').read().strip()))
open('dist/generic-tiers.html', 'w').write(html)
print(json.dumps(rows, indent=0))
