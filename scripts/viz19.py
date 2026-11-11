"""Build dist/part-d-rebates.html: Part D direct and indirect remuneration (DIR) as a share of total Part D
drug costs, 2016 to 2026.

Source: 2026 Medicare Trustees Report, Table IV.B8 "Key Factors for Part D Expenditure Estimates"
(printed page 150), column "Direct and indirect remuneration", footnote 2 "Expressed as a percentage of
total drug costs." 2016 to 2024 are historical data; 2025 and 2026 are intermediate estimates.
Local copy: data/raw/trustees_2026/2026-medicare-trustees-report.pdf. Values transcribed here;
scripts/tieout.py re-reads them from the PDF.
"""
import json

DIR = {2016: 19.9, 2017: 21.9, 2018: 25.0, 2019: 26.5, 2020: 27.0, 2021: 29.1, 2022: 31.3, 2023: 33.5,
       2024: 26.5, 2025: 27.7, 2026: 19.5}
EST = {2025, 2026}

rows = [dict(year=y, pct=v, est=y in EST) for y, v in DIR.items()]
tpl = open('scripts/viz19_template.html').read()
html = (tpl.replace('/*__DATA__*/[]', json.dumps(rows, separators=(',', ':')))
           .replace('__LOGO__', open('assets/d4tp-logo.datauri').read().strip()))
open('dist/part-d-rebates.html', 'w').write(html)
print(rows)
