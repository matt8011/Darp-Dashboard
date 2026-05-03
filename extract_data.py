import pandas as pd
import numpy as np
import warnings
import json
warnings.filterwarnings('ignore')

BASE = r"C:\Users\mkyle\OneDrive\Desktop\darp dashboard\data files"
FILES = {
    "YoY_Data":    f"{BASE}\\YoY Data Sheet (1).xlsx",
    "YoY_Master":  f"{BASE}\\YoY Master Sheet (1).xlsx",
    "F2025":       f"{BASE}\\F2025 Data Analysis.xlsx",
    "S2026":       f"{BASE}\\S2026 Data Analysis .xlsx",
}

# -------------------------------------------------------
# Helpers
# -------------------------------------------------------
def parse_hrs(v):
    if pd.isna(v): return np.nan
    if isinstance(v, pd.Timedelta):
        return v.total_seconds() / 3600
    if isinstance(v, (int, float)):
        return float(v) * 24
    s = str(v).strip()
    try:
        days = 0
        if ' day' in s:
            parts = s.split(',')
            days = int(parts[0].strip().split()[0])
            s = parts[1].strip()
        h, m, sec = s.split(':')
        return days * 24 + int(h) + int(m)/60 + float(sec.split('.')[0])/3600
    except:
        return np.nan

def fmt_date_win(ts):
    return ts.strftime("%b") + " " + str(ts.day)

# -------------------------------------------------------
# Load data — include ALL rows (double_name rows = real shifts)
# -------------------------------------------------------
def load_f25():
    df = pd.read_excel(FILES["F2025"], sheet_name="Bulk Data", header=1)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns={
        'Name': 'name', 'double name': 'double_name',
        'hours worked': 'hours_worked', 'Derived Weight': 'lbs',
        'lb/hr per shift': 'lbhr', 'period': 'period', 'Date': 'date',
        'Weekday': 'weekday', 'dining hall': 'dining_hall'
    })
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['hours_worked'] = df['hours_worked'].apply(parse_hrs)
    df['lbs'] = pd.to_numeric(df['lbs'], errors='coerce')
    df = df[df['lbs'] > 0].copy()
    return df

def load_s26():
    df = pd.read_excel(FILES["YoY_Data"], sheet_name="S26", header=0)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns={
        'Name': 'name', 'Double Name': 'double_name',
        'hours worked': 'hours_worked', 'Derived Weight': 'lbs',
        'lb/hr per shift': 'lbhr', 'Period': 'period', 'Date': 'date',
        'Weekday': 'weekday', 'Dining Hall': 'dining_hall'
    })
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['hours_worked'] = df['hours_worked'].apply(parse_hrs)
    df['lbs'] = pd.to_numeric(df['lbs'], errors='coerce')
    df = df[df['lbs'] > 0].copy()
    return df

f25 = load_f25()
s26 = load_s26()

print(f"F25: {len(f25)} shifts, lbs={f25['lbs'].sum()}, hrs={f25['hours_worked'].dropna().sum():.2f}")
print(f"S26: {len(s26)} shifts, lbs={s26['lbs'].sum()}, hrs={s26['hours_worked'].dropna().sum():.2f}")

# ================================================================
# TASK 1: F25 per-week breakdown
# ================================================================
print("\n" + "="*70)
print("TASK 1: F25 per-week breakdown")
print("="*70)

f25_week_defs = [
    (1,  "Sep 8-Sep 12",  "2025-09-08", "2025-09-12"),
    (2,  "Sep 15-Sep 19", "2025-09-15", "2025-09-19"),
    (3,  "Sep 22-Sep 26", "2025-09-22", "2025-09-26"),
    (4,  "Sep 29-Oct 3",  "2025-09-29", "2025-10-03"),
    (5,  "Oct 6-Oct 10",  "2025-10-06", "2025-10-10"),
    (6,  "Oct 13-Oct 17", "2025-10-13", "2025-10-17"),
    (7,  "Oct 20-Oct 24", "2025-10-20", "2025-10-24"),
    (8,  "Oct 27-Oct 31", "2025-10-27", "2025-10-31"),
    (9,  "Nov 3-Nov 7",   "2025-11-03", "2025-11-07"),
    (10, "Nov 10-Nov 14", "2025-11-10", "2025-11-14"),
    (11, "Nov 17-Nov 21", "2025-11-17", "2025-11-21"),
    (12, "Nov 24-Nov 25", "2025-11-24", "2025-11-25"),
    (13, "Dec 1-Dec 5",   "2025-12-01", "2025-12-05"),
    (14, "Dec 8-Dec 11",  "2025-12-08", "2025-12-11"),
]

task1_result = []
for wk, label, start_str, end_str in f25_week_defs:
    start = pd.Timestamp(start_str)
    end   = pd.Timestamp(end_str)
    mask  = (f25['date'] >= start) & (f25['date'] <= end)
    wdf   = f25[mask]
    mf    = wdf[wdf['dining_hall'] == 'MF']
    bf    = wdf[wdf['dining_hall'] == 'BF']
    total_lbs = wdf['lbs'].sum()
    total_hrs = wdf['hours_worked'].dropna().sum()
    mf_lbs    = mf['lbs'].sum()
    bf_lbs    = bf['lbs'].sum()
    lbhr      = round(total_lbs / total_hrs, 2) if total_hrs > 0 else None
    entry = {
        "week": wk, "label": label,
        "lbs": round(total_lbs), "hrs": round(total_hrs, 2),
        "mf_lbs": round(mf_lbs), "bf_lbs": round(bf_lbs),
        "lbhr": lbhr
    }
    task1_result.append(entry)
    print(f"  Wk {wk:2d} ({label}): lbs={round(total_lbs)}, hrs={round(total_hrs,2)}, "
          f"MF={round(mf_lbs)}, BF={round(bf_lbs)}, lb/hr={lbhr}")

# ================================================================
# TASK 2: F25 weekday lb/hr breakdown
# ================================================================
print("\n" + "="*70)
print("TASK 2: F25 weekday lb/hr breakdown")
print("="*70)

day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
task2_result = {}
for day in day_order:
    ddf   = f25[f25['weekday'] == day]
    ddf_h = ddf[ddf['hours_worked'].notna() & (ddf['hours_worked'] > 0)]
    mf_h  = ddf_h[ddf_h['dining_hall'] == 'MF']
    bf_h  = ddf_h[ddf_h['dining_hall'] == 'BF']
    total_lbs = ddf['lbs'].sum()
    total_hrs = ddf_h['hours_worked'].sum()
    lbhr      = round(total_lbs / total_hrs, 2) if total_hrs > 0 else None
    mf_lbs_h  = mf_h['lbs'].sum(); mf_hrs_h = mf_h['hours_worked'].sum()
    mf_lbhr   = round(mf_lbs_h / mf_hrs_h, 2) if mf_hrs_h > 0 else None
    bf_lbs_h  = bf_h['lbs'].sum(); bf_hrs_h = bf_h['hours_worked'].sum()
    bf_lbhr   = round(bf_lbs_h / bf_hrs_h, 2) if bf_hrs_h > 0 else None
    active_days = int(ddf['date'].nunique())
    entry = {
        "total_lbs": round(total_lbs), "total_hrs": round(total_hrs, 2),
        "lbhr": lbhr, "mf_lbhr": mf_lbhr, "bf_lbhr": bf_lbhr,
        "active_days": active_days
    }
    task2_result[day] = entry
    print(f"  {day}: lbs={round(total_lbs)}, hrs={round(total_hrs,2)}, lb/hr={lbhr}, "
          f"MF={mf_lbhr}, BF={bf_lbhr}, active_days={active_days}")

# ================================================================
# TASK 3: F25 best single shift per ambassador
# ================================================================
print("\n" + "="*70)
print("TASK 3: F25 best single shift per ambassador")
print("="*70)

task3_result = {}
for amb, grp in f25.groupby('name'):
    if pd.isna(amb): continue
    task3_result[str(amb)] = int(grp['lbs'].max())

for amb, mx in sorted(task3_result.items(), key=lambda x: -x[1]):
    # Also show the shift details
    best_row = f25[f25['name'] == amb].loc[f25[f25['name'] == amb]['lbs'].idxmax()]
    print(f"  {amb}: {mx} lbs  ({fmt_date_win(best_row['date'])}, {best_row['period']}, {best_row['dining_hall']})")

# ================================================================
# TASK 4: S26 worst days and extremes
# ================================================================
print("\n" + "="*70)
print("TASK 4: S26 worst days and extremes")
print("="*70)

s26_h = s26[s26['hours_worked'].notna() & (s26['hours_worked'] > 0)].copy()
s26_daily_h = s26_h.groupby('date').agg(
    lbs=('lbs', 'sum'), hrs=('hours_worked', 'sum')
).reset_index()
s26_daily_h = s26_daily_h[(s26_daily_h['lbs'] > 0) & (s26_daily_h['hrs'] > 0)]
s26_daily_h['lbhr'] = s26_daily_h['lbs'] / s26_daily_h['hrs']

worst_lbhr_row = s26_daily_h.loc[s26_daily_h['lbhr'].idxmin()]
worst_lbhr = {
    "label": fmt_date_win(worst_lbhr_row['date']),
    "lbs": round(worst_lbhr_row['lbs']),
    "hrs": round(worst_lbhr_row['hrs'], 2),
    "lbhr": round(worst_lbhr_row['lbhr'], 2)
}

s26_daily_all = s26.groupby('date')['lbs'].sum().reset_index()
s26_daily_all = s26_daily_all[s26_daily_all['lbs'] > 0]
worst_lbs_row = s26_daily_all.loc[s26_daily_all['lbs'].idxmin()]
worst_lbs_day = {
    "label": fmt_date_win(worst_lbs_row['date']),
    "lbs": round(worst_lbs_row['lbs'])
}

min_shift_lbs = int(s26['lbs'].min())
max_shift_lbs = int(s26['lbs'].max())

print(f"  Worst lb/hr day:  {worst_lbhr}")
print(f"  Worst lbs day:    {worst_lbs_day}")
print(f"  Min single shift: {min_shift_lbs} lbs")
print(f"  Max single shift: {max_shift_lbs} lbs")
min_row = s26.loc[s26['lbs'].idxmin()]
max_row = s26.loc[s26['lbs'].idxmax()]
print(f"  Min detail: {min_row['name']} | {fmt_date_win(min_row['date'])} | {min_row['period']} | {min_row['dining_hall']}")
print(f"  Max detail: {max_row['name']} | {fmt_date_win(max_row['date'])} | {max_row['period']} | {max_row['dining_hall']}")

task4_result = {
    "worst_lbhr_day": worst_lbhr,
    "worst_lbs_day": worst_lbs_day,
    "min_shift_lbs": min_shift_lbs,
    "max_shift_lbs": max_shift_lbs
}

# ================================================================
# TASK 5: S26 period × hall lb/hr breakdown
# ================================================================
print("\n" + "="*70)
print("TASK 5: S26 period × hall lb/hr breakdown")
print("="*70)

s26_h2 = s26[s26['hours_worked'].notna() & (s26['hours_worked'] > 0)].copy()

def map_period(p):
    p = str(p).strip().lower()
    if p == 'breakfast': return 'Breakfast'
    if p == 'lunch': return 'Lunch'
    if p == 'dinner': return 'Dinner'
    return None

s26_h2['period_cat'] = s26_h2['period'].apply(map_period)
skipped = s26_h2[s26_h2['period_cat'].isna()]
print(f"  Ambiguous period rows skipped: {len(skipped)} — values: {skipped['period'].unique()}")
s26_h2 = s26_h2[s26_h2['period_cat'].notna()]

task5_result = {}
for hall_key, hall_label in [("MF", "Mainfare"), ("BF", "Butterfield")]:
    for period_val in ["Breakfast", "Lunch", "Dinner"]:
        mask = (s26_h2['dining_hall'] == hall_key) & (s26_h2['period_cat'] == period_val)
        sub  = s26_h2[mask]
        total_lbs = sub['lbs'].sum()
        total_hrs = sub['hours_worked'].sum()
        lbhr = round(total_lbs / total_hrs, 2) if total_hrs > 0 else None
        combo = f"{hall_label} {period_val}"
        task5_result[combo] = {
            "lbs": round(total_lbs), "hrs": round(total_hrs, 2), "lbhr": lbhr
        }
        print(f"  {combo}: lbs={round(total_lbs)}, hrs={round(total_hrs,2)}, lb/hr={lbhr}")

# ================================================================
# TASK 6: S26 best single week (lbs)
# ================================================================
print("\n" + "="*70)
print("TASK 6: S26 best single week (lbs)")
print("="*70)

s26['week_start'] = s26['date'] - pd.to_timedelta(s26['date'].dt.dayofweek, unit='D')
s26_weekly = s26.groupby('week_start')['lbs'].sum().reset_index()
best_s26_row = s26_weekly.loc[s26_weekly['lbs'].idxmax()]
best_s26_start = best_s26_row['week_start']
best_s26_end   = best_s26_start + pd.Timedelta(days=4)
task6_result = {
    "label": f"{fmt_date_win(best_s26_start)}-{fmt_date_win(best_s26_end)}",
    "lbs": round(best_s26_row['lbs'])
}
print(f"  Best S26 week: {task6_result}")
print("\n  All S26 weeks:")
for _, row in s26_weekly.sort_values('week_start').iterrows():
    ws = row['week_start']; we = ws + pd.Timedelta(days=4)
    mark = " <<< BEST" if row['lbs'] == best_s26_row['lbs'] else ""
    print(f"    {fmt_date_win(ws)}-{fmt_date_win(we)}: {round(row['lbs'])}{mark}")

# ================================================================
# TASK 7: F25 best single week (lbs)
# ================================================================
print("\n" + "="*70)
print("TASK 7: F25 best single week (lbs)")
print("="*70)

f25['week_start'] = f25['date'] - pd.to_timedelta(f25['date'].dt.dayofweek, unit='D')
f25_weekly = f25.groupby('week_start')['lbs'].sum().reset_index()
best_f25_row = f25_weekly.loc[f25_weekly['lbs'].idxmax()]
best_f25_start = best_f25_row['week_start']
best_f25_end   = best_f25_start + pd.Timedelta(days=4)
task7_result = {
    "label": f"{fmt_date_win(best_f25_start)}-{fmt_date_win(best_f25_end)}",
    "lbs": round(best_f25_row['lbs'])
}
print(f"  Best F25 week: {task7_result}")
print("\n  All F25 weeks:")
for _, row in f25_weekly.sort_values('week_start').iterrows():
    ws = row['week_start']; we = ws + pd.Timedelta(days=4)
    mark = " <<< BEST" if row['lbs'] == best_f25_row['lbs'] else ""
    print(f"    {fmt_date_win(ws)}-{fmt_date_win(we)}: {round(row['lbs'])}{mark}")

# ================================================================
# FINAL JSON OUTPUT
# ================================================================
print("\n\n" + "="*70)
print("FINAL STRUCTURED JSON OUTPUT")
print("="*70)

output = {
    "task1_f25_weekly": task1_result,
    "task2_f25_weekday": task2_result,
    "task3_f25_best_shift_per_ambassador": task3_result,
    "task4_s26_extremes": task4_result,
    "task5_s26_period_hall": task5_result,
    "task6_s26_best_week": task6_result,
    "task7_f25_best_week": task7_result,
}

print(json.dumps(output, indent=2, default=str))
