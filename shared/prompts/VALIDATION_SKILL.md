---
name: rce-validation
description: >-
  Validate a RCEReport JSON produced by the extraction pipeline and return a
  structured ValidationReport. Use this whenever you receive an RCEReport JSON
  and need to assess whether it is ready for the QA gate — checking schema
  compliance, arithmetic consistency, semantic plausibility, spatial-drift
  signatures, and client-specific rules. This is Phase 3 QA (Validation) of
  the ISEA meta-analysis pipeline. Reach for it any time an extracted
  RCEReport JSON needs to be assessed before passing downstream.
---

# RCE Validation (RCEReport JSON → structured ValidationReport)

## What this agent produces

One `RCEReport` JSON → one **`ValidationReport`** JSON object structured as:

```json
{
  "verdict": "pass" | "pass_with_flags" | "fail",
  "confidence_score": 0.0,
  "source_filename": "ALEKS 1.pdf",
  "issues": [
    {
      "field": "subgroup_findings[2].effect_size_value",
      "severity": "fail" | "flag" | "warn",
      "message": "Plain-English description of the problem.",
      "suggested_fix": "Actionable re-extraction instruction."
    }
  ],
  "field_confidence": {
    "effect_size_value": "high" | "medium" | "low" | "flagged"
  },
  "training_annotation": {
    "original_json": {},
    "issues": [],
    "corrections_needed": [],
    "drift_suspected": [],
    "reviewed_by": null,
    "reviewed_at": null
  }
}
```

`training_annotation` is populated **only when verdict is `fail`** — it is the
record that feeds the training feedback loop. Leave it `null` on pass/pass_with_flags.

## The single most important rule

**Do not pass bad data forward.** A false flag that sends a record back for
human review costs one review cycle. A false pass that lets a wrong effect size
or a swapped subgroup reach the leader artifact costs trust in the entire
pipeline and may affect real district decisions.

When in doubt: **flag it, don't pass it.**

## Verdict definitions

| Verdict | Meaning |
|---|---|
| `pass` | Zero `fail`-severity issues. All `flag` and `warn` issues are either absent or carry a human-acknowledged note. Ready for QA gate. |
| `pass_with_flags` | Zero `fail` issues. One or more unresolved `flag` issues. Send to QA gate but surface flags to the reviewer. |
| `fail` | One or more `fail`-severity issues. Record must return to the extraction step. Populate `training_annotation`. |

## Confidence score

A single float 0.0–1.0 summarizing overall extraction confidence:

- Start at 1.0.
- Subtract 0.20 per `fail` issue.
- Subtract 0.10 per `flag` issue.
- Subtract 0.03 per `warn` issue.
- Floor at 0.0. Cap at 1.0.

A `pass` record should have confidence ≥ 0.80. Below 0.60 always warrants
human review regardless of verdict.

## Field confidence tiers

Assign a tier to every field you assess. Use these definitions consistently:

| Tier | Meaning |
|---|---|
| `high` | Field came from plain text (header card, report title, ESSA label). No visual reading required. Cross-checks pass. |
| `medium` | Field came from a chart but cross-checks pass and no drift risk was detected. |
| `low` | Field came from a chart with non-trivial drift risk, or cross-check was partial (e.g. only one direction confirmed). |
| `flagged` | A specific issue was raised against this field. Always accompanies a corresponding entry in `issues`. |

You do not need to assign a tier to every field in the schema — focus on
fields that have a non-obvious confidence level. Plain header fields not
touched by visual reading can be omitted from `field_confidence`; reviewers
will assume `high` for unlisted fields.

---

## Validation checks (run in this order)

### Check 1 — Schema compliance  (severity: `fail`)

Failing any of these produces a `fail` verdict.

- **All CORE fields are present and non-null.** CORE fields are those documented
  as `[CORE]` in `rce_schema.py`: `report_title`, `product_name`, `district_name`,
  `academic_year`, `report_period`, `essa_tier`, `essa_tier_label`,
  `analysis_method`, `number_of_rces`, `grade_levels`, `outcome_measure`,
  `overall_effectiveness`, `overall_statistical_significance`, `effect_size_raw`,
  `effect_size_value`, `usage` (with its own CORE sub-fields). Check each.
- **All META fields are populated.** `source_filename`, `extraction_model`,
  `extraction_timestamp`, `extraction_schema_version` must all be non-null strings.
- **Enum values are valid.** Every `essa_tier`, `overall_effectiveness`,
  `overall_statistical_significance`, `analysis_method`, `effect_size_type`,
  `subgroup_category` must match the schema's enum. An unrecognized string value
  here is an extraction error, not a data ambiguity.
- **Types match.** `effect_size_value` and `usage_compliance_rate` must be
  floats. `sample_size_min`, `sample_size_max`, and all subgroup `sample_size`
  fields must be integers. `grade_levels` and `subgroup_findings` must be lists.
  `essa_tier` must be an integer (1–4).
- **`SubgroupFinding` CORE fields.** Each finding in `subgroup_findings` must
  have non-null: `effectiveness`, `essa_tier`, `subgroup_category`,
  `subgroup_value`, `grade_levels`, `usage_metric`, `outcome_measure`.
- **`subgroup_category_custom` present when required.** If any finding has
  `subgroup_category = "custom"`, it must also have a non-null
  `subgroup_category_custom` string.

---

### Check 2 — Arithmetic consistency  (severity: `fail`)

These are objective and have no ambiguity; a mismatch is always an extraction
error.

- **`effect_size_raw` → `effect_size_value` parse.** Strip leading sign
  characters and spaces from `effect_size_raw`, parse as float, and compare
  to `effect_size_value`. A mismatch beyond ±0.001 is a `fail`. Example:
  `"+0.20"` should parse to `0.20`.
- **`sample_size_min ≤ sample_size_max`.** If both are present and min > max,
  fail. (The schema validator catches this, but confirm it here too.)
- **Subgroup `sample_size` ≤ `sample_size_max`.** No individual subgroup can
  have more students than the total sample.
- **`usage_compliance_rate` ∈ [0.0, 1.0].** Any value outside this range is
  an extraction error (e.g., a percentage recorded as 27 instead of 0.27).
- **CI bounds vs. `statistical_significance` cross-check.** For any finding
  where `statistical_significance = "significant"` AND a CI is parseable from
  the `notes` field (format `CI: (lower, upper)`), confirm the CI excludes 0
  (both bounds same sign). If CI includes 0 but significance is `"significant"`,
  or vice versa, flag it as `fail`.
- **`effect_size_value` sign matches `overall_effectiveness`.** A positive
  effect size paired with `overall_effectiveness = "negative"` (or vice versa)
  is a `fail`. `neutral` and `not_reported` are exempt.

---

### Check 3 — Semantic plausibility  (severity: `flag`)

These checks reflect domain knowledge about typical education research values.
A violation does not guarantee an error, but always warrants a flag for human
review.

- **Pearson's r bounds.** If `effect_size_type = "pearson_r"`, then
  `|effect_size_value| < 1.0`. Values ≥ 1.0 or ≤ -1.0 are impossible; fail.
  Values in [0.50, 1.0) are unusually large for education research — flag.
- **Hedges' g plausibility.** If `effect_size_type = "hedges_g"`, values
  > 2.0 in absolute terms are rare in K–12 education research — flag.
- **Effect size and sample size coherence.** An effect size > 0.40 with
  n < 30 is plausible but should be flagged as low-power, high-variance.
- **Compliance rate cross-check.** If both `usage_compliance_rate` and a
  raw compliance count appear in the data (e.g., in `usage_notes`), verify
  `rate × sample_size_max ≈ count` (within ±5 students). A large mismatch
  suggests the rate was mis-read as a decimal vs. percentage.
- **Subgroup sample size sums (mutually exclusive categories).** For a
  category like `gender` where subgroups should be mutually exclusive
  (Male + Female + ...), the sum of subgroup `sample_size` values should
  be ≤ `sample_size_max`. A sum significantly exceeding the total (>110%)
  suggests a count was duplicated or mis-assigned.
- **`essa_tier` vs. `analysis_method` coherence.** Tier 1–2 requires
  experimental/quasi-experimental design; Tier 3 is consistent with partial
  correlation. A Tier 1 or 2 with `analysis_method = "partial_correlation"`
  is suspicious — flag.
- **`overall_statistical_significance` vs. `overall_effectiveness`.** A
  `positive` or `negative` effectiveness paired with `not_reported`
  significance is a flag — the platform always reports significance for
  primary findings.

---

### Check 4 — Spatial-drift signatures  (severity: `flag`)

Spatial drift (callout values assigned to the wrong bar) is the #1 failure
mode in chart-heavy extractions. These are heuristic detectors — they identify
patterns characteristic of drift, not proof of it. Every hit requires a flag.

- **Adjacent identical effect sizes.** If two consecutive findings in
  `subgroup_findings` (same subgroup category, adjacent in the list) share
  an identical `effect_size_value`, flag both. Example: Black AA = 0.25,
  White = 0.25 — a suspicious match that suggests the same callout was
  re-used. Allow an exact match only if both findings also share identical
  `sample_size` and `statistical_significance` (some reports genuinely round
  to the same value — but then all three should agree).
- **Uniform effectiveness across a diverse category.** If all findings under
  `race_ethnicity` (typically 4–7 subgroups) carry the same `effectiveness`
  value AND the same `statistical_significance`, flag the whole group. Real
  reports almost always show at least one neutral or not-significant subgroup
  in a multi-ethnicity set.
- **`Visual Ambiguity` note present.** Any finding with a `notes` field
  containing the string `"Visual Ambiguity"` (case-insensitive) must be
  flagged. These are records the extraction agent itself was uncertain about.
  Always flag; never silently pass.
- **Effect size value repeated in `overall_effectiveness` and subgroup.**
  If `effect_size_value` (overall) appears as the `effect_size_value` in
  a subgroup finding, that subgroup may have been copied from the header
  rather than read from the dot plot. Flag if the subgroup `sample_size`
  also matches `sample_size_max`.
- **Missing subgroup callout for a category with ≥4 expected dots.** If a
  category (e.g., Ethnicity) has 4+ subgroup values defined but fewer than
  half have numeric `effect_size_value` (the rest are null), and none have a
  `Visual Ambiguity` flag, flag the category. Either values were dropped, or
  the ambiguity wasn't flagged during extraction.

---

### Check 5 — Completeness  (severity: `warn`)

Warnings do not block a pass but are surfaced to the QA reviewer.

- **`subgroup_findings` empty or null.** If the extracted record has no
  subgroup findings, warn. Most LearnPlatform reports have at least Gender
  and/or Ethnicity toggles. An empty list may mean the toggles weren't read.
- **`effect_size_type` null when `effect_size_value` is present.** The type
  is needed for downstream synthesis — warn and suggest inferring from
  `analysis_method` (correlative → `pearson_r`; experimental → `hedges_g`).
- **EXT narrative fields absent.** If both `summary_key_findings` and
  `next_steps_verbatim` are null, warn. These are used by the artifact phase.
- **`report_period_label` absent.** The label (`BOY-MOY`, `MOY-EOY`,
  `Full Year`) is needed for cross-report comparison. It's derivable from
  `report_period` dates — warn and suggest inferring it.
- **`covariates` null.** The analysis method section almost always lists
  covariates for partial-correlation studies. A null value suggests the
  Demographics & Methods tab wasn't read.

---

### Check 6 — Client-specific rules  (severity: `flag`, configurable)

These rules are parameterized by `product_name`. Apply the matching block.
If no block matches, skip this check.

#### ALEKS (product_name == "ALEKS")

- **Effect size type.** `effect_size_type` must be `"pearson_r"`. ALEKS
  reports are treatment-only correlative studies. If `"hedges_g"` or
  `"not_reported"`, flag.
- **ESSA tier.** All ALEKS RCEs in this series are Level III. If `essa_tier`
  is not `3`, flag and ask the extractor to confirm from the Methods tab.
- **Grade levels.** The current ALEKS report series runs Grade 6 only
  (`grade_levels = ["6"]`). If other grades are present without a
  `sample_size_notes` explaining it, flag.
- **Outcome measure.** Should reference `FastBridge aMath` or
  `Fastbridge aMath` (accept both casings). Any other outcome measure for
  an ALEKS record is suspicious — flag and note.
- **Analysis method.** Should be `partial_correlation`. Any other value
  should be flagged.

#### Template for future clients

When a new client/product is on-boarded, add a block here with:
- Expected `effect_size_type`
- Expected `essa_tier` range
- Expected `grade_levels`
- Expected `outcome_measure` keywords
- Any known quirks (e.g., non-standard compliance threshold units)

---

## Building the `training_annotation` (fail cases only)

When verdict is `fail`, populate `training_annotation` as follows:

```json
{
  "original_json": { /* the full RCEReport JSON as received */ },
  "issues": [ /* same list as top-level issues */ ],
  "corrections_needed": [
    {
      "field": "subgroup_findings[2].effect_size_value",
      "current_value": 0.19,
      "instruction": "Re-trace the leader line on the Ethnicity dot plot for Hispanic/Latino. The CI (-0.07, 0.42) suggests this is correct, but the adjacent match with [1] requires manual confirmation."
    }
  ],
  "drift_suspected": [
    {
      "category": "race_ethnicity",
      "findings_indices": [1, 2],
      "reason": "Identical effect_size_value 0.19 in adjacent subgroups Black AA and Hispanic/Latino."
    }
  ],
  "reviewed_by": null,
  "reviewed_at": null
}
```

The `corrections_needed` list should be actionable re-extraction instructions
tied to specific fields. Reference the chart type and the label to re-read.
Do not write vague instructions like "check the chart" — name the chart, name
the category, name what to trace.

---

## Final self-check before returning

Run through this list after generating the `ValidationReport`:

1. **All six check categories completed?** Schema, arithmetic, plausibility,
   drift, completeness, client-specific. Do not skip a category because the
   record "looks fine."
2. **Every `Visual Ambiguity` note flagged?** Search `subgroup_findings[*].notes`
   for the string — it should never silently pass.
3. **CI bounds checked against significance for every subgroup finding?**
   Parse the CI from the `notes` field if it's there.
4. **Drift check run on every subgroup category, not just Ethnicity?**
   Adjacent-identical check applies to Gender, School, Prior Performance, etc.
5. **`confidence_score` computed last**, after all issues are collected.
6. **Verdict defensible?** A `pass` means you would stake the downstream
   artifact on this record. If anything gave you pause, `pass_with_flags`
   is the correct call.
7. **`training_annotation` populated iff verdict is `fail`.** Don't leave it
   populated on a passing record — it creates noise in the training corpus.
