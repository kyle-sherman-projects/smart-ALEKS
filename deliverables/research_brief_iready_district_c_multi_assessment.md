<!-- title: i-Ready outcomes analysis — Rapid Cycle Evaluation summary for Sample School District C -->

# i-Ready outcomes analysis — Rapid Cycle Evaluation summary for Sample School District C

**Reporting period:** September 2, 2025 – June 23, 2026
**Grade levels:** Kindergarten – 12th grade (varies by outcome measure, see below)
**Usage metrics:** ELA Time on Task, Math Time on Task (no dosage goal configured for this trial — see data notes)
**Outcome measures:** two, evaluated separately — i-Ready's internal diagnostic (district-wide) and Washington State's SmarterBalanced summative test (run one grade at a time)

> **Purpose of this excerpt.** This isn't a full brief — it's a worked example of how to present a trial with two outcome measures that cover different populations, run at different grain. It demonstrates two rules in `shared/prompts/db_field_source_map.md`: §8 (an assessment run one grade at a time produces one row per grade — that's not duplication, all of them belong in the brief) and §9 (check population scope before treating two assessment-metric rows as comparable).

---

## Summary of impacts

This district evaluated i-Ready against two outcome measures during the same reporting period. The internal diagnostic (**iReady**) is scored district-wide, K–12, in one analysis per subject. The state test (**SmarterBalanced**) is only administered in grades 3–8 and 10, and LearnPlatform runs a separate analysis per grade rather than one combined model — seven rows per subject, not duplicates of each other.

### iReady internal diagnostic — district-wide, by grade

**Math** (14,081 students district-wide): a significant positive effect in **every grade from Kindergarten through 8th grade** — strongest in 8th grade (r = +0.18, 95% CI: 0.12–0.24) — fading to not significant in 9th and 10th, with no computed effect size in 11th or 12th (see data notes).

**ELA**: significant positive only in Kindergarten through 3rd grade (strongest in 3rd, r = +0.13, 95% CI: 0.07–0.19); not significant from 4th grade on through 12th.

| Grade | Math r | Math sig | ELA r | ELA sig |
|---|---|---|---|---|
| K | +0.10 | Significant | +0.11 | Significant |
| 1st | +0.10 | Significant | +0.07 | Significant |
| 2nd | +0.08 | Significant | +0.14 | Significant |
| 3rd | +0.16 | Significant | +0.13 | Significant |
| 4th | +0.17 | Significant | +0.04 | Not significant |
| 5th | +0.06 | Significant | +0.01 | Not significant |
| 6th | +0.11 | Significant | +0.03 | Not significant |
| 7th | +0.06 | Significant | +0.05 | Not significant |
| 8th | +0.18 | Significant | +0.01 | Not significant |
| 9th | +0.04 | Not significant | −0.03 | Not significant |
| 10th | −0.06 | Not significant | −0.18 | Not significant |
| 11th | — | Not computed | +0.20 | Not significant |
| 12th | — | Not computed | −0.29 | Not significant |

**No dosage goal was configured for this trial.** `recommended_use`/`target_usage` is `0` in the source data — that's different from a goal existing and not being met. This brief reports raw average usage, not a compliance percentage, and flags the missing goal below rather than treating it as 100% compliance (a zero threshold makes any usage trivially "meet" it).

### SmarterBalanced — one analysis per tested grade (3, 4, 5, 6, 7, 8, 10)

Each row below is its own `impact_analyses` record, all created within the same few hours, one per grade, by design.

| Grade | n | Math r (95% CI) | Math sig | ELA r (95% CI) | ELA sig |
|---|---|---|---|---|---|
| 3rd | 1,330 | +0.12 (0.06, 0.18) | Significant | +0.15 (0.09, 0.21) | Significant |
| 4th | 1,383 | +0.10 (0.05, 0.16) | Significant | +0.06 (0.00, 0.11) | Significant |
| 5th | 1,447 | +0.03 (−0.02, 0.09) | Not significant | +0.03 (−0.02, 0.09) | Not significant |
| 6th | 1,550 | +0.03 (−0.02, 0.09) | Not significant | −0.03 (−0.09, 0.02) | Not significant |
| 7th | 1,544 | +0.07 (0.01, 0.12) | Significant | +0.02 (−0.04, 0.07) | Not significant |
| 8th | 1,934 | +0.06 (0.00, 0.12) | Significant | −0.05 (−0.11, 0.02) | Not significant |
| 10th | 1,684 (only 52 matched) | +0.18 (−0.18, 0.50) | Not significant | −0.10 (−0.43, 0.26) | Not significant |

**Grade 10 needs a different caveat than the rest.** Its sample size column looks similar to the other grades (1,684), but only 52 of those students actually had a matched SmarterBalanced score to pair with usage data, versus roughly 1,300–1,900 matched students in every other grade. That's not "no effect at grade 10" — it's "not enough matched data to measure an effect at grade 10." Reporting it the same way as grades 5 and 6 (which have full-size samples and genuinely show no significant effect) would misrepresent it.

**The overall pattern across both assessments agrees:** effects are strongest and most consistent in the early grades (3rd and 4th show significant positive effects on every measure above), fade through the middle grades, and are inconclusive or absent by high school.

---

## Data notes & flags

- **An assessment run one grade at a time produces one row per grade — combine them, don't pick one.** SmarterBalanced is administered separately for grades 3, 4, 5, 6, 7, 8, and 10 (not 9, 11, or 12), and LearnPlatform runs each grade as its own `impact_analyses` record. Seven near-identical-looking rows for the same product/period/metric are not duplicates to deduplicate down to one; they're one grade each; report all of them.
- **Two outcome measures, two different grains.** The iReady diagnostic is one district-wide K–12 analysis; SmarterBalanced is seven separate single-grade analyses. Never merge them into one table cell per subgroup — present them as two separate result sets, as done above.
- **Grade 10 SmarterBalanced has a data-matching problem, not a null effect.** Only 52 of 1,684 in-scope students had a matched score. Flag the sample-size caveat explicitly rather than reporting it alongside genuinely full-sample non-significant grades.
- **No dosage goal configured.** `recommended_use` (`target_usage`) is `0` for this trial. Average usage is reported; a compliance percentage is not.
- **An unusually large effect size on a small sample, elsewhere in this same trial.** Native Hawaiian or Other Pacific Islander students show r = +0.76 (95% CI: 0.47–0.90) on the iReady Math diagnostic, at n = 29 — right at the edge of the n < 30 stability threshold used elsewhere in this pipeline. The source system returned a value rather than null here; a result this large from a sample this small should still be treated as unstable and not headlined without that caveat.
- **11th and 12th grade show no computed effect size for iReady Math**, despite adequate sample size (n = 204 and 164). The cause isn't visible from the data alone — flagging rather than guessing. (ELA did compute values for those same grades, for what it's worth, so the gap is specific to the Math measure.)
- **Source:** `impact_analyses.id = 8073` (iReady, ELA) and `id = 8075` (iReady, Math) for the district-wide diagnostic; `id = 8076–8082` (SmarterBalanced, Math, grades 3/4/5/6/7/8/10) and `id = 8083–8089` (SmarterBalanced, ELA, grades 3/4/5/6/7/8/10) for the per-grade state-test analyses. (`8074` isn't part of this batch at all — not a row we dropped, just not present.) Follows the rules in `shared/prompts/db_field_source_map.md` §§8–9. District and school names have been replaced with generic labels, consistent with the other briefs in this repository.
