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

## 8. Picking among duplicate `active` rows

A single trial can have many `active` rows that share the same `use_metric`
and `assessment_metric` — not archived, not tagged differently, genuinely
identical-looking metadata. This isn't necessarily bad data; it's usually the
result of someone re-running the same analysis configuration repeatedly while
setting up a trial.

**Pull `created_at`/`updated_at` and take the most recently updated row.**

```sql
SELECT ia.id, ia.use_metric, ia.assessment_metric, ia.created_at, ia.updated_at
FROM impact_analyses ia
JOIN tools tl ON tl.id = ia.tool_id
LEFT JOIN organizations o ON o.id = ia.organization_id
WHERE o.name ILIKE '%<district name>%'
  AND tl.name ILIKE '%<tool name>%'
ORDER BY ia.use_metric, ia.assessment_metric, ia.updated_at DESC;
```

Worked example: Bellevue School District's i-Ready × Math Time on Task ×
SmarterBalanced had seven `active` rows (ids 8076–8082), created 5–40 minutes
apart across about three hours on one day. That's someone iterating on the
setup, not a scheduled refresh. The last one in the sequence (`8082`,
by `updated_at`) is the one that reflects the final configuration — use it,
not an arbitrary or lowest/highest id.

## 9. Multiple assessment metrics for the same product/period — check population scope first

A trial can run separate outcome analyses against two different assessments
for the same product and period (e.g., a state summative test *and* the
product's own internal diagnostic). Do **not** assume these two rows describe
the same population just because the product and dates match — **check
`result.grade_level` (or the school list in `cov1`) before treating them as
comparable.**

Worked example: Bellevue's i-Ready trial (2025–26) has two outcome rows for
`"Math Time on Task"`:

| | vs. iReady (internal diagnostic) | vs. SmarterBalanced (WA state test) |
|---|---|---|
| Population | All of K–12 (13 grade levels) | 10th grade only |
| `students_count` | 14,081 | 1,684 in scope, but only 52 had a matched score |
| Effect size | r = +0.095, p = 2.5×10⁻²² | r = +0.182, p = 0.335 (not significant) |

These aren't two readings of one finding — SmarterBalanced is only
administered in grade 10 in Washington, so that row is structurally confined
to a single grade with a tiny matched sample, while the internal-diagnostic
row covers the whole district. **When grade/population scope differs between
two assessment-metric rows, report them as separate, differently-scoped
findings.** Never average, blend, or present them as two columns of the same
table — a reader would reasonably assume they're describing the same
students, and they aren't.

If you're building a brief from a case like this, lead with the row that has
real statistical power (here, the district-wide iReady result) as the primary
evidence, and present the narrower row as an explicitly caveated side note
(sample size, grade restriction, and non-significance stated up front), not
as a second opinion on the same question.

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
