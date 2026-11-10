"""Build dist/negotiated-30day.html: price of a 30-day supply, Medicare negotiated price vs VA Big4, for the
2026 negotiated drugs among the compared top-100 brands.

30-day supply: CMS's negotiated price per 30-day equivalent supply ("Single MFP per 30 DES") and per unit
("NDC-9 MFP per Unit Price"), CMS MFP data file of Nov 2, 2026, rows in effect Nov 1, 2026. Units in a
30-day supply = 30-day price / unit price for the package's NDC-9. Part D 30-day = Part D unit cost x those
units (equals the negotiated price). VA 30-day = VA Big4 unit price x the same units, median across the
drug's packages. Run after scripts/top100.py. Template: scripts/viz30_template.html.
"""
import json
import pandas as pd

MFP = 'data/raw/cms_mfp/ex/CMS_Negotiation_Program_Selected_Drug_List_and_Maximum_Fair_Price_Data_File_20261102.csv'
NAMES = {'eliquis': 'Eliquis', 'jardiance': 'Jardiance', 'xarelto': 'Xarelto', 'januvia': 'Januvia',
         'farxiga': 'Farxiga', 'entresto': 'Entresto', 'enbrel': 'Enbrel', 'novolog': 'NovoLog', 'fiasp': 'Fiasp'}
GENERIC = {'novolog': 'insulin aspart', 'fiasp': 'insulin aspart'}

money = lambda s: s.str.replace(r'[$,]', '', regex=True).astype(float)
mf = pd.read_csv(MFP, dtype=str)
mf = mf[(pd.to_datetime(mf['MFP Effective Date']) <= '2026-11-01')
        & (pd.to_datetime(mf['MFP End Date']).fillna(pd.Timestamp('2099-12-31')) >= '2026-11-01')]
mf = mf.assign(p9=mf['NDC-9'].str.replace('-', ''), m30=money(mf['Single MFP per 30 DES']),
               mu=money(mf['NDC-9 MFP per Unit Price'])).drop_duplicates('p9')

n = pd.read_csv('data/work/top100_ndc.csv', dtype={'NDC': str})
n = n[n.big4_vs_partd.notna() & ~n.unit_flag & n.family.isin(NAMES)]
n['p9'] = n.NDC.str[:9]
m = n.merge(mf[['p9', 'm30', 'mu']], on='p9')       # NovoLog Mix has no MFP row and drops out here
m['units30'] = m.m30 / m.mu
m['pd30'] = m.partd_unit * m.units30
m['va30'] = m.va_big4_unit * m.units30
b = pd.read_csv('data/work/top100_brand.csv').set_index('family')

rows = []
for f, g in m.groupby('family'):
    pd30, va30 = g.pd30.median(), g.va30.median()
    rows.append(dict(name=NAMES[f], generic=GENERIC.get(f, b.loc[f, 'generic'].lower()), rank=int(b.loc[f, 'rank']),
                     neg30=round(g.m30.iloc[0], 2), pd30=round(pd30, 2), va30=round(va30, 2),
                     pct=round((va30 / pd30 - 1) * 100, 3), n=len(g)))
rows.sort(key=lambda d: -d['pct'])
for d in rows:
    assert abs(d['pd30'] - d['neg30']) <= 0.01 * d['neg30'], d   # Part D 30-day equals the negotiated price

tpl = open('scripts/viz30_template.html').read()
html = (tpl.replace('/*__DATA__*/[]', json.dumps(rows, separators=(',', ':')))
           .replace('__LOGO__', open('assets/d4tp-logo.datauri').read().strip()))
open('dist/negotiated-30day.html', 'w').write(html)
pd.set_option('display.width', 200)
print(pd.DataFrame(rows).to_string(index=False))
