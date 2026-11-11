"""Top 100 brand drugs in Medicare Part D (2024 claims), priced per unit:
VA Big4 (Nov 1, 2026 VA file) vs median Part D plan unit cost (2026 Q3 SPUF pricing file, 30-day).

Usage: python scripts/top100.py   (paths below are relative to the project root)
Outputs: data/work/top100_ndc.csv (one row per NDC), data/work/top100_brand.csv (one row per brand)
"""
import re
import duckdb
import pandas as pd

SPEND = 'data/raw/partd_spending_2024/DSD_PTD_RY26_P04_V10_DY24_BGM.csv'
SPUF = 'data/raw/spuf_2026q3/ex/pricing file PPUF_2026Q3.txt'
VA = 'data/raw/va/va_2026-11-01.csv'
FDA_PROD = 'data/raw/fda_ndc/product.txt'
FDA_PKG = 'data/raw/fda_ndc/package.txt'
NADAC = 'data/raw/nadac/nadac_2026.csv'
MDRP = 'data/raw/mdrp/drugproducts-q2-2026.csv'
DAFDA = 'data/raw/drugsatfda/ex/'
ASOF = pd.Timestamp('2026-11-01')


def fam(name):
    """Brand family key: first word of the name, letters only."""
    w = re.sub(r'[^a-z ]', ' ', str(name).lower()).split()
    return w[0] if w else ''


def ndc11(dashed):
    """FDA dashed NDC (4-4-2, 5-3-2, 5-4-1) to 11 digits."""
    a, b, c = dashed.split('-')
    return a.zfill(5) + b.zfill(4) + c.zfill(2)


# ---------- 1. FDA: brand products and NDC package quantities ----------
prod = pd.read_csv(FDA_PROD, sep='\t', dtype=str, encoding='latin-1')
prod = prod[prod.PRODUCTTYPENAME.str.contains('PRESCRIPTION', na=False)]
prod['family'] = prod.PROPRIETARYNAME.map(fam)
prod['is_brand'] = (prod.MARKETINGCATEGORYNAME.isin(['NDA', 'BLA'])
                    & (prod.family != prod.NONPROPRIETARYNAME.map(fam)))
# A brand family needs at least one such product sold under its application's own drug name in Drugs@FDA.
# This drops "PEG-3350, Electrolytes, and Ascorbate", an unbranded product under MoviPrep's NDA 021881.
_dp = pd.read_csv(DAFDA + 'Products.txt', sep='\t', dtype=str, encoding='latin-1', on_bad_lines='skip')
_appl_names = _dp.assign(a=_dp.ApplNo.str.lstrip('0'), f=_dp.DrugName.map(fam)).groupby('a').f.agg(set)
prod['name_ok'] = [f in _appl_names.get(re.sub(r'^\D+', '', str(a)).lstrip('0'), set())
                   for f, a in zip(prod.family, prod.APPLICATIONNUMBER)]
brand_fams = set(prod.loc[prod.is_brand & prod.name_ok, 'family'])

pkg = pd.read_csv(FDA_PKG, sep='\t', dtype=str, encoding='latin-1')
pkg = pkg.merge(prod[['PRODUCTID', 'family', 'is_brand', 'PROPRIETARYNAME', 'DOSAGEFORMNAME', 'APPLICATIONNUMBER']],
                on='PRODUCTID')
pkg['NDC'] = pkg.NDCPACKAGECODE.map(ndc11)
pkg['is_kit'] = pkg.PACKAGEDESCRIPTION.str.contains(r'\bKIT\b', na=False) & pkg.PACKAGEDESCRIPTION.str.contains(r'\*', na=False, regex=True)

SEG = re.compile(r'^\s*([\d.]+)\s+(.+?)\s+in\s+1\s+', re.I)


def qty(desc, unit):
    """Package quantity in NCPDP billing unit (EA, ML, GM) from the FDA package description."""
    counts, amount = [], None
    for seg in str(desc).split(' / '):
        m = SEG.match(seg)
        if not m:
            return None
        n, what = float(m.group(1)), m.group(2).strip().lower()
        if what in ('ml', 'g', 'kg', 'l', 'mg'):
            amount = (what, n)
            break
        counts.append(n)
    prodc = 1.0
    for n in counts:
        prodc *= n
    if unit == 'EA':
        return prodc
    if amount is None:
        return None
    u, n = amount
    if unit == 'ML' and u == 'ml':
        return prodc * n
    if unit == 'GM' and u == 'g':
        return prodc * n
    return None


# ---------- 2. Part D utilization 2024: rank brand families ----------
sp = pd.read_csv(SPEND)
sp = sp[sp.Mftr_Name == 'Overall'].copy()
sp['family'] = sp.Brnd_Name.map(fam)
sp = sp[(sp.family != sp.Gnrc_Name.map(fam)) & sp.family.isin(brand_fams)]
# the brand's FDA products must contain the CMS generic's first ingredient word. FDA leaves SUBSTANCENAME
# blank on some products (Humira, Paxlovid); those use NONPROPRIETARYNAME instead.
subs = (prod[prod.is_brand].assign(ingr=lambda d: d.SUBSTANCENAME.fillna(d.NONPROPRIETARYNAME))
        .groupby('family').ingr.agg(lambda x: ' '.join(x.dropna()).lower()))
sp = sp[[fam(g) in subs.get(f, '') for f, g in zip(sp.family, sp.Gnrc_Name)]]
# Drugs@FDA: drop a CMS brand row whose exact name is approved only under ANDAs (a generic sold under a
# brand-style name, e.g. Klor-Con M20). Rows with no exact name match in Drugs@FDA are kept.
d_app = pd.read_csv(DAFDA + 'Applications.txt', sep='\t', dtype=str, encoding='latin-1')
d_prod = pd.read_csv(DAFDA + 'Products.txt', sep='\t', dtype=str, encoding='latin-1', on_bad_lines='skip')
d_prod = d_prod.merge(d_app[['ApplNo', 'ApplType']], on='ApplNo')
d_prod['family'] = d_prod.DrugName.map(fam)
key = lambda s: re.sub(r'[^a-z0-9]', '', str(s).lower())
d_types = d_prod.groupby(d_prod.DrugName.map(key)).ApplType.agg(set)
sp['anda_only'] = sp.Brnd_Name.map(lambda b: d_types.get(key(b), set()) == {'ANDA'})
print('CMS rows dropped as ANDA-only in Drugs@FDA:', sorted(sp.loc[sp.anda_only, 'Brnd_Name']))
sp = sp[~sp.anda_only]
rank = (sp.groupby('family')
          .agg(brand_names=('Brnd_Name', lambda x: '; '.join(sorted(set(x)))),
               generic=('Gnrc_Name', 'first'),
               claims_2024=('Tot_Clms_2024', 'sum'),
               spending_2024=('Tot_Spndng_2024', 'sum'))
          .sort_values('claims_2024', ascending=False).reset_index())
rank['rank'] = range(1, len(rank) + 1)
top = rank.head(100)

# ---------- 3. Part D 2026 Q3 median unit cost per NDC ----------
con = duckdb.connect()
con.execute('set enable_progress_bar=false')
pd_ndc = con.execute(f"""
    select NDC, count(*) n_plans, median(cast(UNIT_COST as double)) partd_unit
    from read_csv('{SPUF}', delim='|', header=true, all_varchar=true)
    where DAYS_SUPPLY='30' group by NDC""").df()
pd_ndc['prod9'] = pd_ndc.NDC.str[:9]

# ---------- 4. VA current Big4 / FSS ----------
va = pd.read_csv(VA, dtype=str)
va['NDC'] = va.NDCWithDashes.str.replace('-', '')
va['Price'] = va.Price.astype(float)
va = va[(va.Price > 0.01)
        & (pd.to_datetime(va.PriceStartDate) <= ASOF)
        & (pd.to_datetime(va.PriceStopDate) >= ASOF)]
va['family'] = va.TradeName.map(fam)
vp = (va.pivot_table(index='NDC', columns='PriceType', values='Price', aggfunc='min')
        .reset_index())
vmeta = va.groupby('NDC').agg(va_name=('TradeName', 'first'), va_pkg=('PackageDescription', 'first'),
                              va_family=('family', 'first')).reset_index()
vp = vp.merge(vmeta, on='NDC')

# ---------- 5. NADAC billing unit (latest per NDC) ----------
na = pd.read_csv(NADAC, dtype=str)
na['NDC'] = na.NDC.str.zfill(11)
na['eff'] = pd.to_datetime(na['Effective Date'])
na = na.sort_values('eff').groupby('NDC').tail(1)[['NDC', 'Pricing Unit', 'NADAC Per Unit']]
na.columns = ['NDC', 'unit', 'nadac_unit']
na['nadac_unit'] = na.nadac_unit.astype(float)

# ---------- 6. NDC universe per top family ----------
fams = set(top.family)
fda_ndcs = pkg[pkg.family.isin(fams) & pkg.is_brand][['NDC', 'family', 'PACKAGEDESCRIPTION', 'PROPRIETARYNAME']]
va_ndcs = vp[vp.va_family.isin(fams)][['NDC', 'va_family']].rename(columns={'va_family': 'family'})
nd = pd.concat([fda_ndcs, va_ndcs]).drop_duplicates('NDC')
nd = nd.drop(columns=['PACKAGEDESCRIPTION', 'PROPRIETARYNAME']).merge(
    pkg[['NDC', 'PACKAGEDESCRIPTION', 'PROPRIETARYNAME', 'APPLICATIONNUMBER']], on='NDC', how='left')
nd = nd.merge(vp, on='NDC', how='inner')            # must have a current VA price
# Kits and starter, titration or initiation packs are dropped, except a carton of kits that each hold one
# syringe or pen ("2 KIT in 1 CARTON / 1 KIT in 1 KIT * 1 SYRINGE in 1 TRAY ..."), billed per kit (Humira).
one_syr_kit = nd.PACKAGEDESCRIPTION.str.contains(r'^\d+ KIT in 1 CARTON .*/\s*1 KIT in 1 KIT\s*\*\s*1 SYRINGE in 1 TRAY',
                                                 na=False)
kit = ((nd.PACKAGEDESCRIPTION.str.contains(r'KIT', na=False) & ~one_syr_kit)
       | nd.va_name.str.contains(r'STARTER|\bSTART\b|INITIATION|TITRATION', na=False))
kit_fams = set(nd.loc[kit, 'family'])
nd = nd[~kit]
nd = nd.merge(na, on='NDC', how='left')
nd['prod9'] = nd.NDC.str[:9]

# Part D price: exact NDC, else same product (first 9 digits), median across packages
exact = pd_ndc[['NDC', 'n_plans', 'partd_unit']]
byprod = pd_ndc.groupby('prod9').agg(n_plans_p=('n_plans', 'max'), partd_unit_p=('partd_unit', 'median')).reset_index()
nd = nd.merge(exact, on='NDC', how='left').merge(byprod, on='prod9', how='left')
nd['partd_match'] = nd.partd_unit.notna().map({True: 'exact NDC', False: 'same product'})
nd['partd_unit'] = nd.partd_unit.fillna(nd.partd_unit_p)
nd['n_plans'] = nd.n_plans.fillna(nd.n_plans_p)
nd.loc[nd.partd_unit.isna(), 'partd_match'] = None

# ---------- 7. package quantity in the billing unit, from three sources ----------
# CMS Medicaid Drug Rebate Program product file: unit type and units per package.
mdrp = pd.read_csv(MDRP, dtype=str, usecols=['Year', 'Quarter', 'NDC', 'Unit Type', 'Units Per Pkg Size'])
mdrp = (mdrp.assign(yq=mdrp.Year + mdrp.Quarter).sort_values('yq').groupby('NDC').tail(1)
            .rename(columns={'Unit Type': 'mdrp_unit'}))
mdrp['mdrp_qty'] = mdrp['Units Per Pkg Size'].astype(float)
nd = nd.merge(mdrp[['NDC', 'mdrp_unit', 'mdrp_qty']], on='NDC', how='left')
nd['mdrp_unit'] = nd.mdrp_unit.replace({'TAB': 'EA', 'CAP': 'EA'})
# billing unit: NADAC, else the rebate file
nd['unit'] = nd.unit.fillna(nd.mdrp_unit)

# Source 1: FDA package text, with two fixed rules
nd['fda_qty'] = [qty(d, u) if pd.notna(d) and pd.notna(u) else None for d, u in zip(nd.PACKAGEDESCRIPTION, nd.unit)]
# Two-strip Ellipta inhalers (Breo, Anoro, Trelegy): billed one unit per blister, two blisters per dose.
two_strip = nd.family.isin(['breo', 'anoro', 'trelegy'])
nd.loc[two_strip, 'fda_qty'] = nd.loc[two_strip, 'fda_qty'] * 2
# Respimat cartridges: billed per gram; 60- and 120-puff cartridges hold 4 g. 10-puff samples are dropped.
resp = nd.PACKAGEDESCRIPTION.str.contains('SPRAY, METERED in 1 CARTRIDGE', na=False)
puffs = nd.PACKAGEDESCRIPTION.str.extract(r'(\d+) SPRAY, METERED in 1 CARTRIDGE')[0].astype(float)
nd.loc[resp, 'unit'] = 'GM'
nd.loc[resp, 'fda_qty'] = puffs[resp].map(lambda p: 4.0 if p >= 60 else 0.667)
nd = nd[~(resp & (puffs < 60))].copy()


def va_qty(txt, unit):
    """VA PackageDescription in the billing unit: "30", "100UD", "3X10", "5X3ML", "18GM"."""
    t = str(txt).upper().replace(' ', '')
    m = re.fullmatch(r'(?:(\d+)X)?([\d.]+)(ML|GM|G)', t)
    if m:
        n = float(m.group(1) or 1) * float(m.group(2))
        if unit == ('ML' if m.group(3) == 'ML' else 'GM'):
            return n
    if unit != 'EA':
        return None
    m = re.fullmatch(r'(\d+)X[\d.]+ML', t)          # single-use vials billed each: "30X0.4ML" = 30
    if m:
        return float(m.group(1))
    m = re.fullmatch(r'(\d+)X(\d+)', t) or re.fullmatch(r'(\d+)(?:UD|S)?', t)
    if m:
        return float(m.group(1)) * (float(m.group(2)) if m.lastindex == 2 else 1)
    return None


# Source 2: VA package text
nd['va_qty'] = [va_qty(t, u) for t, u in zip(nd.va_pkg, nd.unit)]
# Source 3: CMS rebate file, when its unit type is the billing unit. For tablets and capsules it often
# reports 1 regardless of count, so a 1 for an EA item is not used.
nd['mdrp_q'] = nd.mdrp_qty.where((nd.mdrp_unit == nd.unit) & ~((nd.unit == 'EA') & (nd.mdrp_qty == 1)))


def vote(row):
    """Quantity agreed by at least two sources; the only source if there is one; if two or more
    disagree, the value that puts the VA Big4 unit price at 0.3x-1.1x NADAC, if exactly one does."""
    vals = [(s, row[c]) for s, c in (('FDA', 'fda_qty'), ('VA', 'va_qty'), ('CMS rebate file', 'mdrp_q'))
            if pd.notna(row[c]) and row[c] > 0]
    for s1, v1 in vals:
        agree = [s for s, v in vals if abs(v - v1) <= 0.01 * v1]
        if len(agree) >= 2:
            return v1, ' + '.join(agree)
    if len(vals) == 1:
        return vals[0][1], vals[0][0] + ' only'
    if vals and pd.notna(row.Big4) and pd.notna(row.nadac_unit):
        fit = [(s, v) for s, v in vals if 0.3 <= row.Big4 / v / row.nadac_unit <= 1.1]
        if len(fit) == 1:
            return fit[0][1], fit[0][0] + ' (NADAC tie-break)'
    return None, 'sources disagree' if vals else 'no source'


nd[['qty', 'qty_src']] = pd.DataFrame([vote(r) for _, r in nd.iterrows()], index=nd.index)

for col in ('Big4', 'FSS', 'NC'):
    if col in nd:
        nd[f'va_{col.lower()}_unit'] = nd[col] / nd.qty
nd['big4_vs_partd'] = nd.va_big4_unit / nd.partd_unit - 1
# unit sanity flag: VA FSS/Big4 per unit should land within 0.2x-2x of NADAC for brands
# Benchmark is NADAC. When NADAC is missing, Part D is used only if the package count rests on one source:
# a count two sources agree on is not overridden by Part D (for negotiated drugs Part D is capped at the
# negotiated price, so comparing against it would drop exactly the high VA prices being measured).
ref = nd.va_big4_unit.fillna(nd.get('va_fss_unit'))
one_src = ~nd.qty_src.str.contains(r'\+', na=False)
bench = nd.nadac_unit.where(nd.nadac_unit.notna(), nd.partd_unit.where(one_src))
nd['unit_flag'] = ((ref / bench) > 2) | ((ref / bench) < 0.2) | nd.qty.isna()
nd = nd.merge(top[['family', 'rank']], on='family')
# Drugs@FDA application type per NDC: via the NDC Directory application number; for an NDC no longer in
# the NDC Directory, the application types of Drugs@FDA products named with the brand family
d_type = d_app.set_index('ApplNo').ApplType
# application number from the full NDC Directory (Humulin R, N and 70/30 are listed as OTC products)
allp = pd.read_csv(FDA_PROD, sep='\t', dtype=str, encoding='latin-1')[['PRODUCTID', 'APPLICATIONNUMBER']]
allk = pd.read_csv(FDA_PKG, sep='\t', dtype=str, encoding='latin-1')[['PRODUCTID', 'NDCPACKAGECODE']]
allk['NDC'] = allk.NDCPACKAGECODE.map(ndc11)
appl = allk.merge(allp, on='PRODUCTID').drop_duplicates('NDC').set_index('NDC').APPLICATIONNUMBER
nd['APPLICATIONNUMBER'] = nd.NDC.map(appl)
nd['dafda_type'] = nd.APPLICATIONNUMBER.str.extract(r'(\d+)$')[0].str.zfill(6).map(d_type)
by_name = d_prod.groupby('family').ApplType.agg(lambda x: '/'.join(sorted(set(x))))
miss = nd.dafda_type.isna()
nd.loc[miss, 'dafda_type'] = nd.loc[miss, 'family'].map(by_name).map(lambda t: f'by name: {t}' if isinstance(t, str) else t)
nd.sort_values(['rank', 'NDC']).to_csv('data/work/top100_ndc.csv', index=False)

ok = nd[nd.big4_vs_partd.notna() & ~nd.unit_flag]
bad = ok[~ok.dafda_type.isin(['NDA', 'BLA', 'by name: NDA', 'by name: BLA'])]
print('compared NDCs by Drugs@FDA application type:', ok.dafda_type.value_counts().to_dict())
assert bad.empty, bad[['family', 'NDC', 'va_name', 'dafda_type']]
br = (ok.groupby('family')
        .agg(ndcs_compared=('NDC', 'count'),
             big4_vs_partd_median=('big4_vs_partd', 'median'),
             big4_vs_partd_min=('big4_vs_partd', 'min'),
             big4_vs_partd_max=('big4_vs_partd', 'max'))
        .reset_index())
out = top.merge(br, on='family', how='left')
status = []
for f in out.family:
    sub = nd[nd.family == f]
    if f in set(br.family):
        status.append('compared')
    elif f in kit_fams and (sub.empty or sub.partd_unit.isna().all()):
        status.append('kit or starter packs only')
    elif sub.empty:
        status.append('no current VA price')
    elif sub.get('Big4', pd.Series(dtype=float)).notna().sum() == 0:
        status.append('no Big4 price')
    elif sub.partd_unit.isna().all():
        status.append('not in Part D pricing file')
    else:
        status.append('units need review')
out['status'] = status
out.to_csv('data/work/top100_brand.csv', index=False)

print(out.status.value_counts().to_string())
pd.set_option('display.width', 250)
print(out[['rank', 'family', 'claims_2024', 'status', 'ndcs_compared', 'big4_vs_partd_median',
           'big4_vs_partd_min', 'big4_vs_partd_max']].round(3).to_string(index=False))
