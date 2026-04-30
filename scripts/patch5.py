import sys
sys.stdout.reconfigure(encoding='utf-8')
import openpyxl
from collections import defaultdict

wb = openpyxl.load_workbook(
    r'C:\Users\mkyle\OneDrive\Desktop\darp dashboard\data files\S2026 Data Analysis .xlsx',
    data_only=True
)
ws = wb['Bulk Data']

# col A=timestamp, B=name, H=lbs(Derived Weight), I=lb/hr, N=Efficiency Score
# Per ambassador: max single shift lbs, and all shifts for avg
amb_shifts = defaultdict(list)  # name -> list of (lbs, lbhr, eff)

for row in ws.iter_rows(min_row=2, values_only=True):
    name = row[1]  # col B
    lbs  = row[7]  # col H
    lbhr = row[8]  # col I
    eff  = row[13] # col N
    if not name or not lbs:
        continue
    try:
        lbs_val = float(lbs)
        lbhr_val = float(lbhr) if lbhr else None
        eff_val  = float(eff)  if eff  else None
    except (TypeError, ValueError):
        continue
    if lbs_val > 0:
        amb_shifts[name].append((lbs_val, lbhr_val, eff_val))

# Per ambassador: max single shift lbs, avg lbs/shift, total lbs, total shifts, total hrs
results = []
for name, shifts in amb_shifts.items():
    max_lbs = max(s[0] for s in shifts)
    avg_lbs = sum(s[0] for s in shifts) / len(shifts)
    total_lbs = sum(s[0] for s in shifts)
    total_shifts = len(shifts)
    # hours: lbs / lbhr for each shift where lbhr is known
    hrs_list = [s[0]/s[1] for s in shifts if s[1] and s[1] > 0]
    total_hrs = sum(hrs_list)
    # avg eff (only shifts where eff is known)
    eff_list = [s[2] for s in shifts if s[2]]
    avg_eff = sum(eff_list) / len(eff_list) if eff_list else 0
    results.append({
        'name': name,
        'max_lbs': round(max_lbs, 2),
        'avg_lbs': round(avg_lbs, 2),
        'total_lbs': round(total_lbs, 2),
        'total_shifts': total_shifts,
        'total_hrs': round(total_hrs, 2),
        'lbhr': round(total_lbs / total_hrs, 2) if total_hrs > 0 else 0,
        'avg_eff': round(avg_eff * 100, 1),  # ×100 for display
    })

results.sort(key=lambda x: x['name'])
print("// Per-ambassador aggregated stats from S26 Bulk Data")
print("const ambStats = {")
for r in results:
    print(f"  {repr(r['name'])}: {{maxLbs:{r['max_lbs']},avgLbs:{r['avg_lbs']},totalLbs:{r['total_lbs']},shifts:{r['total_shifts']},hrs:{r['total_hrs']},lbhr:{r['lbhr']},avgEff:{r['avg_eff']}}},")
print("};")
