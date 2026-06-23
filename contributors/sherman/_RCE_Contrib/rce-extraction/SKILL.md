---
name: rce-extraction
description: >-
  Parse a LearnPlatform Rapid Cycle Evaluation (RCE) "Full Report" PDF into a
  single structured JSON record conforming to rce_schema.py (the RCEReport model).
  Use this whenever you are handed an RCE report, an ALEKS / Amplify / Lexia /
  i-Ready "Usage & Outcomes" PDF export, or any LearnPlatform evaluation
  dashboard and asked to extract metrics — effect sizes, sample sizes, usage
  compliance, ESSA tier, or per-subgroup findings — even if the user just says
  "harvest the numbers from this report" or "turn this brief into data." This is
  Phase 3 (Data Harvesting) of the ISEA meta-analysis pipeline. The reports are
  chart-heavy dashboards, so this skill exists primarily to stop the model from
  misreading bar charts and effect-size dot plots (the "spatial drift" failure).
  Reach for it any time an RCE/LearnPlatform PDF needs to become structured data.
---

# RCE Extraction (LearnPlatform Full Report PDF → structured JSON)

## What this skill produces

One RCE Full Report PDF = **one `RCEReport` JSON object**. The schema is the
authority on field names, types, enums, and which fields are required (`CORE`)
vs. optional (`EXT`) vs. pipeline-populated (`META`). Read it before extracting:

- `references/rce_schema.py` — the Pydantic v2 model. The field docstrings tell
  you exactly what each field means and give example values.
- `references/field_source_map.md` — where each schema field physically lives on
  the page (which card, which chart, which callout). Read this once per report.
- `references/aleks_worked_example.json` — a correct, fully-worked ALEKS output
  to anchor format and value style.

Output a JSON object with the schema's field names. Leave `META` fields
(`source_filename`, `extraction_model`, `extraction_timestamp`,
`extraction_schema_version`) as the pipeline supplies them, or fill obvious ones
(filename) and set the rest to clearly-marked placeholders. Every `EXT` field
that isn't present in the document is `null` — do not invent it.

## The single most important rule

These reports are **interactive-dashboard screenshots**, not clean tables. Bar
values sit in floating callout boxes joined to their bar by a thin leader line,
and **the same subgroup categories are reordered from chart to chart**. The
documented failure mode (Amanda's "spatial drift") is assigning a number to the
neighboring bar instead of the correct one. If you read these charts the way you
read a table — assuming left-to-right position is stable and labels sit directly
above their bar — you will silently swap values between subgroups.

So the governing principle is: **never trust spatial position. Re-anchor every
value to its own axis label, every time, by tracing the leader line.** The
protocol below makes this concrete. Follow it for any chart you extract from.

## Document anatomy (LearnPlatform "View Usage & Outcomes" export)

The PDF is a vertical scroll of cards under three tabs. A single product export
(e.g. `ALEKS 1.pdf`) typically holds everything you need; sibling files
(`ALEKS 2..5.pdf`) are usually the same dashboard with a **different subgroup
toggle** pre-selected (Grade Level, Gender, Ethnicity, School, SpEd Status). If
several files are provided for one product, treat them as one logical report and
merge their subgroup charts — the header-level facts are identical across them
(verify this; if a header number differs, flag it).

Top to bottom you will find:

1. **Header card — "Usage & Outcomes Analysis"** (top of page 1). Plain text
   key/value pairs: Product, Timeframe, Usage Metric, Recommended Dosage,
   Outcome, Total Students, State, Year of Study, Tagline. Top-right: **Overall
   Effect Size** (e.g. `+0.20`) with a red-yellow-green gauge. These are the
   easiest, highest-confidence fields — extract them as literal text.
2. **Usage Analysis** — a donut ("% Used / Not Used") and a single number
   ("On average, how many minutes…" e.g. `486 minutes`).
3. **Usage-distribution bar chart** — students binned by minutes/dosage, each
   bar tagged with a "N students / X% of total users" callout.
4. **Benchmark bar chart** — "…reach the recommended usage benchmark?" The green
   bar / green callout ("156 students / 27% of total users", or a "met or
   exceeded the recommended dosage" banner) gives the compliance rate.
5. **Per-group toggle charts** — three charts, each with a
   `Grade Level | Gender | Ethnicity | School | SpEd Status` toggle row:
   - "How many students in each group used the product?" (count bars)
   - "To what extent did students in each group use the product?" (**Average
     Minutes on system** bars)
   - "…reach the recommended usage benchmark?" (grouped not-using / using /
     met bars)
6. **Outcome Analysis — effect-size dot plot** — "Is greater usage of '<product>'
   related to favorable learning outcomes for different student groups?" A
   toggle row (`Overall | Grade Level | Gender | Ethnicity | Prior Performance |
   School | SpEd Status`) and a scatter of colored dots, each with a callout box
   `ES: 0.25 / CI: (0.15, 0.34) / n: 374`. **This card is the source for
   `subgroup_findings` and the overall effect size.**
7. **Demographics & Methods tab** — analysis method (partial correlation), ESSA
   tier language ("Level III / Promising Evidence"), covariates. Check it for
   `analysis_method`, `essa_tier`, `essa_tier_label`, `covariates`.

`Comments` boxes ("No comments yet.") and the `Share/Print Report` rail are
chrome — ignore them.

## Chart-reading protocol (do this before writing any chart value)

Apply this to every bar chart and dot plot you extract. It is adapted from the
visual-audit protocol the team validated against Gemini Pro; the reasoning is
spelled out so you can apply it to charts these examples don't cover.

**Step 1 — Sequential transcription, one bar at a time.** Read the horizontal
axis strictly left to right. For every bar (or dot), write a literal line before
you tabulate anything:

> "Item [k] from the left: x-axis label = [label]; the callout connected to this
> bar by its leader line reads [verbatim text]; bar color = [color]."

Writing each bar out in prose first is not busywork — it forces you to bind
*this label* to *this bar's callout* while you are looking at both, which is
exactly the binding that drift breaks.

**Step 2 — Trace the leader line, do not read top-down.** A callout box is
usually offset up and to the side of its bar, with a thin line pointing to the
bar's top. The number physically nearest a bar may belong to a *neighbor*.
Follow the line, not the proximity. On the Average-Minutes chart this is the #1
source of error.

**Step 3 — Re-read the axis for every chart; never carry order across charts.**
The count chart, the average-minutes chart, and the effect-size dot plot
routinely list the **same** categories in **different** left-to-right orders
(see `field_source_map.md` for a real ALEKS Ethnicity example where the order
changes between the count chart and the minutes chart). Re-establish the axis
labels from scratch each time. A value is only ever bound to a category name,
never to "the third bar."

**Step 4 — Cross-check the tallest and shortest.** Pick the visually tallest and
shortest bars and confirm their labels and values independently. If the tallest
bar doesn't carry the largest number, you have a swap — stop and re-trace.

**Step 5 — Reconcile against the header.** Per-group counts should roughly sum to
Total Students; a subgroup `n` should not exceed Total Students; a compliance
count and its percentage should be consistent with Total Students. If something
doesn't reconcile, re-read before recording.

**Step 6 — Flag, don't guess.** If a label is cut off, a leader line is
ambiguous, two callouts overlap, or a dot has no callout, record the value as
the string `"Visual Ambiguity"` (or set the numeric field to `null` and add a
`notes` entry naming the chart and what was unclear). A flagged gap is recoverable
downstream; a confident wrong number is not. **Never** average, interpolate, or
infer a missing bar value from the axis gridlines.

## Mapping rules (decisions the schema needs you to make)

**Effect size.** Store the verbatim string in `effect_size_raw` (keep the sign
and leading dot exactly: `"+0.20"`, `".20"`) and the parsed float in
`effect_size_value` (`0.20`). The header gauge and the "Overall" dot in the
effect-size plot should agree; if they don't, trust the dot plot's labeled
callout and note the discrepancy.

**Effectiveness direction** comes from the dot color, which the plot's own legend
defines:
- green ("students had better learning outcomes") → `positive`
- yellow ("all students had similar learning outcomes") → `neutral`
- red ("other students had better learning outcomes") → `negative`
- mixed signals across subgroups at the report level → `overall_effectiveness = mixed`
- nothing reported → `not_reported`

**Statistical significance.** A finding is `significant` when the report says so
(headline text "statistically significant") **or** the confidence interval in the
callout excludes 0 (e.g. `CI: (0.15, 0.34)` → significant; `CI: (-0.07, 0.42)` →
`not_significant`). If neither text nor CI is available, use `not_reported`.

**ESSA tier.** Map the written label to the enum: "Level I / Strong" → 1,
"Level II / Moderate" → 2, **"Level III / Promising" → 3**, "Level IV /
Demonstrates a Rationale" → 4. Keep the literal label in `essa_tier_label`
("Level III").

**Usage compliance.** `usage_compliance_threshold` is the recommended dosage as
written ("665 Minutes on system", or "30 minutes per week" — record what the
report shows; include both if both appear). `usage_compliance_rate` is the green
"met or exceeded" share as a decimal (27% → `0.27`). `usage_metric` is the
report's metric normalized to the schema's style ("Minutes on system" →
`total_time`).

**Grade levels** are strings (`["6"]`, `["3","4","5"]`), taken from the grade
axis labels ("6th grade" → "6").

## Building `subgroup_findings`

Each row is one (subgroup_category × subgroup_value) finding, sourced from the
**effect-size dot plot** under each toggle (Gender, Ethnicity, School, SpEd
Status, Prior Performance), one dot = one row. For each dot, after running the
chart protocol:

- `subgroup_category` — the toggle name, normalized: `gender`, `ethnicity`,
  `school`, `sped_status`, `prior_performance`.
- `subgroup_value` — the x-axis label (`"White"`, `"Female"`,
  `"Southeast Polk Middle"`, `"No"`, `"Lowest 40% of Fall testing scores"`).
- `effectiveness` — from dot color (rules above).
- `essa_tier` — the report's tier (same as the overall tier unless stated
  otherwise; ALEKS subgroup findings are Level III → 3).
- `effect_size_raw` / `effect_size_value` — from the callout `ES:` value.
- `statistical_significance` — from the callout `CI:` (excludes 0 ⇒ significant).
- `sample_size` — the callout `n:` value.
- `grade_levels`, `usage_metric`, `outcome_measure` — carry the report-level
  values unless the subgroup specifies otherwise.
- A dot with no callout, or a category with "not enough data," becomes a row with
  numeric fields `null` and a `notes` string saying so — don't drop it silently,
  and don't fabricate a number.

If a subgroup toggle isn't present in the provided PDFs, omit those rows (don't
guess them from the narrative). `subgroup_findings` may be an empty list.

## Final self-check before returning

1. **Schema-validate.** Mentally (or by running it) instantiate `RCEReport` with
   your JSON. Every `CORE` field present and correctly typed? Enums valid?
2. **Reconcile the arithmetic.** Subgroup `n`s and per-group counts consistent
   with Total Students; compliance count ↔ percentage ↔ total.
3. **Re-trace any value you felt unsure about** rather than leaving a confident
   guess. Confirm no two adjacent subgroups share a suspiciously identical value
   (a classic drift signature).
4. **List your flags.** Surface every `"Visual Ambiguity"` / null-with-note so a
   human can spot-check exactly those, and briefly say which charts you read
   visually vs. which came from plain header text.
