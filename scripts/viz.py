"""Build dist/index.html: VA Big4 vs Medicare Part D, percent difference by brand (90 compared brands).

Run after scripts/top100.py. Reads data/work/top100_brand.csv and top100_ndc.csv, injects the rows into
scripts/viz_template.html, writes dist/index.html.
"""
import json
import re
import pandas as pd

NEG = {'eliquis', 'jardiance', 'xarelto', 'januvia', 'farxiga', 'entresto', 'enbrel', 'novolog', 'fiasp'}
NAME_FIX = {'novolog': 'NovoLog', 'oxycontin': 'OxyContin'}
UNIT = {'EA': 'each', 'ML': 'per mL', 'GM': 'per gram'}

b = pd.read_csv('data/work/top100_brand.csv')
b = b[b.status == 'compared']
n = pd.read_csv('data/work/top100_ndc.csv', dtype={'NDC': str})
n = n[n.big4_vs_partd.notna() & ~n.unit_flag]
n['unit'] = n.unit.fillna(n.mdrp_unit)



def tidy(name):
    """VA trade name in title case with units kept lowercase (2.5 mg, 3 mL, 6.1 g)."""
    t = name.title()
    t = re.sub(r'(?<=\d)(Mg|Mcg|Ml|Gm|Unt|Unit|Units)\b',
               lambda m: {'Mg': ' mg', 'Mcg': ' mcg', 'Ml': ' mL', 'Gm': ' g'}.get(m.group(1), ' units'), t)
    t = re.sub(r'/Ml\b', '/mL', t)
    t = re.sub(r'\b(Hfa|Er|Xr|Ec)\b', lambda m: m.group(1).upper(), t)
    return re.sub(r',(?=\D)', ', ', t).replace('  ', ' ')


rows = []
for r in b.itertuples():
    shortest = min(r.brand_names.split('; '), key=len)
    name = NAME_FIX.get(r.family, shortest.split()[0].rstrip('*'))
    sub = n[n.family == r.family]
    ex = sub.iloc[(sub.big4_vs_partd - r.big4_vs_partd_median).abs().argsort().iloc[0]]  # package nearest the median
    rows.append(dict(
        name=name, generic=r.generic.title(), neg=r.family in NEG, rank=int(r.rank), claims=int(r.claims_2024), spend=round(r.spending_2024 / 1e9, 3),
        pct=round(r.big4_vs_partd_median * 100, 3), lo=round(r.big4_vs_partd_min * 100, 3),
        hi=round(r.big4_vs_partd_max * 100, 3), n=int(r.ndcs_compared),
        ex_name=tidy(ex.va_name), ex_va=round(ex.va_big4_unit, 2), ex_pd=round(ex.partd_unit, 2),
        ex_unit=UNIT.get(ex.unit, 'per unit')))

# spending rank among the 90 drugs shown (2024 Part D gross spending, annual file)
for i, d in enumerate(sorted(rows, key=lambda d: -d['spend']), 1):
    d['srank'] = i
rows.sort(key=lambda d: d['pct'])
tpl = open('scripts/viz_template.html').read()
html = (tpl.replace('/*__DATA__*/[]', json.dumps(rows, separators=(',', ':')))
           .replace('__LOGO__', open('assets/d4tp-logo.datauri').read().strip()))
open('dist/index.html', 'w').write(html)
print(len(rows), 'brands;', sum(d['pct'] > 0 for d in rows), 'VA higher;', sum(d['neg'] for d in rows), 'negotiated')
print(', '.join(d['name'] for d in rows))
