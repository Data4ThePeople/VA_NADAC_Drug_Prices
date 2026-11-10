"""Claude's own tie-out. Recomputes the built numbers from raw files with separate code paths and
reports every difference. Run from the project root after top100.py and basket.py."""
import re
import duckdb
import pandas as pd

TOL = 1e-6
out = []


def check(name, built, recomputed, tol=TOL, rel=False):
    if pd.isna(built) and pd.isna(recomputed):
        ok = True
    elif pd.isna(built) or pd.isna(recomputed):
        ok = False
    else:
        diff = abs(built - recomputed) / (abs(recomputed) if rel and recomputed else 1)
        ok = diff <= tol
    out.append((name, built, recomputed, 'OK' if ok else 'DIFF'))
    return ok


b = pd.read_csv('data/work/top100_brand.csv')
n = pd.read_csv('data/work/top100_ndc.csv', dtype={'NDC': str})
k = pd.read_csv('data/work/basket.csv')

# ---------- A. ranking: claims per brand from the raw annual file ----------
an = pd.read_csv('data/raw/partd_spending_2024/DSD_PTD_RY26_P04_V10_DY24_BGM.csv')
an = an[an.Mftr_Name == 'Overall']
bad = 0
for f, names, c in zip(b.family, b.brand_names, b.claims_2024):
    raw = an[an.Brnd_Name.isin(names.split('; '))].Tot_Clms_2024.sum()
    bad += not check(f'claims_2024 {f}', c, raw)
check('rank order is descending by claims', 1, int(b.claims_2024.is_monotonic_decreasing))
# every CMS brand row whose first word is a top family must be in that family's list
for f, names in zip(b.family, b.brand_names):
    fw = an.Brnd_Name.str.lower().str.replace(r'[^a-z ]', ' ', regex=True).str.split().str[0]
    missing = set(an[(fw == f) & (an.Brnd_Name.str.lower().str.replace(r'[^a-z0-9]', '', regex=True)
                                 != an.Gnrc_Name.str.lower().str.replace(r'[^a-z0-9]', '', regex=True))].Brnd_Name) - set(names.split('; '))
    if missing:  # expected only for rows Drugs@FDA lists only under ANDAs (checked in C2)
        out.append((f'rows starting with "{f}" not counted', '', '; '.join(sorted(missing)), 'INFO'))
check('one row per brand in brand file', len(b), b.family.nunique())
check('no CMS row counted in two brands', 0, int(pd.Series([nm for x in b.brand_names for nm in x.split('; ')]).duplicated().sum()))
check('one row per NDC in NDC file', len(n), n.NDC.nunique())

# ---------- B. per-NDC prices from raw files ----------
va = pd.read_excel('data/raw/va/TPharmPrices-11-01-2026.xlsx', dtype={'NDCWithDashes': str})
va['ndc'] = va.NDCWithDashes.str.replace('-', '', regex=False)
va['start'] = pd.to_datetime(va.PriceStartDate, format='%m/%d/%Y')
va['stop'] = pd.to_datetime(va.PriceStopDate, format='%m/%d/%Y')
cur = va[(va.start <= '2026-11-01') & (va.stop >= '2026-11-01') & (va.Price > 0.01)]
big4 = cur[cur.PriceType == 'Big4'].groupby('ndc').Price.min()

con = duckdb.connect()
con.execute('set enable_progress_bar=false')
ndcs = list(set(n.NDC) | set(n.NDC.str[:9]))
med = con.execute("""
    select NDC, median(cast(UNIT_COST as double)) m
    from read_csv('data/raw/spuf_2026q3/ex/pricing file PPUF_2026Q3.txt', delim='|', header=true, all_varchar=true)
    where DAYS_SUPPLY = '30' group by NDC""").df().set_index('NDC').m
prod_med = med.groupby(med.index.str[:9]).median()

cmp_ = n[n.big4_vs_partd.notna() & ~n.unit_flag]
nb = npd = 0
for r in cmp_.itertuples():
    nb += not check(f'Big4 {r.NDC}', r.Big4, big4.get(r.NDC))
    raw_pd = med.get(r.NDC, prod_med.get(r.NDC[:9]))
    npd += not check(f'Part D unit {r.NDC}', r.partd_unit, raw_pd, 1e-9, rel=True)
    check(f'ratio {r.NDC}', r.big4_vs_partd, (r.Big4 / r.qty) / raw_pd - 1, 1e-9)
# package quantity: every compared NDC must have a count agreed by two sources (or the NADAC tie-break),
# and the agreed count must equal at least two of FDA / VA / CMS rebate file
for r in cmp_.itertuples():
    srcs = [v for v in (r.fda_qty, r.va_qty, r.mdrp_q) if pd.notna(v)]
    agree = sum(abs(v - r.qty) <= 0.01 * r.qty for v in srcs)
    if agree < 2:
        out.append((f'qty single-source {r.NDC} {r.va_name}', r.qty, r.qty_src, 'REVIEW'))
check('compared NDCs with qty from 2+ sources', len(cmp_) - 2,
      int(sum(sum(abs(v - q) <= 0.01 * q for v in (a, b_, c_) if pd.notna(v)) >= 2
              for q, a, b_, c_ in zip(cmp_.qty, cmp_.fda_qty, cmp_.va_qty, cmp_.mdrp_q))))

# ---------- C. external check: Part D unit price vs CMS per-unit negotiated price (MFP) ----------
# CMS MFP data file (Nov 2, 2026): one row per NDC-11 and effective period, MFP per unit by NDC-9.
mf = pd.read_csv('data/raw/cms_mfp/ex/CMS_Negotiation_Program_Selected_Drug_List_and_Maximum_Fair_Price_Data_File_20261102.csv', dtype=str)
mf['eff'] = pd.to_datetime(mf['MFP Effective Date'])
mf['end'] = pd.to_datetime(mf['MFP End Date']).fillna(pd.Timestamp('2099-12-31'))
mf = mf[(mf.eff <= '2026-11-01') & (mf.end >= '2026-11-01')]
mf['p9'] = mf['NDC-9'].str.replace('-', '')
mf['mfp_unit'] = mf['NDC-9 MFP per Unit Price'].str.replace(r'[$,]', '', regex=True).astype(float)
mfp9 = mf.groupby('p9').mfp_unit.agg(['min', 'max'])
check('MFP file: one per-unit price per NDC-9 on Nov 1, 2026', 0, int((mfp9['min'] != mfp9['max']).sum()))
neg_fams = {'eliquis', 'jardiance', 'xarelto', 'januvia', 'farxiga', 'entresto', 'enbrel', 'novolog', 'fiasp'}
for r in cmp_[cmp_.family.isin(neg_fams)].itertuples():
    m = mfp9['min'].get(r.NDC[:9])
    if m is None:  # NovoLog Mix 70/30 is not a selected drug
        out.append((f'Part D unit vs MFP {r.NDC} {r.va_name}', r.partd_unit, 'not on CMS MFP list', 'INFO'))
    else:  # Part D unit costs carry 4 decimals; MFP per unit carries 6
        check(f'Part D unit = MFP per unit {r.NDC} {r.va_name}', r.partd_unit, m, 1e-4)
# Part D unit price must never exceed the MFP (CMS caps it)
check('compared negotiated NDCs with Part D unit above MFP', 0,
      int(sum(r.partd_unit > mfp9['min'].get(r.NDC[:9], 1e18) + 1e-4 for r in cmp_.itertuples())))

# 30-day chart (dist/negotiated-30day.html): VA 30-day = Big4 from the xlsx / package qty x units in CMS's
# 30-day supply (30-day MFP / per-unit MFP for the NDC-9), median across packages; Part D 30-day = CMS 30-day MFP
mf['m30'] = mf['Single MFP per 30 DES'].str.replace(r'[$,]', '', regex=True).astype(float)
m30 = mf.drop_duplicates('p9').set_index('p9')
neg_c = cmp_[cmp_.NDC.str[:9].isin(m30.index)].copy()
neg_c['va30'] = [big4.get(nd) / q * m30.loc[nd[:9], 'm30'] / m30.loc[nd[:9], 'mfp_unit'] for nd, q in zip(neg_c.NDC, neg_c.qty)]
import json as _j
chart = {d['name'].lower(): d for d in _j.loads(re.search(r'const DATA = (\[.*?\]);', open('dist/negotiated-30day.html').read()).group(1))}
for f, g in neg_c.groupby('family'):
    check(f'30-day VA {f}', chart[f]['va30'], round(g.va30.median(), 2), 0.006)
    check(f'30-day Part D = CMS 30-day MFP {f}', chart[f]['pd30'], m30.loc[g.NDC.iloc[0][:9], 'm30'], 0.01 * chart[f]['pd30'])

# ---------- C2. Drugs@FDA: every compared NDC traces to an NDA or BLA (separate code path) ----------
fp = pd.read_csv('data/raw/fda_ndc/product.txt', sep='\t', dtype=str, encoding='latin-1')
fk = pd.read_csv('data/raw/fda_ndc/package.txt', sep='\t', dtype=str, encoding='latin-1')
fk['ndc'] = fk.NDCPACKAGECODE.map(lambda d: ''.join(x.zfill(w) for x, w in zip(d.split('-'), (5, 4, 2))))
an_no = fk.merge(fp, on='PRODUCTID').drop_duplicates('ndc').set_index('ndc').APPLICATIONNUMBER
dapp = pd.read_csv('data/raw/drugsatfda/ex/Applications.txt', sep='\t', dtype=str, encoding='latin-1').set_index('ApplNo').ApplType
dprd = pd.read_csv('data/raw/drugsatfda/ex/Products.txt', sep='\t', dtype=str, encoding='latin-1', on_bad_lines='skip')
for r in cmp_.itertuples():
    a = an_no.get(r.NDC)
    t = dapp.get(re.sub(r'\D', '', a).zfill(6)) if isinstance(a, str) else None
    if t is None:  # not in the NDC Directory: Drugs@FDA applications whose product name starts with the brand
        apps = dprd[dprd.DrugName.str.upper().str.startswith(r.family.upper(), na=False)].ApplNo.unique()
        ts = {dapp.get(x) for x in apps}
        t = ts.pop() if len(ts) == 1 else None
        out.append((f'Drugs@FDA by brand name {r.NDC} {r.va_name}', '', t, 'INFO'))
    check(f'NDA/BLA {r.NDC}', 1, int(t in ('NDA', 'BLA')))
# no counted CMS brand row may be a name Drugs@FDA lists only under ANDAs
key = lambda x: re.sub(r'[^a-z0-9]', '', str(x).lower())
dtypes_by_name = dprd.merge(dapp.rename('ApplType'), left_on='ApplNo', right_index=True).groupby(
    dprd.DrugName.map(key)).ApplType.agg(set)
counted = [nm for names in b.brand_names for nm in names.split('; ')]
check('counted CMS rows that are ANDA-only in Drugs@FDA', 0,
      sum(dtypes_by_name.get(key(nm), set()) == {'ANDA'} for nm in counted))

# ---------- D. brand-level stats ----------
c = cmp_.groupby('family').big4_vs_partd.median()
bc = b[b.status == 'compared'].set_index('family')
for f in c.index:
    check(f'brand median {f}', bc.loc[f, 'big4_vs_partd_median'], c[f], 1e-12)
check('brands compared', 90, len(c))
check('brands VA higher', 9, int((c > 0).sum()))
check('median brand VA vs Part D (rounded to 0.1 pt)', -0.271, round(c.median(), 3))
out.append(('brands VA higher (list)', '', ', '.join(sorted(c[c > 0].index)), 'INFO'))

# ---------- E. basket from raw spending files ----------
qt = pd.read_csv('data/raw/partd_spending_2026q1/QDD_PTD_RQ2603_P01_V10_DQT2601_20260708.csv')
qt = qt[(qt.Mftr_Name == 'Overall') & (qt.Year == '2026 (Q1)')]
# some brand names appear on more than one Overall row (different generics); none may be in the basket
names = set(k.brand)
check('basket names duplicated in annual file', 0, int(an[an.Brnd_Name.duplicated(keep=False)].Brnd_Name.isin(names).sum()))
check('basket names duplicated in 2026 Q1 file', 0, int(qt[qt.Brnd_Name.duplicated(keep=False)].Brnd_Name.isin(names).sum()))
qt = qt.drop_duplicates('Brnd_Name').set_index('Brnd_Name').Avg_Spnd_Per_Clm
anc = an.drop_duplicates('Brnd_Name').set_index('Brnd_Name').Tot_Clms_2024
k2 = k.copy()
k2['pd_raw'] = k2.brand.map(anc) * k2.brand.map(qt)
k2['va_raw'] = k2.pd_raw * (1 + k2.big4_vs_partd)
for r in k2[k2.in_basket].itertuples():
    check(f'basket Part D {r.brand}', r.partd_cost, r.pd_raw, 1e-9, rel=True)
inb = k2[k2.in_basket]
NEG = inb.negotiated_2026
for label, d in [('all', inb), ('negotiated', inb[NEG]), ('other', inb[~NEG])]:
    check(f'basket {label} Part D $B', round(d.partd_cost.sum() / 1e9, 2), round(d.pd_raw.sum() / 1e9, 2))
    check(f'basket {label} VA $B', round(d.va_cost.sum() / 1e9, 2), round(d.va_raw.sum() / 1e9, 2))
    out.append((f'basket {label} VA vs Part D', '', f'{d.va_raw.sum() / d.pd_raw.sum() - 1:+.1%}', 'INFO'))
check('basket brand count', 89, inb.family.nunique())
# the negotiated flag must equal the CMS 2026 list (Imbruvica, Stelara not in top 100)
neg_list = {'eliquis', 'jardiance', 'xarelto', 'januvia', 'farxiga', 'entresto', 'enbrel', 'novolog', 'fiasp',
            'imbruvica', 'stelara'}
check('negotiated flag matches CMS list', 1,
      int(set(k.loc[k.negotiated_2026, 'family']) == (neg_list & set(k.family))))
check('NovoLog Mix rows not flagged negotiated', 0, int(k[k.brand.str.upper().str.contains('MIX') & k.negotiated_2026].shape[0]))

r = pd.DataFrame(out, columns=['check', 'built', 'recomputed', 'result'])
r.to_csv('data/work/tieout_claude.csv', index=False)
pd.set_option('display.width', 220)
pd.set_option('display.max_colwidth', 120)
print(r.result.value_counts().to_string())
print(r[r.result != 'OK'].to_string(index=False))
