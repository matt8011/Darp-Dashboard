import sys
sys.stdout.reconfigure(encoding='utf-8')
import openpyxl
from collections import defaultdict

wb = openpyxl.load_workbook(
    r'C:\Users\mkyle\OneDrive\Desktop\darp dashboard\data files\S2026 Data Analysis .xlsx',
    data_only=True
)
ws = wb['Bulk Data']

# Cols (0-indexed, data rows start at row 3):
# B=1 name, H=7 lbs, I=8 lbhr, J=9 period, K=10 date, L=11 weekday, M=12 hall, N=13 eff

def fmt_date(d):
    if not d: return None
    if hasattr(d, 'date'): d = d.date()
    return d.strftime('%b %d').replace(' 0',' ') if hasattr(d, 'strftime') else str(d)

def date_key(d):
    if not d: return None
    if hasattr(d, 'date'): d = d.date()
    return d.isoformat() if hasattr(d, 'isoformat') else str(d)

# Aggregate per date (program-level)
date_data = defaultdict(lambda: {'lbs':0,'hrs':0,'shifts':0,'eff_sum':0,'eff_n':0,'label':''})
# Per ambassador per date
amb_date = defaultdict(lambda: defaultdict(lambda: {'lbs':0,'hrs':0,'shifts':0,'eff_sum':0,'eff_n':0,'label':''}))

for row in ws.iter_rows(min_row=3, values_only=True):
    name  = row[1]
    lbs   = row[7]
    lbhr  = row[8]
    date_v = row[10]
    eff   = row[13]

    if not name or name == 'N/A' or not lbs:
        continue
    try:
        lbs_v = float(lbs)
        lbhr_v = float(lbhr) if lbhr else 0
        eff_v  = float(eff)  if eff  else None
    except (TypeError, ValueError):
        continue
    if lbs_v <= 0:
        continue

    dk = date_key(date_v)
    if not dk: continue
    label = fmt_date(date_v)

    # Compute hrs from lbs/lbhr (or use timedelta — use lbhr for consistency)
    hrs_v = lbs_v / lbhr_v if lbhr_v > 0 else 0

    # Program-level per date
    d = date_data[dk]
    d['lbs']    += lbs_v
    d['hrs']    += hrs_v
    d['shifts'] += 1
    d['label']   = label
    if eff_v:
        d['eff_sum'] += eff_v * 100
        d['eff_n']   += 1

    # Ambassador per date
    a = amb_date[name][dk]
    a['lbs']    += lbs_v
    a['hrs']    += hrs_v
    a['shifts'] += 1
    a['label']   = label
    if eff_v:
        a['eff_sum'] += eff_v * 100
        a['eff_n']   += 1

# Build program-level date records
prog_dates = []
for dk, d in date_data.items():
    lbhr = round(d['lbs']/d['hrs'], 1) if d['hrs'] > 0 else 0
    eff  = round(d['eff_sum']/d['eff_n'], 1) if d['eff_n'] > 0 else 0
    prog_dates.append({'dk':dk,'label':d['label'],'lbs':round(d['lbs']),'hrs':round(d['hrs'],1),'shifts':d['shifts'],'lbhr':lbhr,'eff':eff})

# Top 5 dates by lbhr, eff, lbs
def top5_dates(key):
    return sorted([x for x in prog_dates if x[key]>0], key=lambda x:-x[key])[:5]

print("// Top 5 program dates by stat")
for stat in ['lbhr','eff','lbs']:
    t5 = top5_dates(stat)
    print(f"const topDateBy_{stat} = [")
    for x in t5:
        print(f"  {{label:{repr(x['label'])},lbs:{x['lbs']},hrs:{x['hrs']},shifts:{x['shifts']},lbhr:{x['lbhr']},eff:{x['eff']}}},")
    print("];")

print()
print("// Per-ambassador best single day by stat")
for stat in ['lbhr','eff','lbs']:
    print(f"const ambBestDay_{stat} = {{")
    for name in sorted(amb_date.keys()):
        dates = amb_date[name]
        best = None
        for dk, d in dates.items():
            if d['lbs'] <= 0: continue
            lbhr = round(d['lbs']/d['hrs'],1) if d['hrs']>0 else 0
            eff  = round(d['eff_sum']/d['eff_n'],1) if d['eff_n']>0 else 0
            val  = lbhr if stat=='lbhr' else (eff if stat=='eff' else round(d['lbs']))
            if best is None or val > best['val']:
                best = {'val':val,'label':d['label'],'lbs':round(d['lbs']),'hrs':round(d['hrs'],1),'shifts':d['shifts'],'lbhr':lbhr,'eff':eff}
        if best:
            print(f"  {repr(name)}:{{val:{best['val']},label:{repr(best['label'])},lbs:{best['lbs']},hrs:{best['hrs']},shifts:{best['shifts']},lbhr:{best['lbhr']},eff:{best['eff']}}},")
    print("};")
