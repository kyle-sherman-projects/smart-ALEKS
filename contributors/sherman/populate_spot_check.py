#!/usr/bin/env python3
"""
populate_spot_check.py
======================
Read an extracted RCEReport JSON and write a ready-to-review spot_check.html
populated with the real values, confidence tiers, and source citations.

Usage
-----
.venv/bin/python3 contributors/sherman/populate_spot_check.py \
    data/annotations/aleks_extracted.json \
    --output deliverables/spot_check.html
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE = REPO_ROOT / "deliverables" / "spot_check.html"  # read-only prototype — never written to

# ── Tier / source metadata for every report-level field ──────────────────────
# (group, label, json_path, tier, source_citation)
# tier: "text" = printed on page (high confidence)
#       "chart" = read from chart callout (medium, drift-checkable)
#       "flag"  = unresolved visual ambiguity (must be resolved by a human)

FIELD_META = [
    ("Report identity", "Report title",       "report_title",                    "text",  "Dashboard header / report cover"),
    ("Report identity", "Product name",        "product_name",                    "text",  'Header card → "Product:" (p.1)'),
    ("Report identity", "District",            "district_name",                   "text",  "Report title / cover"),
    ("Report identity", "Academic year",       "academic_year",                   "text",  "Derived from Timeframe (p.1)"),
    ("Report identity", "Report period",       "report_period",                   "text",  'Header card → "Timeframe:" (p.1)'),
    ("Report identity", "Period label",        "report_period_label",             "chart", "Derived (Aug→Feb = BOY-MOY)"),
    ("Report identity", "Author",              "author",                          "text",  "Report byline"),

    ("Study design",    "ESSA tier",           "essa_tier_label",                 "chart", 'Demographics & Methods tab — "Promising Evidence"'),
    ("Study design",    "Analysis method",     "analysis_method",                 "chart", "Demographics & Methods tab"),
    ("Study design",    "Number of RCEs",      "number_of_rces",                  "chart", "Methods / Table 1"),
    ("Study design",    "Covariates",          "covariates",                      "chart", "Method description"),

    ("Sample",          "Grade levels",        "grade_levels",                    "chart", 'Outcome chart x-axis ("6th grade")'),
    ("Sample",          "Total students (n)",  "sample_size_max",                 "text",  'Header card → "Total Students:" (p.1)'),
    ("Sample",          "Sample note",         "sample_size_notes",               "text",  "Brief footnote / Table 2"),

    ("Outcomes",        "Outcome measure",     "outcome_measure",                 "text",  'Header card → "Outcome:" (p.1)'),
    ("Outcomes",        "Overall effect size", "effect_size_raw",                 "text",  'Header gauge "Overall Effect Size" (p.1)'),
    ("Outcomes",        "Effect size (parsed)","effect_size_value",               "text",  "Parsed from header gauge / Overall dot ES callout"),
    ("Outcomes",        "Effect size type",    "effect_size_type",                "chart", "Methods (partial correlation → pearson_r)"),
    ("Outcomes",        "Overall effectiveness","overall_effectiveness",          "chart", "Gauge color (green) / Overall dot color"),
    ("Outcomes",        "Overall significance","overall_statistical_significance","text",  'Narrative "statistically significant" / Overall dot CI excludes 0'),

    ("Usage",           "Usage metric",        "usage.usage_metric",              "text",  'Header card → "Usage Metric:" (p.1)'),
    ("Usage",           "Recommended dosage",  "usage.usage_compliance_threshold","text",  'Header card → "Recommended Dosage:" (p.1)'),
    ("Usage",           "Compliance rate",     "usage.usage_compliance_rate",     "chart", 'Benchmark chart — green "met or exceeded" bar/banner'),
    ("Usage",           "Usage period (weeks)","usage.usage_period_weeks",        "chart", 'Usage-distribution banner ("across N weeks")'),
    ("Usage",           "Usage notes",         "usage.usage_notes",               "text",  '"On average, how many minutes…" card (p.1)'),
]


def get_nested(d: dict, path: str):
    """Resolve a dotted path like 'usage.usage_metric' into a value."""
    parts = path.split(".")
    val = d
    for p in parts:
        if not isinstance(val, dict):
            return None
        val = val.get(p)
    return val


def fmt(val) -> str:
    """Format a value for display in the spot-check UI."""
    if val is None:
        return "—"
    if isinstance(val, list):
        return ", ".join(str(v) for v in val)
    if isinstance(val, float):
        return f"{val:.2f}" if val != int(val) else str(int(val))
    return str(val)


def build_record(data: dict) -> dict:
    """Transform an RCEReport dict into the spot_check RECORD format."""

    record = {
        "meta": {
            "source_filename": data.get("source_filename", ""),
            "product": data.get("product_name", ""),
            "district": data.get("district_name", ""),
            "period": data.get("report_period", ""),
            "model": data.get("extraction_model", ""),
            "schema": f"rce_schema.py v{data.get('extraction_schema_version', '0.1')}",
        },
        "fields": [],
        "subgroups": [],
    }

    for group, label, path, tier, source in FIELD_META:
        val = get_nested(data, path)
        if val is None and path not in ("author", "sample_size_notes", "usage.usage_notes"):
            continue  # skip truly absent optional fields
        record["fields"].append([group, label, path, fmt(val), tier, source])

    for sf in (data.get("subgroup_findings") or []):
        ci_lo = sf.get("confidence_interval_lower")
        ci_hi = sf.get("confidence_interval_upper")
        ci_str = f"({ci_lo}, {ci_hi})" if ci_lo is not None and ci_hi is not None else "—"

        notes = sf.get("notes") or ""
        is_ambiguous = "Visual Ambiguity" in notes or sf.get("effect_size_raw") is None

        cat = sf.get("subgroup_category", "")
        if sf.get("subgroup_category_custom"):
            cat = sf["subgroup_category_custom"]

        record["subgroups"].append({
            "cat": cat,
            "val": sf.get("subgroup_value", ""),
            "eff": sf.get("effectiveness", "not_reported"),
            "es": sf.get("effect_size_raw") or "—",
            "ci": ci_str,
            "n": str(sf["sample_size"]) if sf.get("sample_size") is not None else "—",
            "sig": sf.get("statistical_significance", "not_reported"),
            "tier": "flag" if is_ambiguous else "chart",
            "note": notes or f"{'Green' if sf.get('effectiveness')=='positive' else 'Yellow'} dot; CI {'excludes' if sf.get('statistical_significance')=='significant' else 'includes'} 0.",
        })

    return record


def inject_record(html: str, record: dict) -> str:
    """Replace the const RECORD = {...}; block in the HTML with the new record."""
    record_js = json.dumps(record, indent=2, ensure_ascii=False)
    new_block = f"const RECORD = {record_js};"
    return re.sub(r"const RECORD\s*=\s*\{.*?\};", new_block, html, flags=re.DOTALL)


def main():
    parser = argparse.ArgumentParser(
        description="Populate spot_check.html with a real extracted RCEReport JSON"
    )
    parser.add_argument("json_path", help="Path to extracted RCEReport JSON")
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output HTML path (default: data/reviews/<stem>_spot_check.html)",
    )
    args = parser.parse_args()

    json_path = Path(args.json_path)
    data = json.loads(json_path.read_text())
    record = build_record(data)

    out_path = Path(args.output) if args.output else (
        REPO_ROOT / "data" / "reviews" / f"{json_path.stem}_spot_check.html"
    )
    if out_path.resolve() == TEMPLATE.resolve():
        print("ERROR: output path resolves to the spot_check.html prototype — choose a different path.", file=sys.stderr)
        sys.exit(1)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    html = TEMPLATE.read_text()
    updated = inject_record(html, record)

    out_path.write_text(updated)
    fields = len(record["fields"])
    subgroups = len(record["subgroups"])
    flags = sum(1 for s in record["subgroups"] if s["tier"] == "flag")
    print(f"Written to {out_path}")
    print(f"  {fields} report-level fields · {subgroups} subgroup rows · {flags} ambiguity flag(s)")


if __name__ == "__main__":
    main()
