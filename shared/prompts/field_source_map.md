# Field → source map (LearnPlatform ALEKS Full Report PDF)

Where every `RCEReport` field physically lives in the "View Usage & Outcomes"
export, with the observed ALEKS values (`ALEKS 1–5.pdf`, Sample School District,
2025–26 BOY–MOY) as a concrete anchor. Order of fields follows `rce_schema.py`.

## Table of contents
1. Header card (plain text — high confidence)
2. Usage Analysis cards
3. Per-group toggle charts (visual — apply the protocol)
4. Outcome Analysis dot plot → subgroup_findings (visual — highest drift risk)
5. Demographics & Methods tab
6. The ALEKS spatial-drift example (read this)

---

## 1. Header card — "Usage & Outcomes Analysis" (page 1, plain text)

| Schema field | Page location | ALEKS value |
|---|---|---|
| `product_name` | "Product:" | `ALEKS` |
| `report_period` | "Timeframe:" | `08/25/2025 - 02/20/2026` |
| `usage.usage_metric` | "Usage Metric:" → normalize | `Minutes on system` → `total_time` |
| `usage.usage_compliance_threshold` | "Recommended Dosage:" | `665 Minutes on system` (≈ 30 min/wk × ~25 wks) |
| `outcome_measure` | "Outcome:" (+ "MOY" timing from narrative) | `FastBridge aMath` → `MOY Fastbridge aMath Scores` |
| `sample_size_max` / overall `n` | "Total Students:" | `572` |
| (context) `district`/`state`/year | "State:", "Year of Study:" | `Iowa`, `2026` |
| `effect_size_raw` / `effect_size_value` | top-right "Overall Effect Size:" gauge | `+0.20` / `0.20` |
| `overall_effectiveness` | gauge color (green) | `positive` |
| `academic_year` | derive from timeframe | `2025-2026` |
| `report_period_label` | derive (Aug→Feb = BOY–MOY) | `BOY-MOY` |
| `district_name` | report title / cover | `Sample School District` |

## 2. Usage Analysis cards

| Schema field | Location | ALEKS value |
|---|---|---|
| (% used) | donut "Used / Not Used" | Used 97% / Not Used 3% |
| `usage.usage_notes` (avg minutes) | "On average, how many minutes…" | `486 minutes` |
| `usage.usage_period_weeks` | usage-distribution banner ("across 25 weeks") | `25` |
| `usage.usage_compliance_rate` | benchmark chart green bar / banner ("156 students … 27% of total users" / "156 students met or exceeded the recommended dosage") | `0.27` |

## 3. Per-group toggle charts (visual)

Three charts, each with a `Grade Level | Gender | Ethnicity | School | SpEd
Status` toggle. They feed usage context and let you cross-check counts. Apply the
chart protocol; callouts are "N students / X% of total users" floating boxes with
leader lines.

- "How many students in each group used the product?" → per-group **counts**.
- "To what extent did students in each group use the product?" → **Average
  Minutes on system** bars. *(This is the chart Amanda's QA prompt targets.)*
- "…reach the recommended usage benchmark?" → grouped not-using/using/met bars.

These primarily corroborate `sample_size`, `usage_compliance_rate`, and the
existence of each subgroup. The authoritative effect numbers come from §4.

## 4. Outcome Analysis dot plot → `subgroup_findings` (highest drift risk)

"Is greater usage of '<product>' related to favorable learning outcomes for
different student groups?" Toggle: `Overall | Grade Level | Gender | Ethnicity |
Prior Performance | School | SpEd Status`. Each dot has a callout
`ES: _ / CI: (_, _) / n: _` and a color (green/yellow/red per the legend).

Observed ALEKS dots:

| Toggle | x-axis label | ES | CI | n | color → effectiveness | significance (CI vs 0) |
|---|---|---|---|---|---|---|
| Grade Level / Overall | 6th grade | 0.20 | (0.12, 0.28) | 572 | green → positive | significant |
| Ethnicity | Black or African American | 0.25 | (0.15, 0.34) | 374 | green → positive | significant |
| Ethnicity | White | 0.33 | (0.02, 0.59) | 41 | green → positive | significant |
| Ethnicity | Hispanic/Latino | 0.19 | (-0.07, 0.42) | 64 | yellow → neutral | not_significant |
| Ethnicity | American Indian or Alaska Native | 0.12 | (-0.13, 0.36) | 73 | yellow → neutral | not_significant |
| Ethnicity | Asian / Native Hawaiian / Two or more races | — | — | — | dot present, callout not legible | flag `Visual Ambiguity` |

Category mapping (toggle → `subgroup_category` enum): School → `school`, Grade
Level → `grade_level`, Gender → `gender`, Ethnicity → `race_ethnicity`, plus
`ell` and `frl_status` where present. **SpEd Status** and **Prior Performance**
appear as toggles here but are not standardized categories → record as `custom`
with `subgroup_category_custom` = `"SpEd status"` / `"prior performance"`.
`effect_size_type` = `pearson_r` for these correlative ALEKS findings;
significance from the 95% CI excluding 0.

The Research Brief's Appendix B independently lists these significant-positive
subgroups (use only to sanity-check, **not** as a substitute for reading the
PDF): Gender = Male, Gender = Female, Ethnicity = White, Ethnicity = Two or more
races, School = Southeast Polk Middle, SPED Status = No, and "Students with the
lowest 40% of Fall testing scores" — all Positive / Level III.

## 5. Demographics & Methods tab

| Schema field | ALEKS value |
|---|---|
| `analysis_method` | `partial_correlation` (descriptive stats for usage) |
| `essa_tier` / `essa_tier_label` | `3` / `Level III` (Promising Evidence) |
| `number_of_rces` | `1` |
| `covariates` | `["school", "grade_level"]` (per method description) |
| `grade_levels` | `["6"]` (outcomes ran for Grade 6 only) |
| `sample_size_notes` | "not enough data to run an Outcomes analysis for grades other than 6" |

---

## 6. The ALEKS spatial-drift example — why Step 3 exists

In `ALEKS 3.pdf` (Ethnicity toggle), the **same seven ethnicities appear in two
different left-to-right orders within a few inches of scroll**:

- "How many students used the product?" (count chart) axis order:
  `Native Hawaiian/OPI, White, Black African American, Two More Races,
  Hispanic Latino, Asian, American Indian/Alaska Native`.
- "To what extent… Average Minutes on system" axis order:
  `Hispanic/Latino, American Indian/Alaska Native, Asian, Black or African
  American, Native Hawaiian/OPI, White, Two more races`.

If you memorize "position 2 = White" from the first chart and reuse it on the
second, you bind White's bar to American Indian/Alaska Native — a silent swap.

Additionally, the **Average Minutes callouts are offset boxes with leader lines**
(e.g. `740 minutes / 0% of total users` floats above and left of its bar). The
number closest to a given bar often belongs to its neighbor. And in the
**effect-size dot plot** there are 7 ethnicity ticks but only ~4 legible
callouts/dots, so each ES must be matched to its category by tracing the leader
line down to the correct x-axis tick — never by counting positions.

Takeaway encoded in the SKILL: re-read the axis per chart, trace leader lines,
bind values to category names (never to positions), confirm tallest⇄largest, and
flag anything you can't resolve.
