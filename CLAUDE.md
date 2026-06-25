# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

Automates extraction and synthesis of LearnPlatform Rapid Cycle Evaluation (RCE) reports into an interactive HTML research brief. The starting product is ALEKS. Reports are chart-heavy dashboard PDFs; the core engineering challenge is reliable structured extraction from them, especially bar charts where callout labels drift spatially from their bars.

**Sponsor:** Instructure / LearnPlatform — **Stakeholder:** Amanda Cadran (senior researcher)

## Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | MVP: PDF → extraction → interactive HTML artifact |
| `meta-analysis-full` | Extended: full synthesis pipeline, District Research Brief at scale |
| `llm-direct` | Experimental: raw RCE data → LLM directly, bypassing PDFs |

All branches share the Phase 3 parsing and extraction foundation built in `contributors/sherman/`.

## Setup

```bash
pip install pydantic>=2.0 pdfplumber anthropic pandas jupyter pytest
# or: conda env create -f environment.yml && conda activate meta-analysis
```

`data/sample_reports/` is gitignored — PDFs stay off the repo.

## Key Commands

**Schema smoke-check** (run before committing schema or fixture changes):
```bash
python3 -c "
import json, sys
sys.path.insert(0, 'deliverables')
from rce_schema import RCEReport
d = json.load(open('data/annotations/aleks_worked_example.json')); d.pop('_comment', None)
print('SCHEMA OK' if RCEReport(**d) else 'FAIL')
"
```

**Run the schema directly** (prints worked-example JSON):
```bash
python3 deliverables/rce_schema.py
```

**Project status digest:**
```bash
python3 shared/utils/status_report.py         # print to terminal
python3 shared/utils/status_report.py --post  # post to Slack (requires SLACK_WEBHOOK_URL)
```

**Tests** (once populated):
```bash
pytest shared/tests/
```

## Architecture

The pipeline has five stages:

1. **PDF ingestion** — `pdfplumber` (or `PyMuPDF` / Tesseract OCR for scanned pages) converts RCE PDFs to raw text.
2. **LLM extraction** — Claude receives structured text + the extraction skill (`contributors/sherman/rce-extraction/SKILL.md`) and returns JSON conforming to the Pydantic schema. Gemini Enterprise is used in parallel by Amanda for chart-heavy pages.
3. **Schema validation** — `RCEReport` (Pydantic v2) validates the JSON; a `model_validator` auto-parses `effect_size_raw → effect_size_value` and checks sample-size range.
4. **QA gate** — `spot_check.html` is a self-contained browser page; it loads an `RCEReport` JSON, confidence-tiers every value, floats ambiguity flags, and exports a verified JSON + review log. Only verified data passes into the leader-facing artifact.
5. **Output** — `deliverables/artifact.html` (interactive HTML research brief, Phase 4+).

## Schema Overview (`rce_schema.py`)

Three models: `RCEReport` (root) → `UsageAnalysis` (nested) + `List[SubgroupFinding]` (nested list).

Field tiers:
- **CORE** — must extract; validation fails without these.
- **EXT** — extract if present; `None` if absent — never fabricate.
- **META** — provenance fields populated by the pipeline, not the LLM (`source_filename`, `extraction_model`, `extraction_timestamp`, `extraction_schema_version`).

Key enums: `ESSATier` (1–4), `EffectivenessDirection`, `StatisticalSignificance`, `AnalysisMethod`, `EffectSizeType` (`pearson_r` / `hedges_g` — the platform does not use Cohen's d), `SubgroupCategory`.

Current version: **DRAFT v0.1**. Bump the version string when adding fields.

## Where Things Live

Phase 3 assets are in their canonical homes:

| File | Location |
|---|---|
| Pydantic extraction schema | `deliverables/rce_schema.py` |
| Gold fixture (worked example) | `data/annotations/aleks_worked_example.json` |
| Extraction skill + field source map | `shared/prompts/SKILL.md`, `shared/prompts/field_source_map.md` |
| QA gate (spot-check tool) | `deliverables/spot_check.html` |
| Leader-facing evidence brief | `deliverables/artifact.html` |
| Status report script | `shared/utils/status_report.py` |

## Engineering Conventions

- **Pydantic v2 only** — no v1 compatibility shims (`model_dump()` not `.dict()`, etc.)
- All new scripts go in `contributors/sherman/` during development; promote to `shared/` or `deliverables/` when ready.
- `.DS_Store` is globally gitignored — do not re-add.
- For full extraction guidance (spatial-drift protocol, chart-reading steps, mapping rules), see `contributors/sherman/CLAUDE.md` and `contributors/sherman/rce-extraction/SKILL.md`.

## Glossary

| Term | Meaning |
|---|---|
| RCE | Rapid Cycle Evaluation — one LearnPlatform report |
| ESSA tiers | Evidence levels I–IV (Strong / Moderate / Promising / Rationale) |
| BOY / MOY / EOY | Beginning / Middle / End of year testing windows |
| Spatial drift | The failure mode where LLM assigns a chart callout value to the neighboring bar instead of the correct one |
| Pearson's r | Correlation effect size used in treatment-only/correlative ALEKS reports |
| Hedge's g | Effect size used in experimental/quasi-experimental reports |
