"""
rce_schema.py
=============
Pydantic v2 extraction schema for LearnPlatform Rapid Cycle Evaluation (RCE) reports.

Grounded in: Amplify Boost BOY-MOY 2025-26 Research Brief (sample report)
Status     : DRAFT v0.1 — for team review at ISEA Hackweek Day 2
Author     : Sherman Rodriguez (engineering lead)

FIELD TIERS
-----------
  CORE   — Must be present for a record to be valid. Validated in gold-standard study.
  EXT    — Extended. Extract if present; None if absent. Not required for MVP pass/fail.
  META   — Pipeline/provenance metadata. Populated by the pipeline, not the LLM.

DESIGN NOTES
------------
- SubgroupFinding is a nested list, not flat fields, because the number of
  subgroup rows varies across reports (Appendix B in sample = 6 rows).
- effect_size_raw stores the string exactly as it appears in the report;
  effect_size_value stores the parsed float. Both are kept so validation
  can catch LLM parsing errors.
- All Optional fields default to None. The pipeline sets <field>_missing=True
  flags via a post-processing step (not modeled here to keep the schema clean).
- ESSA tier is stored as both a string label ("Level III") and an int (3) for
  easier filtering downstream.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


# ── Enumerations ──────────────────────────────────────────────────────────────

class ESSATier(int, Enum):
    """ESSA evidence tier as integer for sorting/filtering."""
    TIER_1 = 1  # Strong Evidence
    TIER_2 = 2  # Moderate Evidence
    TIER_3 = 3  # Promising Evidence
    TIER_4 = 4  # Demonstrates a Rationale


class EffectivenessDirection(str, Enum):
    POSITIVE  = "positive"
    NEGATIVE  = "negative"
    NEUTRAL   = "neutral"
    MIXED     = "mixed"
    NOT_REPORTED = "not_reported"


class StatisticalSignificance(str, Enum):
    SIGNIFICANT     = "significant"
    NOT_SIGNIFICANT = "not_significant"
    NOT_REPORTED    = "not_reported"


class AnalysisMethod(str, Enum):
    PARTIAL_CORRELATION = "partial_correlation"
    REGRESSION          = "regression"
    QUASI_EXPERIMENTAL  = "quasi_experimental"
    RCT                 = "rct"
    DESCRIPTIVE         = "descriptive"
    OTHER               = "other"
    NOT_REPORTED        = "not_reported"


# ── Sub-models ────────────────────────────────────────────────────────────────

class SubgroupFinding(BaseModel):
    """
    One row from the subgroup breakdown table (Appendix B in sample report).
    Each SubgroupFinding is one combination of subgroup × grade × outcome.

    Example from sample:
        effectiveness="positive", essa_tier=3, subgroup_category="gender",
        subgroup_value="male", grade_levels=["3","4","5"],
        usage_metric="total_time", outcome_measure="Fastbridge aReading"
    """
    # CORE subgroup fields
    effectiveness: EffectivenessDirection = Field(
        ...,
        description="Direction of effect for this subgroup."
    )
    essa_tier: ESSATier = Field(
        ...,
        description="ESSA evidence tier for this subgroup finding."
    )
    subgroup_category: str = Field(
        ...,
        description="Category of subgroup (e.g. 'gender', 'ethnicity', 'school', 'sped_status')."
    )
    subgroup_value: str = Field(
        ...,
        description="Value within the category (e.g. 'male', 'white', 'Clay Elementary', 'no')."
    )
    grade_levels: List[str] = Field(
        ...,
        description="Grade levels included in this subgroup analysis (e.g. ['3','4','5'])."
    )
    usage_metric: str = Field(
        ...,
        description="Usage metric used in this subgroup analysis (e.g. 'total_time')."
    )
    outcome_measure: str = Field(
        ...,
        description="Outcome measure for this subgroup (e.g. 'Fastbridge aReading')."
    )

    # EXT subgroup fields
    effect_size_raw: Optional[str] = Field(
        None,
        description="[EXT] Effect size as reported in text (e.g. '.10'). None if not reported."
    )
    effect_size_value: Optional[float] = Field(
        None,
        description="[EXT] Parsed float of effect size. None if not parseable."
    )
    statistical_significance: StatisticalSignificance = Field(
        StatisticalSignificance.NOT_REPORTED,
        description="[EXT] Statistical significance for this subgroup finding."
    )
    sample_size: Optional[int] = Field(
        None,
        description="[EXT] N for this subgroup if reported separately."
    )
    notes: Optional[str] = Field(
        None,
        description="[EXT] Any qualifying notes (e.g. 'not enough data to run analysis')."
    )


class UsageAnalysis(BaseModel):
    """
    Describes how the edtech product was used, distinct from outcome findings.
    Maps to the Usage Analysis section / Table 1 of the sample report.
    """
    # CORE
    usage_metric: str = Field(
        ...,
        description="How usage was measured (e.g. 'total_time', 'sessions', 'lessons_completed')."
    )
    usage_compliance_threshold: Optional[str] = Field(
        None,
        description="[CORE] Recommended usage benchmark (e.g. '30 minutes per week')."
    )
    usage_compliance_rate: Optional[float] = Field(
        None,
        description="[CORE] Proportion of students meeting threshold (e.g. 0.75 for 75%)."
    )
    # EXT
    usage_period_weeks: Optional[int] = Field(
        None,
        description="[EXT] Number of weeks of usage data analyzed (e.g. 25)."
    )
    usage_notes: Optional[str] = Field(
        None,
        description="[EXT] Any additional context about usage patterns."
    )


# ── Root model ────────────────────────────────────────────────────────────────

class RCEReport(BaseModel):
    """
    Root extraction model for one LearnPlatform RCE report document.

    One RCEReport = one report file = one row in the master dataset,
    with subgroup_findings as a nested list (variable length).

    FIELD COUNT SUMMARY
    -------------------
    CORE fields : 16
    EXT fields  : 12
    META fields :  4
    Subgroup    :  nested (variable, each SubgroupFinding has 7 CORE + 5 EXT)
    """

    # ── GROUP 1: Document / Provenance ─────────────────────────────────────
    # META — populated by pipeline, not LLM

    source_filename: str = Field(
        ...,
        description="[META] Original filename of the source document."
    )
    extraction_model: str = Field(
        ...,
        description="[META] LLM model used for extraction (e.g. 'claude-sonnet-4-6')."
    )
    extraction_timestamp: str = Field(
        ...,
        description="[META] ISO 8601 datetime of extraction run."
    )
    extraction_schema_version: str = Field(
        "0.1",
        description="[META] Version of this schema used for extraction."
    )

    # ── GROUP 2: Report Identity ────────────────────────────────────────────
    # CORE

    report_title: str = Field(
        ...,
        description="[CORE] Full title of the research brief as it appears in the document."
    )
    product_name: str = Field(
        ...,
        description="[CORE] Name of the edtech product evaluated (e.g. 'Amplify Boost')."
    )
    district_name: str = Field(
        ...,
        description="[CORE] Name of the school district (may be anonymized, e.g. 'Sample School District')."
    )
    author: Optional[str] = Field(
        None,
        description="[CORE] Author(s) listed on the report (e.g. 'Amanda Cadran, PhD')."
    )
    academic_year: str = Field(
        ...,
        description="[CORE] Academic year covered (e.g. '2025-2026')."
    )
    report_period: str = Field(
        ...,
        description="[CORE] Time window of data collection (e.g. '08/25/2025–02/20/2026')."
    )
    report_period_label: Optional[str] = Field(
        None,
        description="[EXT] Human-readable label for period (e.g. 'BOY-MOY', 'MOY-EOY', 'Full Year')."
    )

    # ── GROUP 3: Study Design ───────────────────────────────────────────────
    # CORE

    essa_tier: ESSATier = Field(
        ...,
        description="[CORE] ESSA evidence tier claimed for the primary analysis."
    )
    essa_tier_label: str = Field(
        ...,
        description="[CORE] ESSA tier label as written in the report (e.g. 'Level III', 'Tier III')."
    )
    analysis_method: AnalysisMethod = Field(
        ...,
        description="[CORE] Primary statistical method used (e.g. 'partial_correlation')."
    )
    number_of_rces: int = Field(
        ...,
        description="[CORE] Total number of RCEs reported in this brief."
    )

    # EXT
    covariates: Optional[List[str]] = Field(
        None,
        description="[EXT] Control variables included in the analysis (e.g. ['school', 'grade_level'])."
    )
    analysis_method_notes: Optional[str] = Field(
        None,
        description="[EXT] Verbatim or paraphrased description of method from report."
    )

    # ── GROUP 4: Sample ─────────────────────────────────────────────────────
    # CORE

    grade_levels: List[str] = Field(
        ...,
        description="[CORE] Grade levels included in the primary analysis (e.g. ['3','4','5'])."
    )
    sample_size_min: Optional[int] = Field(
        None,
        description="[CORE] Minimum sample size across RCEs (from 'Sample Size Range' in Table 1)."
    )
    sample_size_max: Optional[int] = Field(
        None,
        description="[CORE] Maximum sample size across RCEs."
    )

    # EXT
    sample_size_notes: Optional[str] = Field(
        None,
        description="[EXT] Any caveats on sample (e.g. 'not enough data for Grade X subgroup')."
    )

    # ── GROUP 5: Outcomes ───────────────────────────────────────────────────
    # CORE

    outcome_measure: str = Field(
        ...,
        description="[CORE] Primary outcome measure name (e.g. 'MOY Fastbridge aReading Scores')."
    )
    overall_effectiveness: EffectivenessDirection = Field(
        ...,
        description="[CORE] Overall direction of effect across all RCEs."
    )
    overall_statistical_significance: StatisticalSignificance = Field(
        ...,
        description="[CORE] Whether primary findings are statistically significant."
    )
    effect_size_raw: Optional[str] = Field(
        None,
        description="[CORE] Effect size as it appears in the report (e.g. '.10'). None if not stated."
    )
    effect_size_value: Optional[float] = Field(
        None,
        description="[CORE] Parsed float. None if raw value is not parseable to float."
    )

    # EXT
    effect_size_type: Optional[str] = Field(
        None,
        description="[EXT] Type of effect size reported (e.g. \"Cohen's d\", \"partial correlation r\")."
    )
    outcome_timing: Optional[str] = Field(
        None,
        description="[EXT] When outcome was measured (e.g. 'MOY', 'EOY', 'BOY')."
    )

    # ── GROUP 6: Usage ──────────────────────────────────────────────────────
    # CORE (nested model)

    usage: UsageAnalysis = Field(
        ...,
        description="[CORE] Usage analysis details — metric, threshold, compliance rate."
    )

    # ── GROUP 7: Subgroup Findings ──────────────────────────────────────────
    # EXT (nested list — variable length)

    subgroup_findings: Optional[List[SubgroupFinding]] = Field(
        None,
        description="[EXT] Rows from the subgroup breakdown table (Appendix B). Empty list if no subgroup table present."
    )

    # ── GROUP 8: Narrative Fields ───────────────────────────────────────────
    # EXT — for synthesis phase (Phase 4), not validation MVP

    summary_key_findings: Optional[str] = Field(
        None,
        description="[EXT] 1-3 sentence summary of headline findings as stated in the report."
    )
    next_steps_verbatim: Optional[str] = Field(
        None,
        description="[EXT] Next Steps section text, verbatim or lightly cleaned."
    )

    # ── Validators ─────────────────────────────────────────────────────────

    @model_validator(mode="after")
    def parse_effect_size(self) -> "RCEReport":
        """If effect_size_raw is present and effect_size_value is None, attempt parse."""
        if self.effect_size_raw and self.effect_size_value is None:
            try:
                self.effect_size_value = float(self.effect_size_raw.strip().lstrip("="))
            except ValueError:
                pass  # Leave as None; pipeline will flag for review
        return self

    @model_validator(mode="after")
    def validate_sample_size_range(self) -> "RCEReport":
        """Ensure min <= max when both are present."""
        if (
            self.sample_size_min is not None
            and self.sample_size_max is not None
            and self.sample_size_min > self.sample_size_max
        ):
            raise ValueError(
                f"sample_size_min ({self.sample_size_min}) cannot exceed "
                f"sample_size_max ({self.sample_size_max})"
            )
        return self


# ── Example instantiation (mirrors Amplify Boost sample report) ────────────────

AMPLIFY_BOOST_EXAMPLE = RCEReport(
    # META
    source_filename="Research_Brief__Amplify_Boost_BOY-MOY_25-26.docx",
    extraction_model="claude-sonnet-4-6",
    extraction_timestamp="2026-06-23T09:00:00Z",
    extraction_schema_version="0.1",

    # Identity
    report_title="Amplify Boost Outcomes Analysis — Rapid Cycle Evaluation Summary for Sample School District",
    product_name="Amplify Boost",
    district_name="Sample School District",
    author="Amanda Cadran, PhD",
    academic_year="2025-2026",
    report_period="08/25/2025–02/20/2026",
    report_period_label="BOY-MOY",

    # Study design
    essa_tier=ESSATier.TIER_3,
    essa_tier_label="Level III",
    analysis_method=AnalysisMethod.PARTIAL_CORRELATION,
    number_of_rces=1,
    covariates=["school", "grade_level"],

    # Sample
    grade_levels=["3", "4", "5"],
    sample_size_min=545,
    sample_size_max=577,

    # Outcomes
    outcome_measure="MOY Fastbridge aReading Scores",
    overall_effectiveness=EffectivenessDirection.POSITIVE,
    overall_statistical_significance=StatisticalSignificance.SIGNIFICANT,
    effect_size_raw=".10",
    outcome_timing="MOY",

    # Usage
    usage=UsageAnalysis(
        usage_metric="total_time",
        usage_compliance_threshold="30 minutes per week",
        usage_compliance_rate=0.75,
        usage_period_weeks=25,
    ),

    # Subgroup findings (Appendix B)
    subgroup_findings=[
        SubgroupFinding(
            effectiveness=EffectivenessDirection.POSITIVE,
            essa_tier=ESSATier.TIER_3,
            subgroup_category="gender",
            subgroup_value="male",
            grade_levels=["3", "4", "5"],
            usage_metric="total_time",
            outcome_measure="Fastbridge aReading",
        ),
        SubgroupFinding(
            effectiveness=EffectivenessDirection.POSITIVE,
            essa_tier=ESSATier.TIER_3,
            subgroup_category="ethnicity",
            subgroup_value="white",
            grade_levels=["3", "4", "5"],
            usage_metric="total_time",
            outcome_measure="Fastbridge aReading",
        ),
        SubgroupFinding(
            effectiveness=EffectivenessDirection.POSITIVE,
            essa_tier=ESSATier.TIER_3,
            subgroup_category="school",
            subgroup_value="Clay Elementary",
            grade_levels=["3", "4", "5"],
            usage_metric="total_time",
            outcome_measure="Fastbridge aReading",
        ),
        SubgroupFinding(
            effectiveness=EffectivenessDirection.POSITIVE,
            essa_tier=ESSATier.TIER_3,
            subgroup_category="school",
            subgroup_value="Mitchellville Elementary",
            grade_levels=["3", "4", "5"],
            usage_metric="total_time",
            outcome_measure="Fastbridge aReading",
        ),
        SubgroupFinding(
            effectiveness=EffectivenessDirection.POSITIVE,
            essa_tier=ESSATier.TIER_3,
            subgroup_category="school",
            subgroup_value="Runnells Elementary",
            grade_levels=["3", "4", "5"],
            usage_metric="total_time",
            outcome_measure="Fastbridge aReading",
        ),
        SubgroupFinding(
            effectiveness=EffectivenessDirection.POSITIVE,
            essa_tier=ESSATier.TIER_3,
            subgroup_category="sped_status",
            subgroup_value="no",
            grade_levels=["3", "4", "5"],
            usage_metric="total_time",
            outcome_measure="Fastbridge aReading",
        ),
    ],

    summary_key_findings=(
        "Students in Grades 3 and 5 with more time on Amplify Boost had higher MOY "
        "Fastbridge aReading scores. Results are statistically significant and meet "
        "ESSA Tier III criteria. 75% of students in Grades 3-5 met the 30 min/week threshold."
    ),
)


if __name__ == "__main__":
    import json
    print(json.dumps(AMPLIFY_BOOST_EXAMPLE.model_dump(), indent=2))
