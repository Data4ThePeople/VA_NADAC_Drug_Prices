"""Basket cost of the top brands, priced two ways.

Part D: 2024 claims (annual Part D Spending by Drug) x 2026 Q1 average spending per claim
        (quarterly Part D Spending by Drug), one CMS brand row at a time.
VA:     the Part D cost x (VA Big4 / Part D unit price) for that row, where the ratio is the median
        over the row's matched NDCs from scripts/top100.py. Rows with no matched NDC use the brand's
        median ratio.

Run after scripts/top100.py. Output: data/work/basket.csv
"""
import re
import pandas as pd

ANNUAL = 'data/raw/partd_spending_2024/DSD_PTD_RY26_P04_V10_DY24_BGM.csv'
QUARTER = 'data/raw/partd_spending_2026q1/QDD_PTD_RQ2603_P01_V10_DQT2601_20260708.csv'
PACK = {'KWIKPEN', 'FLEXPEN', 'FLEXTOUCH', 'SOLOSTAR', 'MAX', 'HFA', 'PEN', 'SURECLICK', 'PENFILL',
        'TEMPO', 'JUNIOR', 'VIAL', 'INHUB', 'ELLIPTA', 'AEROSPHERE', 'PUSHTOUCH', 'UNOREADY', 'SYRINGE',
        'PAK', 'PUSHTRONEX', 'DISKUS', 'MINI'}
NEG = {'eliquis', 'jardiance', 'xarelto', 'januvia', 'farxiga', 'entresto', 'enbrel', 'novolog', 'fiasp'}
CONC = re.compile(r'U-?(200|300|500)|(200|300|500) ?U|CONC')

b = pd.read_csv('data/work/top100_brand.csv')
b = b[b.status == 'compared']
n = pd.read_csv('data/work/top100_ndc.csv', dtype={'NDC': str})
n = n[n.big4_vs_partd.notna() & ~n.unit_flag].copy()
n['names'] = (n.va_name.fillna('') + ' ' + n.PROPRIETARYNAME.fillna('')).str.upper()

an = pd.read_csv(ANNUAL)
an = an[an.Mftr_Name == 'Overall'].set_index('Brnd_Name')
qt = pd.read_csv(QUARTER)
qt = qt[(qt.Mftr_Name == 'Overall') & (qt.Year == '2026 (Q1)')].set_index('Brnd_Name')


def words(name):
    return re.sub(r'[^A-Z ]', ' ', name.upper()).split()


def conc(name):
    m = CONC.search(name.upper())
    return (m.group(1) or m.group(2) or 'CONC') if m else None


rows = []
for f, names, fam_ratio in zip(b.family, b.brand_names, b.big4_vs_partd_median):
    fam_ndcs = n[n.family == f]
    for brand in names.split('; '):
        sub = fam_ndcs
        # insulin concentration: U-200 / U-500 rows match only those NDCs, plain rows exclude them
        c = conc(brand)
        has_conc = sub.names.map(lambda x: conc(x) is not None)
        sub = sub[sub.names.str.contains(c)] if c and c != 'CONC' else sub[~has_conc] if has_conc.any() else sub
        # sub-brand words (Respimat, Sustenna, Maintena, Mix...) must match the NDC name
        sub_words = [w for w in words(brand)[1:] if len(w) >= 3 and w not in PACK]
        for w in sub_words:
            sub = sub[sub.names.str.contains(rf'\b{w}\b')]
        if not sub_words:
            others = {w for nm in names.split('; ') if nm != brand
                      for w in words(nm)[1:] if len(w) >= 3 and w not in PACK}
            if others:
                sub = sub[~sub.names.map(lambda x: any(re.search(rf'\b{o}\b', x) for o in others))]
        ratio = sub.big4_vs_partd.median() if len(sub) else fam_ratio
        claims = an.loc[brand, 'Tot_Clms_2024']
        per_clm = qt.loc[brand, 'Avg_Spnd_Per_Clm'] if brand in qt.index else None
        rows.append(dict(family=f, brand=brand, ndcs_matched=len(sub),
                         ratio_source='row NDCs' if len(sub) else 'brand median',
                         big4_vs_partd=ratio, claims_2024=claims, partd_per_claim_2026q1=per_clm))

x = pd.DataFrame(rows)
x['in_basket'] = x.partd_per_claim_2026q1.notna()
# CMS's 2026 selected drug for these families is insulin aspart (NovoLog, Fiasp); NovoLog Mix 70/30
# (insulin aspart protamine and insulin aspart) is not on the CMS negotiated price list
x['negotiated_2026'] = x.family.isin(NEG) & ~x.brand.str.upper().str.contains('MIX')
x['partd_cost'] = x.claims_2024 * x.partd_per_claim_2026q1
x['va_cost'] = x.partd_cost * (1 + x.big4_vs_partd)
x.to_csv('data/work/basket.csv', index=False)

pd.set_option('display.width', 220)
print('rows left out (no 2026 Q1 spending row):', x.loc[~x.in_basket, 'brand'].tolist())
print('rows using brand median ratio:', x.loc[x.in_basket & (x.ratio_source == 'brand median'), 'brand'].tolist())
k = x[x.in_basket]


def tot(d, label):
    pdc, vac = d.partd_cost.sum(), d.va_cost.sum()
    print(f'{label:24s} brands={d.family.nunique():3d}  Part D ${pdc/1e9:7.2f}B  VA Big4 ${vac/1e9:7.2f}B  '
          f'VA vs Part D {vac/pdc-1:+.1%}')


tot(k, 'All priced brands')
tot(k[k.negotiated_2026], '2026 negotiated drugs')
tot(k[~k.negotiated_2026], 'All other brands')
g = k.groupby('family')[['partd_cost', 'va_cost']].sum().assign(gap=lambda d: d.va_cost - d.partd_cost)
print((g.sort_values('gap', ascending=False).head(10) / 1e9).round(2).to_string())
