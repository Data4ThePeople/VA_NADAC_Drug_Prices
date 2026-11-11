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
        # Second check for a count set by the NADAC tie-break: (a) the VA package field gives the item count
        # and the FDA text gives the volume per item; their product must equal the count used; (b) the VA price
        # per unit at that count must sit within 10% of the same drug's per-unit VA price on packages whose
        # count two or more sources agree on.
        vol = re.search(r'/ ([\d.]+) mL in 1', str(r.PACKAGEDESCRIPTION))
        items = pd.to_numeric(str(r.va_pkg).strip(), errors='coerce')
        a_ok = vol is not None and pd.notna(items) and abs(items * float(vol.group(1)) - r.qty) < 1e-9
        peers = cmp_[(cmp_.family == r.family) & (cmp_.NDC != r.NDC) & (cmp_.qty_src.str.contains(r'\+'))]
        peer = (peers.Big4 / peers.qty).median()
        b_ok = pd.notna(peer) and abs((r.Big4 / r.qty) / peer - 1) <= 0.10
        out.append((f'qty tie-break {r.NDC} {r.va_name}: VA count x FDA mL per item = '
                    f'{items:g} x {vol.group(1) if vol else "?"}; VA $/unit {r.Big4 / r.qty:,.2f} vs agreed '
                    f'packages {peer:,.2f}', r.qty, r.qty_src, 'OK' if a_ok and b_ok else 'REVIEW'))
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
check('brands compared', 89, len(c))
check('brands VA higher', 9, int((c > 0).sum()))
check('median brand VA vs Part D (rounded to 0.1 pt)', -0.269, round(c.median(), 3))
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
k2['pd_raw'] = k2.brand.map(anc) * k2.brand.str.replace(r'\*+$', '', regex=True).str.strip().map(qt)  # Q1 file has no '*'
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

# ---------- F. generic tier chart (dist/generic-tiers.html), separate code path ----------
# pandas only; generic status from the FDA product file by labeler-product code (first 9 NDC digits)
# instead of the package file; first generic date by a plain dict pass over Drugs@FDA.
import json as _j2
SP = 'data/raw/spuf_2026q3/ex/'
fx = pd.read_csv(SP + 'basic drugs formulary file  PPUF_2026Q3.txt', sep='|', dtype=str,
                 usecols=['FORMULARY_ID', 'RXCUI', 'NDC', 'TIER_LEVEL_VALUE'])
fx['tier'] = fx.TIER_LEVEL_VALUE.astype(int)
px = pd.read_csv(SP + 'plan information  PPUF_2026Q3.txt', sep='|', dtype=str, encoding='latin-1',
                 usecols=['CONTRACT_ID', 'PLAN_ID', 'SEGMENT_ID', 'FORMULARY_ID']).drop_duplicates()
ntier = fx.groupby('FORMULARY_ID').tier.max()
px = px[px.FORMULARY_ID.map(ntier).isin([5, 6])]
check('generic tiers: plans on 5- or 6-tier formularies', 5295, len(px))
pr = pd.read_csv('data/raw/fda_ndc/product.txt', sep='\t', dtype=str, encoding='latin-1')
pr['p9'] = pr.PRODUCTNDC.map(lambda s: s.split('-')[0].zfill(5) + s.split('-')[1].zfill(4))
cat9 = pr.drop_duplicates('p9').set_index('p9')
fx['cat'] = fx.NDC.str[:9].map(cat9.MARKETINGCATEGORYNAME)
fx['appl'] = fx.NDC.str[:9].map(cat9.APPLICATIONNUMBER)
plx = px.merge(fx, on='FORMULARY_ID')
gen = plx[plx.cat == 'ANDA']
# first generic approval by active ingredient + form
apps = pd.read_csv('data/raw/drugsatfda/ex/Applications.txt', sep='\t', dtype=str, encoding='latin-1')
andas = set(apps.ApplNo[apps.ApplType == 'ANDA'])
subs = pd.read_csv('data/raw/drugsatfda/ex/Submissions.txt', sep='\t', dtype=str, encoding='latin-1')
apdate = {}
for a, t, st, d in zip(subs.ApplNo, subs.SubmissionType, subs.SubmissionStatus, subs.SubmissionStatusDate):
    if a in andas and t == 'ORIG' and st == 'AP':
        apdate[a] = min(apdate.get(a, d), d)
prods = pd.read_csv('data/raw/drugsatfda/ex/Products.txt', sep='\t', dtype=str, encoding='latin-1', on_bad_lines='skip')
firstd, keys = {}, {}
for a, ing, frm in zip(prods.ApplNo, prods.ActiveIngredient, prods.Form):
    if a in andas and a in apdate:
        firstd[(ing, frm)] = min(firstd.get((ing, frm), apdate[a]), apdate[a])
        keys.setdefault(a, set()).add((ing, frm))
fg = {a: min(firstd[k] for k in ks) for a, ks in keys.items()}
yrs = gen.drop_duplicates('RXCUI').set_index('RXCUI').appl.str.replace('ANDA', '').map(fg)
yrs = (pd.Timestamp('2026-10-01') - pd.to_datetime(yrs)).dt.days / 365.25
gen = gen.assign(yrs=gen.RXCUI.map(yrs))
grp = {'Brand-name drugs': plx[plx.cat.isin(['NDA', 'BLA'])], 'All generic drugs': gen}
for lab_, lo_, hi_ in [('Under 2 years', 0, 2), ('2 to 5 years', 2, 5), ('5 to 10 years', 5, 10),
                       ('10 to 20 years', 10, 20), ('20 years or more', 20, 100)]:
    grp[lab_] = gen[(gen.yrs >= lo_) & (gen.yrs < hi_)]
built20 = {d['label']: d for d in _j2.loads(re.search(r'const DATA = (\[.*?\]);', open('dist/generic-tiers.html').read()).group(1))}
for lab_, d in grp.items():
    bd = built20[lab_]
    check(f'generic tiers {lab_}: products', bd['products'], d.RXCUI.nunique())
    check(f'generic tiers {lab_}: plan listings', bd['placements'], len(d))
    check(f'generic tiers {lab_}: tier 3 %', bd['t3'], round(100 * (d.tier == 3).mean(), 2), 0.05)
    check(f'generic tiers {lab_}: tiers 4-5 %', bd['t45'], round(100 * d.tier.isin([4, 5]).mean(), 2), 0.05)

# ---------- G. rebate chart (dist/part-d-rebates.html): values re-read from the Trustees Report PDF ----------
from pypdf import PdfReader
_tr = PdfReader('data/raw/trustees_2026/2026-medicare-trustees-report.pdf')
_page = next(pg.extract_text() for pg in _tr.pages if 'Table IV.B8.—Key Factors for Part D Expenditure Estimates1' in (pg.extract_text() or ''))
_dir = {int(m.group(1)): float(m.group(2)) for m in re.finditer(r'^(20[12]\d)\s+[−\-]?[\d.]+\s*%?\s+([\d.]+)\s*%?\s+[\d.]+', _page, re.M)}
built19 = {d['year']: d for d in _j2.loads(re.search(r'const DATA = (\[.*?\]);', open('dist/part-d-rebates.html').read()).group(1))}
for yr_, d in built19.items():
    check(f'rebate chart {yr_} DIR %', d['pct'], _dir.get(yr_))
check('rebate chart: estimates are 2025 and 2026', 1, int({y for y, d in built19.items() if d['est']} == {2025, 2026}))

# ---------- H. patient cost chart (dist/patient-cost.html): month-by-month simulation ----------
built21 = _j2.loads(re.search(r'const DATA = (\[.*?\]);', open('dist/patient-cost.html').read()).group(1))
mfr = pd.read_csv('data/raw/cms_mfp/ex/CMS_Negotiation_Program_Selected_Drug_List_and_Maximum_Fair_Price_Data_File_20261102.csv', dtype=str)
mfr = mfr[(pd.to_datetime(mfr['MFP Effective Date']) <= '2026-11-01')
          & (pd.to_datetime(mfr['MFP End Date']).fillna(pd.Timestamp('2099-12-31')) >= '2026-11-01')]
mfr['m30'] = mfr['Single MFP per 30 DES'].str.replace(r'[$,]', '', regex=True).astype(float)
top10 = b[b.status == 'compared'].nlargest(10, 'spending_2024').family.tolist()
check('patient chart: drugs are the top 10 by 2024 spending', 1,
      int([d['name'].lower() for d in built21] == [f.lower() for f in top10]))
month_pk = {}
for d in built21:
    fam = d['name'].lower()
    if d['neg']:
        p30 = mfr[mfr['Selected Drug Name'].str.upper().str.startswith(d['name'].upper())].m30.unique()
        check(f'patient chart {d["name"]}: 30-day price = CMS negotiated', d['price'], float(p30[0]) if len(p30) == 1 else None, 0.005)
    else:
        q, days = {'ozempic': (3, 28), 'mounjaro': (2, 28), 'trulicity': (2, 28), 'trelegy': (60, 30), 'revlimid': (21, 28),
                   'humira': (2, 28)}[fam]
        pk = n[(n.family == fam) & (n.qty == q) & n.big4_vs_partd.notna() & ~n.unit_flag]
        if fam == 'ozempic':
            pk = pk[pk.unit == 'ML']
        if fam == 'mounjaro':  # 2.5 mg is a starting dose only
            pk = pk[~pk.va_name.str.contains(r'\b2\.5 ?MG', na=False)]
        if fam == 'humira':  # 40 mg every other week
            pk = pk[pk.va_name.str.contains('40MG', na=False)]
        month_pk[fam] = (pk, days)
        check(f'patient chart {d["name"]}: 30-day price', d['price'], round((pk.partd_unit * pk.qty).median() * 30 / days, 2), 0.005)
    # simulate 12 fills under the 2026 standard benefit
    paid, ded_left, fills = 0.0, 615.0, []
    for _ in range(12):
        pay = min(d['price'], ded_left) + 0.25 * max(0.0, d['price'] - ded_left)
        ded_left = max(0.0, ded_left - d['price'])
        pay = min(pay, 2100.0 - paid); paid += pay; fills.append(pay)
    check(f'patient chart {d["name"]}: first fill', d['in_ded'], round(fills[0], 2), 0.011)
    check(f'patient chart {d["name"]}: year', d['year'], round(paid, 2), 0.011)
    after_sim = round(0.25 * d['price'], 2) if fills[0] < 2100 else 0.0
    check(f'patient chart {d["name"]}: fill after deductible', d['after'], min(after_sim, 2100.0), 0.011)

# real-plan figures in the patient chart, pandas path (fx/px from section F are plans on 5- or 6-tier formularies)
bc = pd.read_csv(SP + 'beneficiary cost file  PPUF_2026Q3.txt', sep='|', dtype=str)
bc = bc[(bc.COVERAGE_LEVEL == '1') & (bc.DAYS_SUPPLY == '1')].copy()
usep = bc.COST_TYPE_PREF != '0'
bc['typ'] = bc.COST_TYPE_PREF.where(usep, bc.COST_TYPE_NONPREF)
for c_ in ('AMT', 'MIN_AMT', 'MAX_AMT'):
    bc[c_] = bc[f'COST_{c_}_PREF'].where(usep, bc[f'COST_{c_}_NONPREF']).astype(float)
bc['TIER'] = bc.TIER.astype(int)
pded = pd.read_csv(SP + 'plan information  PPUF_2026Q3.txt', sep='|', dtype=str, encoding='latin-1',
                   usecols=['CONTRACT_ID', 'PLAN_ID', 'SEGMENT_ID', 'DEDUCTIBLE']).drop_duplicates(['CONTRACT_ID', 'PLAN_ID', 'SEGMENT_ID'])
for d in built21:
    fam = d['name'].lower()
    p9s = set(n.loc[n.family == fam, 'NDC'].str[:9])
    rows_ = fx[fx.NDC.str[:9].isin(p9s)].merge(px, on='FORMULARY_ID')
    t_ = rows_.groupby(['CONTRACT_ID', 'PLAN_ID', 'SEGMENT_ID']).tier.min().rename('TIER').reset_index()
    t_ = t_.merge(bc, on=['CONTRACT_ID', 'PLAN_ID', 'SEGMENT_ID', 'TIER']).merge(pded, on=['CONTRACT_ID', 'PLAN_ID', 'SEGMENT_ID'])
    # each plan's own 30-day price from the pricing file (non-negotiated drugs); else the chart's price
    if fam in month_pk:
        pk, days = month_pk[fam]
        qq = pk.groupby(pk.NDC.str[:9]).qty.median()
        pp = con.execute(f"""select CONTRACT_ID, PLAN_ID, SEGMENT_ID, substr(NDC, 1, 9) p9, cast(UNIT_COST as double) u
            from read_csv('{SP}pricing file PPUF_2026Q3.txt', delim='|', header=true, all_varchar=true)
            where DAYS_SUPPLY = '30' and substr(NDC, 1, 9) in ({','.join(repr(x) for x in qq.index)})""").df()
        pp['m'] = pp.u * pp.p9.map(qq) * 30 / days
        ownp = pp.groupby(['CONTRACT_ID', 'PLAN_ID', 'SEGMENT_ID']).m.median().rename('px').reset_index()
        t_ = t_.merge(ownp, on=['CONTRACT_ID', 'PLAN_ID', 'SEGMENT_ID'], how='left')
        t_['px'] = t_.px.fillna(d['price'])
    else:
        t_['px'] = d['price']
    cost = []
    for typ_, amt_, mn_, mx_, px_ in zip(t_.typ, t_.AMT, t_.MIN_AMT, t_.MAX_AMT, t_.px):
        v = amt_ if typ_ == '1' else amt_ * px_ if typ_ == '2' else float('nan')
        if typ_ == '2' and mx_ > 0: v = min(v, mx_)
        if typ_ == '2' and mn_ > 0: v = max(v, mn_)
        cost.append(min(v, 2100.0))
    check(f'patient chart {d["name"]}: real plans covering', d['rp_plans'], len(t_))
    check(f'patient chart {d["name"]}: real plans on tiers 3 to 5 %', d['rp_tier3'], round(100 * t_.TIER.between(3, 5).mean(), 1), 0.051)
    check(f'patient chart {d["name"]}: real plans coinsurance %', d['rp_coins'], round(100 * (t_.typ == '2').mean(), 1), 0.051)
    check(f'patient chart {d["name"]}: real plans deductible %', d['rp_ded'],
          round(100 * ((t_.DED_APPLIES_YN == 'Y') & (t_.DEDUCTIBLE.astype(float) > 0)).mean(), 1), 0.051)
    check(f'patient chart {d["name"]}: real plans median after deductible', d['rp_after'], round(float(pd.Series(cost).median()), 2), 0.011)

# Revlimid generic (lenalidomide) in the post: coverage and tiers, pandas path
len_rx = set(fx.loc[(fx.cat == 'ANDA') & fx.NDC.str[:9].map(cat9.NONPROPRIETARYNAME).str.contains('lenalidomide', case=False, na=False), 'RXCUI'])
lt = fx[fx.RXCUI.isin(len_rx)].merge(px, on='FORMULARY_ID').groupby(['CONTRACT_ID', 'PLAN_ID', 'SEGMENT_ID']).tier.min()
check('lenalidomide generic: plans covering', 5295, len(lt))
check('lenalidomide generic: plans on tier 5', 5283, int((lt == 5).sum()))
check('lenalidomide generic: plans on tier 4', 12, int((lt == 4).sum()))
check('lenalidomide generic: plans on tiers 1, 2 or 6', 0, int(lt.isin([1, 2, 6]).sum()))
lc = lt.rename('TIER').reset_index().merge(bc, on=['CONTRACT_ID', 'PLAN_ID', 'SEGMENT_ID', 'TIER'])
check('lenalidomide generic: coinsurance %', 99.4, round(100 * (lc.typ == '2').mean(), 1), 0.051)
check('lenalidomide generic: median coinsurance rate', 0.25, lc[lc.typ == '2'].AMT.median())
check('lenalidomide generic: lowest coinsurance rate (post: 25% to 33%)', 0.25, lc[lc.typ == '2'].AMT.min())
check('lenalidomide generic: highest coinsurance rate (post: 25% to 33%)', 0.33, round(lc[lc.typ == '2'].AMT.max(), 2))
# each plan's own price per capsule (median over its lenalidomide ANDA products, 30-day), 21-capsule cycle,
# first and second fill with the plan's deductible and cost sharing, capped at $2,100
len9 = sorted(set(fx.loc[fx.RXCUI.isin(len_rx), 'NDC'].str[:9]) | set(cat9[cat9.NONPROPRIETARYNAME.str.contains('lenalidomide', case=False, na=False)
                                                                         & (cat9.MARKETINGCATEGORYNAME == 'ANDA')].index))
lp = con.execute(f"""select CONTRACT_ID, PLAN_ID, SEGMENT_ID, NDC, cast(UNIT_COST as double) u
    from read_csv('{SP}pricing file PPUF_2026Q3.txt', delim='|', header=true, all_varchar=true)
    where DAYS_SUPPLY = '30' and substr(NDC, 1, 9) in ({','.join(repr(x) for x in len9)})""").df()
lnat = lp.groupby('NDC').u.median().median()
lo = lp.groupby(['CONTRACT_ID', 'PLAN_ID', 'SEGMENT_ID']).u.median().rename('unit').reset_index()
lc = lc.merge(pded, on=['CONTRACT_ID', 'PLAN_ID', 'SEGMENT_ID']).merge(lo, on=['CONTRACT_ID', 'PLAN_ID', 'SEGMENT_ID'], how='left')
lc['own'] = lc.unit.notna()
lc['unit'] = lc.unit.fillna(lnat)
f1, f2 = [], []
for r_ in lc.itertuples():
    cyc = 21 * r_.unit
    dl = float(r_.DEDUCTIBLE) if (r_.DED_APPLIES_YN == 'Y' and float(r_.DEDUCTIBLE) > 0) else 0.0
    paid, pays = 0.0, []
    for _ in range(2):
        ind = min(cyc, dl); dl -= ind
        rest = cyc - ind
        if r_.typ == '1':
            sh = min(r_.AMT, rest)
        else:
            sh = r_.AMT * rest
            if r_.MAX_AMT > 0: sh = min(sh, r_.MAX_AMT)
            if r_.MIN_AMT > 0: sh = max(sh, r_.MIN_AMT)
            sh = min(sh, rest)
        pay = min(ind + (sh if rest > 0 else 0.0), 2100.0 - paid); paid += pay; pays.append(paid)
    f1.append(pays[0]); f2.append(pays[1])
lc['f1'], lc['f2'] = f1, f2
check('lenalidomide generic: own price, % of plans with cost rows', 100.0, round(100 * lc.own.mean(), 1), 0.051)
check('lenalidomide generic: median 21-capsule cycle at plan price (post: about $6,600)', 6600,
      round(float((21 * lc.unit).median()), -2))
check('lenalidomide generic: % of plans reaching $2,100 on the first fill (post: about half)', 50.1,
      round(100 * (lc.f1 >= 2099.995).mean(), 1), 0.051)
check('lenalidomide generic: % of plans reaching $2,100 by the second fill (post: 85%)', 85,
      round(100 * (lc.f2 >= 2099.995).mean()), 0)
lw = pd.read_csv('data/work/lenalidomide.csv', dtype={'PLAN_ID': str, 'SEGMENT_ID': str})
check('lenalidomide generic: scripts/lenalidomide.py first fill median', round(float(lw.loc[lw.typ.notna(), 'fill1'].median()), 2),
      round(float(lc.f1.median()), 2), 0.011)
check('Revlimid brand: plans covering', 225, [d for d in built21 if d['name'] == 'Revlimid'][0]['rp_plans'])

r = pd.DataFrame(out, columns=['check', 'built', 'recomputed', 'result'])
r.to_csv('data/work/tieout_claude.csv', index=False)
pd.set_option('display.width', 220)
pd.set_option('display.max_colwidth', 120)
print(r.result.value_counts().to_string())
print(r[r.result != 'OK'].to_string(index=False))
