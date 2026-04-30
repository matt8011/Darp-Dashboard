import sys
sys.stdout.reconfigure(encoding='utf-8')
import openpyxl
from collections import defaultdict

wb = openpyxl.load_workbook(
    r'C:\Users\mkyle\OneDrive\Desktop\darp dashboard\data files\S2026 Data Analysis .xlsx',
    data_only=True
)
ws = wb['Bulk Data']

# Headers row = row 2, data starts row 3
# Cols (0-indexed): A=0 timestamp, B=1 name, H=7 lbs, I=8 lbhr, J=9 period,
#                   K=10 date, L=11 weekday, M=12 hall, N=13 efficiency

# Week start dates (Monday) for S26 — 15 weeks matching s26WeekMeta order
WEEK_STARTS = [
    '2026-01-19','2026-01-26','2026-02-02','2026-02-09','2026-02-16',
    '2026-02-23','2026-03-02','2026-03-09','2026-03-16','2026-03-23',
    '2026-03-30','2026-04-06','2026-04-13','2026-04-20','2026-04-27',
]
from datetime import date, timedelta
def week_idx(d):
    """Return 0-14 index for a date, or None if not in semester."""
    if not d: return None
    if hasattr(d, 'date'): d = d.date()
    for i, ws_str in enumerate(WEEK_STARTS):
        ws_date = date.fromisoformat(ws_str)
        we_date = ws_date + timedelta(days=6)
        if ws_date <= d <= we_date:
            return i
    return None

DAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday']

# Accumulators
amb_max_lbhr   = defaultdict(float)   # name -> max single shift lb/hr
amb_max_eff    = defaultdict(float)   # name -> max single shift eff
amb_period_cnt = defaultdict(lambda: defaultdict(int))  # name -> period -> count
day_lbs        = defaultdict(list)   # weekday -> [lbs]
day_lbhr       = defaultdict(list)   # weekday -> [lbhr]
day_eff        = defaultdict(list)   # weekday -> [eff]
day_shifts     = defaultdict(int)    # weekday -> shift count
week_eff       = defaultdict(list)   # week_idx -> [eff]

for row in ws.iter_rows(min_row=3, values_only=True):
    name    = row[1]
    lbs     = row[7]
    lbhr    = row[8]
    period  = row[9]
    date_v  = row[10]
    weekday = row[11]
    eff     = row[13]

    if not name or name == 'N/A' or not lbs:
        continue
    try:
        lbs_v  = float(lbs)
        lbhr_v = float(lbhr) if lbhr else None
        eff_v  = float(eff)  if eff  else None
    except (TypeError, ValueError):
        continue
    if lbs_v <= 0:
        continue

    # Per-ambassador max single shift lb/hr and eff
    if lbhr_v and lbhr_v > amb_max_lbhr[name]:
        amb_max_lbhr[name] = round(lbhr_v, 2)
    if eff_v and eff_v > amb_max_eff[name]:
        amb_max_eff[name] = round(eff_v * 100, 1)

    # Most frequent period
    if period:
        amb_period_cnt[name][period] += 1

    # Weekday aggregates
    if weekday and weekday in DAYS:
        day_lbs[weekday].append(lbs_v)
        if lbhr_v: day_lbhr[weekday].append(lbhr_v)
        if eff_v:  day_eff[weekday].append(eff_v * 100)
        day_shifts[weekday] += 1

    # Week-level efficiency
    wi = week_idx(date_v)
    if wi is not None and eff_v:
        week_eff[wi].append(eff_v * 100)

# ── Output ──────────────────────────────────────────────────────────────────
print("const ambMaxShiftLbhr = {")
for name in sorted(amb_max_lbhr):
    print(f"  {repr(name)}:{amb_max_lbhr[name]},")
print("};")

print("\nconst ambMaxShiftEff = {")
for name in sorted(amb_max_eff):
    print(f"  {repr(name)}:{amb_max_eff[name]},")
print("};")

print("\nconst ambMostFreqPeriod = {")
for name in sorted(amb_period_cnt):
    best = max(amb_period_cnt[name], key=lambda p: amb_period_cnt[name][p])
    print(f"  {repr(name)}:{repr(best)},")
print("};")

print("\n// Weekday stats — index 0=Mon 1=Tue 2=Wed 3=Thu 4=Fri")
for key, vals in [('wkdayAvgLbhr', day_lbhr), ('wkdayAvgEff', day_eff)]:
    arr = []
    for d in DAYS:
        v = vals.get(d, [])
        arr.append(round(sum(v)/len(v), 1) if v else 0)
    print(f"const {key} = {arr};")

wkday_avg_lbs_per_shift = []
for d in DAYS:
    lbs_list = day_lbs.get(d, [])
    sc = day_shifts.get(d, 0)
    wkday_avg_lbs_per_shift.append(round(sum(lbs_list)/sc, 1) if sc > 0 else 0)
print(f"const wkdayAvgLbsPerShift = {wkday_avg_lbs_per_shift};")

print("\n// Week-level avg efficiency (×100) — index 0-14 matching s26WeekMeta")
week_eff_arr = []
for wi in range(15):
    vals = week_eff.get(wi, [])
    week_eff_arr.append(round(sum(vals)/len(vals), 1) if vals else 0)
print(f"const weekAvgEff = {week_eff_arr};")
