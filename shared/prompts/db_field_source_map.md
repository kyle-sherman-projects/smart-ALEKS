# Field → source map (LearnPlatform production database)

An alternative to the PDF/screenshot extraction path in `SKILL.md`. If a district's
RCE has already run inside LearnPlatform, its computed results live in the
`impact_analyses` table of the read-only Rails app database
(`learn_trials_production`) — no PDF, no screenshotting, no spatial-drift risk.

**Validated against a real row:** `impact_analyses.id = 7505`, ALEKS ×
Southeast Polk Community School District, 2025–26 BOY–MOY. Every number in
`deliverables/sample_research_brief_ALEKS.html` traces to this row. Treat it as
the reference worked example the way `SKILL.md` §6 treats the spatial-drift PDF.

## Table of contents
1. Locating the right row
2. `impact_analyses` column reference
3. `result` → subgroup effect-size table
4. `treatment_and_comparison_groups_by_demographic` → dosage/fidelity table
5. Deriving the demographic (active-user) table
6. Two different "n" — don't mix them up
7. Distinguishing a real outcome analysis from a usage-only one
8. Picking among duplicate `active` rows
9. Multiple assessment metrics for the same product/period — check population scope first
10. Caveats

---

## 1. Locating the right row

Two-step query. Never `SELECT *` — `result`/`r_result` can be large; pull them
only once you know the specific `id`.

**Step 1 — locate candidate rows** (cheap, metadata only):

```sql
SELECT ia.id, o.name AS organization_name, tl.name AS tool_name, ia.use_metric,
       ia.recommended_use, ia.assessment_metric, ia.period_init, ia.period_end,
       ia.rce_type
FROM impact_analyses ia
JOIN tools tl ON tl.id = ia.tool_id
LEFT JOIN organizations o ON o.id = ia.organization_id
WHERE tl.name ILIKE '%<tool name>%'
  AND o.name ILIKE '%<district name>%'
ORDER BY ia.period_end DESC;
```

**Step 2 — pull the full row** once you've picked an `id`:

```sql
SELECT id, use_metric, recommended_use, assessment_metric, period_init, period_end,
       grade, confidence_level, covariate_titles, rce_type,
       result, r_result, treatment_and_comparison_groups_by_demographic,
       impact_errors, report_summary, custom_summary
FROM impact_analyses
WHERE id = <id>;
```

## 2. `impact_analyses` column reference

| Column | Holds | ALEKS/Southeast Polk value (id 7505) |
|---|---|---|
| `use_metric` | Usage metric label | `"Minutes on system"` |
| `recommended_use` | Dosage goal | `665` |
| `assessment_metric` | Outcome measure | `"FastBridge aMath"` |
| `period_init` / `period_end` | Reporting window | `2025-08-25` / `2026-02-20` |
| `confidence_level` | CI level | `95` |
| `covariate_titles` | Labels for `cov1`–`cov5` in the JSON below | `{"cov1":"School","cov2":"SpEd Status"}` |
| `rce_type` | Which analyses ran (see §7) | `["usage_analysis","outcome_analysis"]` |
| `result` | Effect sizes, CIs, usage — by subgroup | see §3 |
| `r_result` | Same subgroups, raw R model output (p-values, std err) | see §3 |
| `treatment_and_comparison_groups_by_demographic` | Dosage/fidelity counts by subgroup | see §4 |
| `impact_errors` / `report_summary` / `custom_summary` | Data-quality flags / narrative text, when present | null on this row |

## 3. `result` → `subgroup-table-with-effect-size-details.json`

`result` is one JSON object with a key per subgroup dimension: `grade_level`,
`gender`, `ethnicity`, `pre_achievement_quintiles`, and `cov1`…`cov5` (labels
from `covariate_titles`). Each entry in a dimension's array has:
`category`, `students_count`, `average_usage`, `effect_size`,
`lower_confidence_interval`, `upper_confidence_interval`.

Map to the pipeline's per-subgroup row:

| Pipeline field | Source |
|---|---|
| `Subgroup Category` | Dimension name (title-case; `cov1`/`cov2` → `covariate_titles.cov1`/`cov2`) |
| `Subgroup` | `category` |
| `Effect Size (ES)` | `effect_size` (null → `"Not Plotted"`) |
| `Confidence Interval (CI)` | `(lower_confidence_interval, upper_confidence_interval)`, or `"Not Plotted"` if `effect_size` is null |
| `Sample Size (n)` | `students_count` |
| `Statistical Significance` | `effect_size` null → `"Not Plotted"`; else CI excludes 0 → `"Statistically Significant (Positive/Negative)"`; else `"Undetermined / Not Statistically Significant"` |
| `Outcome Context` | Significant → `"Students had better/worse learning outcomes"`; not significant → `"All students had similar learning outcomes"`; not plotted → `"NA - Sample size below statistical threshold (<30) to generate stable effect size"` |

`pre_achievement_quintiles` is an ordered array of 5 — these are the "Prior
Performance" groups, lowest to highest. Label them `Group 1 (Lowest)` …
`Group 5 (Highest)` in array order.

`r_result`'s matching arrays (`*_results`, keyed by the same subsets) carry the
`p_value` and `std_err` behind each effect size, if you need them.

## 4. `treatment_and_comparison_groups_by_demographic` → `percent-meeting-fidelity-subrgroup.json`

Separate JSON object, one key per dimension, each subgroup holding
`treatment` (active users in that group), `comparison` (non-users), and
`numberOfStudentsWhoMetDosage`.

| Pipeline field | Source |
|---|---|
| `Met Fidelity Goal (Count)` | `numberOfStudentsWhoMetDosage` |
| `Active User Baseline (N)` | `treatment` |
| `% of Active Users Who Met Goal` | `numberOfStudentsWhoMetDosage / treatment` |

## 5. Deriving the demographic (active-user) table

`student-demographic-table.json`'s "Active User N-Count" and "Non-Diluted Core
User %" columns are just `treatment` per subgroup (§4) again, with % of that
dimension's total. No separate source needed.

`average-usage-by-subgroup.json`'s "Average Minutes" is `result`'s
`average_usage` (§3); "Difference from Goal" is `average_usage - recommended_use`.

## 6. Two different "n" — don't mix them up

`result`'s `students_count` and `treatment_and_comparison_groups_by_demographic`'s
`treatment` are **not always the same number** for the same subgroup, and both
are correct — they're different populations:

- `result.students_count` — students with **both** usage data and an outcome
  score. This is the denominator for effect sizes.
- `treatment_and_comparison_groups_by_demographic.treatment` — active users
  overall, regardless of whether they have an outcome score. This is the
  denominator for dosage/fidelity.

Worked example, White students, id 7505: `result.ethnicity` reports
`students_count: 374` (used in the effect-size table); the demographic JSON
reports `treatment: 367` (used in the fidelity table). Both are right for their
own table — this is exactly why the original `contributors/amanda/*.json` files
used 374 in one file and 367 in the other. Don't reconcile them into one number.

## 7. Distinguishing a real outcome analysis from a usage-only one

A trial can have multiple `impact_analyses` rows. Check `rce_type` before
trusting `effect_size`:

- `["usage_analysis"]` only → usage-tracking row. `effect_size` will be `null`
  throughout `result`. (Row `7503` for Southeast Polk is this — same period,
  same dosage goal, no outcome tie-in.)
- `["usage_analysis","outcome_analysis"]` → the real RCE result row with
  effect sizes populated. (Row `7505`.)

If step 1's query returns several rows for the same district/period, prefer
the one tagged `outcome_analysis`.

## 8. Rows that look like duplicates may each be one grade — check population scope before touching anything

A single trial can have many `active` rows that share the same `use_metric`
and `assessment_metric` — not archived, not tagged differently, genuinely
identical-looking metadata. **Do not assume these are re-run duplicates and
pick one.** Some assessments (state summative tests especially) are only
administered in certain grades, and the source system runs a **separate
analysis per grade** rather than one combined model. Seven same-looking rows
can mean seven grades, not seven attempts at the same thing.

**Check `result->'grade_level'` on each row before deciding anything:**

```sql
SELECT id, use_metric, assessment_metric, result->'grade_level' AS grade_level_scope
FROM impact_analyses
WHERE id IN (<candidate ids>);
```

- **If every row covers the same grade(s):** they're genuine duplicates — pull
  `created_at`/`updated_at` and take the most recently updated one; the rest
  are almost always someone iterating on the trial setup, not scheduled
  re-runs.
- **If each row covers a different single grade:** they are not duplicates.
  Include all of them — they collectively make up the full grade-by-grade
  picture for that assessment, the same way `result.grade_level` inside one
  row would if the assessment were district-wide.

**Worked example:** Bellevue School District's i-Ready trial has seven
`active` rows for `"Math Time on Task"` × `"SmarterBalanced"` (ids
8076–8082) and seven more for `"ELA Time on Task"` × `"SmarterBalanced"`
(ids 8083–8089). These looked like classic re-run duplicates (same
metadata, created 5–40 minutes apart across one afternoon) — but each one
actually scopes to a single grade: 3, 4, 5, 6, 7, 8, and 10 (never 9, 11, or
12, because Washington State doesn't test those grades with SmarterBalanced).
Treating these as duplicates and keeping only the latest (as an earlier
version of this doc recommended) would have silently discarded six of the
seven grades. Always confirmed this with someone who knows the assessment's
administration schedule if the pattern doesn't reconcile on its own.

## 9. Multiple assessment metrics for the same product/period — check population scope first

A trial can run separate outcome analyses against two different assessments
for the same product and period (e.g., a state summative test *and* the
product's own internal diagnostic). Do **not** assume these describe the same
population just because the product and dates match — **check
`result.grade_level` (or the school list in `cov1`) on every row involved,
including every per-grade row from §8, before treating them as comparable.**

Worked example: Bellevue's i-Ready trial (2025–26) evaluated two outcome
measures for the same Math/ELA usage data:

| | iReady (internal diagnostic) | SmarterBalanced (WA state test) |
|---|---|---|
| Population | All of K–12, one analysis per subject | Grades 3, 4, 5, 6, 7, 8, 10 only — one analysis **per grade** (see §8) |
| Math effect | Significant positive in every grade K–8; fades by 9th–10th | Significant positive in grades 3, 4, 7, 8; not significant in 5, 6; inconclusive at grade 10 (only 52 of 1,684 students had a matched score) |
| ELA effect | Significant positive only K–3rd; not significant from 4th on | Significant positive only in grades 3, 4; not significant 5th–10th |

These are not two readings of one finding, and once the full SmarterBalanced
picture is assembled (not just the grade-10 row), the more useful conclusion
is that **both measures agree**: effects are strongest and most reliable in
the earliest grades and fade going into middle and high school. Grade 10's
SmarterBalanced result needs its own caveat beyond "not significant" — its
matched sample (52) is far smaller than every other grade's (roughly
1,300–1,900), so it's inconclusive due to data availability, not evidence
that the effect disappears.

**When building a brief from a case like this:** present each outcome
measure's full population (not a single grade in isolation) and, if both
measures are available for the same grade, note whether they agree. Never
average, blend, or present two differently-scoped measures as columns of the
same table — a reader would reasonably assume they describe the same
students, and they may not.

## 10. Caveats

- **This is real production data, not de-identified.** `organization_id` /
  `organizations.name` will be the actual district (e.g. "Southeast Polk
  Community School District"). Keep using an anonymized district label (as the
  existing deliverables already do) in anything shared outside the immediate
  RCE team.
- **Not every trial has an `impact_analyses` row.** The `trials` table itself
  is sparse and mostly historical (see the six ALEKS trials found 2015–2018);
  a current engagement may have no row here yet, in which case the PDF/Gemini
  path in `SKILL.md` is still the fallback.
- **`impact_errors` is the data-quality flag column** — check it before
  trusting a row; it maps directly to the brief's Appendix D notes.
- **`recommended_use` of `0` or blank means no dosage goal was configured,
  not that a goal existed and was missed.** On Bellevue's i-Ready rows,
  `target_usage: 0` makes every user with any usage trivially "meet" the
  (nonexistent) goal — the `fidelity_group` breakdown is meaningless here.
  Check for a real, positive `recommended_use` before reporting a usage-
  compliance percentage; if there isn't one, report raw average usage only
  and say plainly that no dosage goal was set for this trial.
