"""Which parent companies run the Part D plans in the generic tier count, and how many people those plans cover.

Parent organization and enrollment: CMS Monthly Enrollment by Plan, October 2026 (one row per contract and
plan; enrollment of 10 or fewer is shown as * and counted as missing here). Part D enrollment = plans that offer Part D (MA-PD, PDP,
employer PDP). Plans: the 5,295 contract-plan-segments on five- or six-tier formularies (SPUF 2026 Q3), as in
scripts/generic_tiers.py; each is matched to its contract's parent organization. Enrollment is by contract and
plan, so a plan's segments are counted once. The largest parent companies are ranked by Part D enrollment.
Post: the 5,295 plans cover about 48 million people; 76% are in plans of the five largest parent companies.
Output: data/work/parent_orgs.csv (one row per parent organization).
"""
import duckdb
import pandas as pd

SP = 'data/raw/spuf_2026q3/ex/'
EN = 'data/raw/cms_enroll_plan_2026_10/ex/Monthly_Report_By_Plan_2026_10.csv'

e = pd.read_csv(EN, dtype=str, encoding='latin-1')
e['enr'] = pd.to_numeric(e.Enrollment.str.replace(',', ''), errors='coerce')
contract_parent = e.groupby('Contract Number')['Parent Organization'].agg(lambda x: x.mode().iat[0])
assert e.groupby('Contract Number')['Parent Organization'].nunique().max() == 1
pd_enr = (e[e['Offers Part D'] == 'Yes'].groupby('Parent Organization').enr.sum()
           .sort_values(ascending=False))
top5 = list(pd_enr.index[:5])

con = duckdb.connect()
con.sql(f"""create table f as select FORMULARY_ID, cast(TIER_LEVEL_VALUE as int) as tier
            from read_csv('{SP}basic drugs formulary file  PPUF_2026Q3.txt', delim='|', header=true, all_varchar=true)""")
p = con.sql(f"""select distinct CONTRACT_ID, PLAN_ID, SEGMENT_ID, FORMULARY_ID
                from read_csv('{SP}plan information  PPUF_2026Q3.txt', delim='|', header=true, all_varchar=true)
                where FORMULARY_ID in (select FORMULARY_ID from f group by 1 having max(tier) in (5, 6))""").df()
p['parent'] = p.CONTRACT_ID.map(contract_parent)
# enrollment of these plans (by contract and plan; segments share a plan's enrollment)
e_cp = e.assign(PLAN_ID=e['Plan ID'].str.zfill(3)).set_index(['Contract Number', 'PLAN_ID']).enr
pp = p.drop_duplicates(['CONTRACT_ID', 'PLAN_ID']).copy()
pp['enr'] = [e_cp.get((c, pl)) for c, pl in zip(pp.CONTRACT_ID, pp.PLAN_ID)]

out = pd.DataFrame({'partd_enrollment': pd_enr})
out['partd_share'] = out.partd_enrollment / pd_enr.sum()
out['plans_5_6_tier'] = p.groupby('parent').size()
out['plans_5_6_tier_enrollment'] = pp.groupby('parent').enr.sum()
out = out.fillna({'plans_5_6_tier': 0}).astype({'plans_5_6_tier': int})
out.to_csv('data/work/parent_orgs.csv')

print(f"Part D enrollment, October 2026 (plans with 11+ enrollees): {pd_enr.sum():,.0f}")
print(out.head(6).to_string())
print(f"plans on 5/6-tier formularies: {len(p):,}; no parent found: {p.parent.isna().sum()}")
print(f"contract-plans: {len(pp):,}; with enrollment: {pp.enr.notna().sum():,} (the rest show * for 10 or fewer enrollees, or are not in the file)")
print(f"enrollment in these plans: {pp.enr.sum():,.0f} ({100 * pp.enr.sum() / pd_enr.sum():.1f}% of Part D enrollment)")
print(f"top 5 by Part D enrollment: {top5}")
print(f"top 5 by enrollment in these plans: {list(pp.groupby('parent').enr.sum().sort_values(ascending=False).index[:5])}")
print(f"people in these plans whose plan is run by the top 5: {pp[pp.parent.isin(top5)].enr.sum():,.0f} "
      f"({100 * pp[pp.parent.isin(top5)].enr.sum() / pp.enr.sum():.1f}%)")
print(f"plans run by the top 5: {p.parent.isin(top5).sum():,} of {len(p):,}")
