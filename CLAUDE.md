# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

Automates extraction and synthesis of LearnPlatform Rapid Cycle Evaluation (RCE) reports into a district-facing Research Brief (Google Doc). The starting product is ALEKS. Reports are chart-heavy dashboard PDFs; the core engineering challenge is reliable structured extraction from them, especially bar charts where callout labels drift spatially from their bars.

**Sponsor:** Instructure / LearnPlatform — **Stakeholder:** Amanda Cadran (senior researcher)

## Pipeline (Current)

```
Raw district data
  → P1: structures data into the RCE file format
  → P2: uploads to LearnPlatform → RCE Dashboard PDFs
  → P2 + Gemini Enterprise (Agent 1): extracts structured XLSX from PDFs
  → P2 manual review: compares XLSX vs. source PDFs
      → corrections needed? → P2 feeds correction + context to Agent 1 → corrected XLSX → re-enters review
  → Verified XLSX → Amanda
  → Amanda + Agent 2: build a Client-Specific Agent (see docs/Research_Brief_Agent_Instructions.md)
  → Client-Specific Agent + previous Research Briefs → contextual synthesis with Amanda
  → Research Brief (Google Doc)
```

**Why Gemini, not Claude:** ALEKS PDFs are image-only exports (no text layer). Claude Vision had too many spatial drift errors on bar charts. Gemini Enterprise handles chart extraction; the `shared/prompts/SKILL.md` documents the spatial-drift protocol both agents follow.

## Setup

```bash
pip install pydantic>=2.0 openpyxl anthropic pandas jupyter pytest python-dotenv
# or: conda env create -f environment.yml && conda activate meta-analysis
```

`data/sample_reports/` is gitignored — PDFs stay off the repo.

## Key Commands

**View the pipeline flowchart:**
Open `deliverables/pipeline_flowchart.html` in any browser. Click any node for a contextual description.

## Architecture

| Stage | Who | What |
|---|---|---|
| PDF ingestion | P2 | LearnPlatform exports chart-heavy dashboard PDFs |
| LLM extraction | P2 + Gemini Enterprise | Feeds PDFs to Gemini; output is a raw XLSX |
| Manual QA loop | P2 | Compares XLSX vs. PDFs; routes corrections through Agent 1 until verified |
| Synthesis setup | Amanda + Agent 2 | Build the Client-Specific Agent for the engagement |
| Synthesis | Client-Specific Agent + Amanda | Ingests verified XLSX + prior briefs; drafts Research Brief |
| Output | Amanda | Finalizes Research Brief as a Google Doc |

## Where Things Live

| File | Location |
|---|---|
| Gemini extraction skill + spatial-drift protocol | `shared/prompts/SKILL.md` |
| PDF field → source mapping | `shared/prompts/field_source_map.md` |
| Research Brief Agent instruction template | `docs/Research_Brief_Agent_Instructions.md` |
| Interactive pipeline flowchart | `deliverables/pipeline_flowchart.html` |
| Sample PDFs (gitignored) | `data/sample_reports/` |

## Engineering Conventions

- All new scripts go in `contributors/sherman/` during development; promote to `shared/` or `deliverables/` when ready.
- `.DS_Store` is globally gitignored — do not re-add.
- No Pydantic schema validation step in the live pipeline.
- For full extraction guidance (spatial-drift protocol, chart-reading steps, mapping rules), see `shared/prompts/SKILL.md`.

## Glossary

| Term | Meaning |
|---|---|
| RCE | Rapid Cycle Evaluation — one LearnPlatform report |
| ESSA tiers | Evidence levels I–IV (Strong / Moderate / Promising / Rationale) |
| BOY / MOY / EOY | Beginning / Middle / End of year testing windows |
| Spatial drift | The failure mode where an LLM assigns a chart callout value to the neighboring bar instead of the correct one |
| Pearson's r | Correlation effect size used in treatment-only/correlative ALEKS reports |
| Hedge's g | Effect size used in experimental/quasi-experimental reports |
