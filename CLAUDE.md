# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Single-page dashboard for URI's Diversion and Recovery Program (DaRP). Tracks food waste diversion across semesters (S24 → S26). No build system — open `index.html` directly in a browser.

## Architecture

**Everything lives in one file: `index.html` (~2900+ lines).** CSS, JS, HTML, and all data constants are inline. There is no bundler, no imports, no external JS beyond Google Fonts.

### Data Layer

All semester data is hardcoded as JS constants near the top of the `<script>` block (~line 727):

- `yoySems[]` — one entry per semester with aggregate stats (`lbs`, `hrs`, `lbhr`, `ambs`, `shifts`, `collDays`, `semWeeks`, etc.)
- `SEASON_DATA` object (keyed by `semKey` like `'F25'`, `'S26'`) — rich per-semester object containing ambassador-level arrays/maps:
  - `ambWeeklyLbs[ambIdx][weekIdx]` — per-ambassador weekly lbs matrix
  - `ambWeeklyHrs`, `ambWeeklyShifts`, `ambWeeklyEff` — same shape, null for pre-hour seasons
  - `ambMaxShiftLbs`, `ambMaxShiftLbhr`, `ambMaxShiftEff`, `ambMaxShiftDate` — best-shift maps keyed by name
  - `ambBestDay_lbs` — best single collection day per ambassador, keyed by name → `{val, label}`
  - `weekMeta[weekIdx]` — `{range, date}` labels per week
  - `weekTotals[]`, `weekAvgEff[]`, `wkdayLbhr` — program-level weekly/weekday aggregates
  - `periodHallLbhr` — `{mf_b, mf_l, mf_d, bf_b, bf_l, bf_d}` each `{lbs, hrs, lbhr}`
  - `topDateBy_lbhr[]`, `topDateBy_lbs[]`, `worstDay_lbhr`, `worstDay_lbs`, `worstShiftLbs`
- `SD` — global variable pointing to the currently selected `SEASON_DATA` entry; updated by `switchSeason(key)`
- Pre-hour seasons (S24, F24, S25): `hrs:null`, `lbhr:null`, no `ambWeeklyHrs`/`ambWeeklyEff`

### Rendering Model

**No virtual DOM or framework.** Every render function rebuilds `innerHTML` from scratch.

Key render functions:
- `switchSeason(key)` — updates `SD`, re-renders all active panels; called from the header dropdown
- `renderLeaderboard(type)` — builds ambassador charts; `type` = `'lbs'` | `'avglbs'` | `'eff'` | `'busybee'`
- `renderVizLbhr()` — Rate Breakdown section (Summary tab); shows lb/hr, lb/shift, lb/day, lb/week rows
- `_renderWkdayChart(container)` — weekday lb/hr grouped bar chart (SVG); only full data in F25/S26
- `renderGrowth()` — All-Time tab charts; uses `(s.sem === SD.semKey)` for current-semester highlighting
- `renderCumChart()`, `renderMfBfChart()`, `renderPeriodChart()`, `renderTeamChart()` — other All-Time charts

**Bar chart primitives:**
- `_lbBarHTML(data, fmt)` — renders ranked bar rows; each datum: `{name, val, extra?, tip?, display?}`
  - `d.display` overrides the splash text inside the bar (while `d.val` still controls bar width)
  - `d.tip` = pre-built HTML string stored in `_tipStore`, revealed on hover
- `_tip(title, rows)` — builds tooltip HTML; row `['—','—']` renders a divider; null/empty values are omitted
- `_pair(a, b)` — wraps two chart blocks in a two-column grid (`.lb-pair`)
- `_chart(title, data, fmt)` — thin wrapper: section title + `_lbBarHTML`

### Tab/Panel System

Five tabs: Summary (`panel-summary`), Ambassadors (`panel-ambassadors`), Eco Impact (`panel-impact`), All-Time (`panel-growth`).

- `showPanel(id, btn)` — activates a tab panel, calls `animateBars()` after 60ms
- `animateBars()` — sets `bar-fill` widths from `data-pct` attributes (CSS transition handles animation)
- `currentTab` global tracks active panel; `currentLb` tracks active leaderboard type

### Selector Card Pattern

Used in Ambassadors and Eco tabs. Cards have class `.lb-sel-card` or `.eco-sel-card`; clicking one calls `showLeaderboard(type, btn)` or `showEco(type, btn)` which toggles `.active` and re-renders the panel content below.

### Tooltip System

- `_tipStore{}` — global map of index → HTML string
- `_tipIdx` — incrementing key
- Tooltips attached inline as `onmouseenter`/`onmouseleave` on bar rows
- `tipShow(event, html)`, `moveTip(event)`, `hideTip()` — position and show `.tip-box`

## Data Extraction Scripts

`scripts/` contains one-off Python scripts run locally to pull data from Excel files in `data files/`:

- `extract_data.py` — main extraction script; uses pandas; reads F25 and S26 from `Bulk Data` sheets; outputs weekly breakdowns, weekday lb/hr, best shifts per ambassador
- `patch5.py`–`patch8.py` — targeted extraction patches for specific data points

Run any script with: `python scripts/extract_data.py`  
Requires: `pandas`, `numpy`, `openpyxl`

Excel files referenced by hardcoded absolute paths (`C:\Users\mkyle\OneDrive\Desktop\darp dashboard\data files\...`) — update `BASE` constant in each script if path changes.

## Key Conventions

- **Season keys**: `'S24'`, `'F24'`, `'S25'`, `'F25'`, `'S26'` — used as keys in `SEASON_DATA`, `yoyRosters`, `yoyAmbLbs`, etc. Must be consistent everywhere.
- **Current-semester highlighting**: use `(s.sem === SD.semKey)` not hardcoded `s.current`. The `s.current` field on `yoySems` entries is legacy and only used for the `yoySems` array.
- **Ambassador index (`ai`)**: ambassadors in `SEASON_DATA` have a stable index used to look up weekly matrices. Always access weekly data as `_wl[a.ai][weekIdx]`.
- **Pre-hour guard pattern**: check `SD.lbhr` before showing lb/hr; check `SD.ambWeeklyHrs` or `SD.ambTotalsLbhr` before showing per-ambassador lb/hr.
- **CSS custom properties**: `--navy`, `--blue`, `--light`, `--gold`, `--green`, `--muted`, `--card`, `--border` — defined in `:root`, used throughout.
- **Dual-column layout**: `_pair()` produces `.lb-pair` (CSS grid, 2 cols). On narrow containers these stack. Charts inside panels use `container-type` if container queries are needed.
- **`ambColorMap`**: global map of ambassador name → hex color. Add new ambassadors here for consistent dot/highlight colors across all charts. Variant spellings (typos) map to same color.
