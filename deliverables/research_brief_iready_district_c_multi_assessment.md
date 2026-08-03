<!-- title: i-Ready outcomes analysis — Rapid Cycle Evaluation summary for Sample School District C -->

# i-Ready outcomes analysis — Rapid Cycle Evaluation summary for Sample School District C

**Reporting period:** September 2, 2025 – June 23, 2026
**Grade levels:** Kindergarten – 12th grade
**Usage metric:** Math Time on Task (no dosage goal configured for this trial — see data notes)
**Outcome measures:** two, evaluated separately (see below)

> **Purpose of this excerpt.** This isn't a full brief — it's a worked example of how to present a trial with two outcome measures that turned out to cover different populations. It demonstrates the rule in `shared/prompts/db_field_source_map.md` §9: never blend or table two assessment-metric rows together without first checking whether they describe the same students.

---

## Summary of impacts

This district evaluated i-Ready against two outcome measures during the same reporting period: its own internal diagnostic (**iReady**) and Washington State's summative test (**SmarterBalanced**). These are presented separately below, not side by side, because they don't describe the same population.

### Primary finding: i-Ready's internal diagnostic, district-wide (K–12)

Across 14,081 students in kindergarten through 12th grade, more time on Math Time on Task was associated with higher iReady diagnostic scores (**r = +0.09**, 95% CI: 0.08–0.11, p < 0.001). This is a modest but highly reliable effect — the sample is large enough that this result is very unlikely to be due to chance. Most individual grade levels show the same positive, significant pattern (strongest in 8th grade at r = +0.18; weakest and not significant in 9th and 10th grade).

**No dosage goal was configured for this trial.** `recommended_use` is `0` in the source data, which means there's nothing to report as a "usage compliance rate" here — that's different from a goal existing and not being met. This brief reports raw average usage (586 minutes) with no compliance percentage, and flags the missing goal in the data notes below rather than treating it as 100% compliance (which a naive read of the source data could wrongly suggest, since a zero threshold makes every user with any usage "meet" it trivially).

### Secondary finding, narrower scope: SmarterBalanced, grade 10 only

Washington State only administers the SmarterBalanced assessment in grade 10, so this outcome measure covers a much smaller, single-grade slice of the same trial: 1,684 tenth-graders were in scope, but only 52 had a usage record that could be matched to a SmarterBalanced score. Within that group, the observed effect (r = +0.18) is **not statistically significant** (95% CI: −0.18 to 0.50, p = 0.34) — the sample is too small to draw a conclusion either way.

This is not a weaker or contradicting version of the primary finding above. It's a different, much smaller population (one grade, one high-school-only sample), and the honest read is "inconclusive due to sample size," not "the effect is smaller here."

---

## Data notes & flags

- **Two outcome measures, two populations.** The iReady diagnostic result covers all of K–12; the SmarterBalanced result covers only grade 10, because that's the only grade in which Washington State administers that test. Do not present these as two columns of one table — a reader would reasonably assume they describe the same students.
- **No dosage goal configured.** `recommended_use` (`target_usage`) is `0` for this trial. Average usage is reported; a compliance percentage is not, since there is no real threshold to compare against.
- **An unusually large effect size on a small sample.** Native Hawaiian or Other Pacific Islander students show r = +0.76 (95% CI: 0.47–0.90) on the iReady diagnostic measure, at n = 29 — just at the edge of the stability threshold used elsewhere in this pipeline (n < 30 → not plotted). The source system computed a value here rather than returning null, but a effect size this large from a sample this small should be treated as unstable and not headlined without that caveat, regardless of what the raw computation returned.
- **Two grade levels returned no effect size despite adequate sample size.** 11th grade (n = 204) and 12th grade (n = 164) both show `effect_size: null` in the source data, even though neither is below the usual n = 30 threshold. The cause isn't visible from the data alone (it may be a lack of usage variance in those grades) — flagging rather than guessing.
- **Source:** `impact_analyses.id = 8075` (iReady diagnostic) and `id = 8082` (SmarterBalanced), following the tiebreak and population-scope rules in `shared/prompts/db_field_source_map.md` §§8–9. District and school names have been replaced with generic labels, consistent with the other briefs in this repository.
