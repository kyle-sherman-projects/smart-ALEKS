# CLAUDE.md — smart-ALEKS

## Project Overview

This project automates the extraction and synthesis of Rapid Cycle Evaluation
(RCE) reports from Instructure's LearnPlatform into an interactive HTML research
brief. The starting product is ALEKS.

**Sponsor:** Instructure / LearnPlatform
**Stakeholder:** Amanda Cadran (senior researcher, virtual)
**Repo:** https://github.com/kyle-sherman-projects/smart-ALEKS

---

## Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | MVP: LearnPlatform PDF → extraction → interactive HTML artifact |
| `meta-analysis-full` | Extended: full synthesis pipeline, anomaly detection, District Research Brief at scale |
| `llm-direct` | Experimental: raw RCE data → LLM directly, bypassing LearnPlatform PDFs entirely |

All branches share the Phase 3 PDF parsing and extraction foundation. Divergence
happens at the synthesis and output stages.

---

## Team

| Name | Role | Strengths |
|------|------|-----------|
| Kyle Sherman | Data Engineer / AI-Prompt Engineer | Python (4/5), Git (5/5), pipeline architecture, Pydantic schema design |
| Oluwaseun Farotimi | Research / Methods Analyst | Meta-analysis, inter-rater reliability, effect size interpretation |
| Annia Yoshizumi | Data Analyst / Generalist | Data processing, edge-case handling, exploratory analysis |
| Amanda Cadran | Project Lead / Domain Expert | LearnPlatform domain knowledge, RCE report structure, QA (virtual) |

---

## Repository Structure

```
smart-ALEKS/
├── contributors/
│   ├── sherman/          # Kyle's work — currently HOSTS the Phase 3 assets below
│   │   ├── rce-extraction/
│   │   │   ├── SKILL.md                 # extraction protocol + anti-spatial-drift rules  → shared/prompts/
│   │   │   └── references/
│   │   │       ├── rce_schema.py        # working copy  → canonical deliverables/rce_schema.py
│   │   │       ├── field_source_map.md  # → shared/prompts/
│   │   │       └── aleks_worked_example.json   # gold fixture  → data/annotations/
│   │   ├── spot_check.html              # reviewer QA gate  → deliverables/spot_check.html
│   │   ├── status_report.py             # project pulse digest  → shared/utils/
│   │   ├── CLAUDE.md
│   │   └── README.md
│   ├── oluwaseun/        # Oluwaseun's validation and IRR work
│   ├── annia/            # Annia's data processing explorations
│   └── amanda/           # Amanda's domain reference materials
├── data/
│   ├── sample_reports/   # De-identified RCE PDFs (ALEKS, source data) — gitignored
│   └── annotations/      # Gold-standard human annotation files (target home for the gold fixture)
├── deliverables/
│   ├── rce_schema.py     # Pydantic v2 extraction schema — SOURCE OF TRUTH
│   ├── pipeline.ipynb    # End-to-end extraction pipeline notebook
│   └── artifact.html     # Interactive HTML research brief output (leader-facing)
├── shared/
│   ├── prompts/          # LLM prompt templates (extraction, synthesis)
│   ├── utils/            # Shared parsing and serialization utilities
│   └── tests/            # pytest unit tests
├── docs/
│   └── Day2_WorkingDoc.docx
├── .gitignore
├── CLAUDE.md
├── README.md
├── model-card.md
└── environment.yml
```

> The Phase 3 assets currently live under `contributors/sherman/`; the `→` arrows
> show their proposed canonical homes. They stay in `sherman/` until Amanda
> reviews and signs off on the move — see "Open Questions."

---

## Tech Stack

- **Language:** Python (primary)
- **PDF Parsing:** `pdfplumber` or `PyMuPDF`; Tesseract OCR if needed for scanned pages
- **Schema:** Pydantic v2 (`RCEReport`, `UsageAnalysis`, `SubgroupFinding` models; CORE/EXT/META field tiers)
- **LLM APIs:** Claude (text extraction, synthesis), Gemini Enterprise (image/chart extraction)
- **Key dependencies:** `pydantic>=2.0`, `pdfplumber`, `anthropic`, `pytest`, `pandas`, `jupyter`

---

## Extraction Schema

The Pydantic v2 schema lives at `deliverables/rce_schema.py` and is the single
source of truth for field names, types, enums, and the CORE/EXT/META tiers. If
extraction needs a new field, change the schema first (currently `DRAFT v0.1` —
bump the version). Target variables:

- Effect size, Cohen's d, p-value
- Student n (total and per subgroup)
- Grade level, subject, district, tool category
- Cost-effectiveness metrics
- Engagement metrics (average usage minutes per subgroup)

Field tiers:

- **CORE** — must extract; pipeline fails without these
- **EXT** — extract if present (else `null`; never fabricate)
- **META** — provenance/audit fields, populated by the pipeline, not the LLM

> Note: several target variables above (Cohen's d, p-value, cost-effectiveness,
> per-subgroup usage minutes) are **not yet modeled** in `rce_schema.py v0.1`,
> which is built around partial correlations. See "Open Questions."

---

## LLM Extraction Strategy

RCE reports contain both text-based tables and image-based bar charts. Use a
split approach:

**Text extraction (Claude):**
- Parse raw PDF text with `pdfplumber`
- Pass structured text to Claude with the extraction prompt
- Output: JSON matching the Pydantic schema

**Chart/image extraction (Claude primary; Gemini Enterprise retained):**
Claude is the primary chart/dot-plot reader, driven by the `rce-extraction`
skill. Gemini Enterprise stays in the mix — Amanda uses it for the same charts —
so the spatial-drift protocol below is a **shared spec both models follow**;
Gemini's prompt is still being tuned against it. Use the protocol for bar-chart
and effect-size dot-plot data.
These dashboard exports are screenshots, not clean tables: value labels sit in
floating callout boxes joined to their bar by a thin leader line, and **the same
subgroups are reordered left-to-right from chart to chart** (e.g. the ALEKS
Ethnicity count chart and average-minutes chart list the seven ethnicities in
different orders). Reading them like a table silently swaps values between
neighbors. The mitigation:

- **Step 1 — Sequential transcription.** Read the axis strictly left to right;
  write one literal line per bar (axis label + the callout its leader line points
  to + bar color) before tabulating anything.
- **Step 2 — Trace the leader line, don't read top-down.** The number nearest a
  bar often belongs to its neighbor; follow the line, not proximity.
- **Step 3 — Re-read the axis for every chart.** Never carry bar order across
  charts; bind every value to a category name, never to "the third bar."
- **Step 4 — Cross-check tallest/shortest** bars against their labels/values.
- **Step 5 — Consolidated Markdown table output**, then map to the schema.
- Flag any unclear label or number as `Visual Ambiguity` (or `null` + a note) —
  a flagged gap is recoverable; a confident wrong number is not.

Operational mapping rules (so text and chart extraction agree):
- **Effectiveness direction** from dot color: green = positive, yellow = neutral,
  red = negative (per the plot legend).
- **Statistical significance:** `significant` if the report says so or the CI
  excludes 0; `not_significant` if the CI includes 0; else `not_reported`.
- **ESSA tier:** Level I/II/III/IV → 1/2/3/4; keep the literal label too.

Extraction prompts live in `shared/prompts/` (`rce_extraction_SKILL.md` +
`field_source_map.md`).

---

## Spot-Check / QA Gate (Phase 3 → 4 handoff)

`deliverables/spot_check.html` is a self-contained reviewer page (open in any
browser). It loads an extracted `RCEReport`, shows every value confidence-tiered
(printed-text / chart-read / visual-ambiguity) with a citation to the source
card/chart/page, floats ambiguity flags to the top, and exports a **verified
JSON + review log**. Only verified data should pass this gate into the
leader-facing `artifact.html`. This is where Amanda's QA happens before anything
reaches a school decision-maker.

---

## Pipeline Phases

| Phase | Description | Owner |
|-------|-------------|-------|
| 0 | Orient & align | All |
| 1 | Define scope, variable list, output template | Amanda lead |
| 2 | Tech setup, API keys, Git repo | Kyle lead |
| 3 | PDF → structured data (parsing, extraction, validation, master dataset) | Kyle lead |
| 4 | Synthesis, visualization, integration test | Kyle lead |
| 5 | Interactive HTML output, documentation, QA | All |

**Current status: Phase 2 complete; Phase 3 substantially complete.** The
extraction skill, Pydantic schema, gold fixture, and spot-check QA gate are built
and the ALEKS slice validates end-to-end. Remaining Phase 3 work: validate
against additional reports, finalize the variable codebook with Amanda, and
relocate the assets to their canonical homes. Phase 4 (synthesis into the
leader-facing `artifact.html`) is next.

---

## Key Decisions Made

- **Starting product:** ALEKS (confirmed)
- **Tech stack:** Python only (no R)
- **LLM access:** Claude + Gemini Enterprise (both confirmed)
- **Output format:** Interactive HTML artifact (MVP); extended branches may produce PDF/HTML research brief
- **Scope boundary:** No direct LearnPlatform API integration — work from exported PDFs only

---

## Open Questions

- Final variable codebook pending (Amanda's Google Sheet — request access if needed)
- Schema coverage gap (remaining): `rce_schema.py` does **not** yet model
  cost-effectiveness (optional, district-elected; Amanda wants a scoping chat this
  week) or **per-subgroup usage minutes** (the "Avg Minutes on system" chart value;
  likely a new `SubgroupFinding` field — confirm with Amanda)
- `effect_size_type` field tier: CORE vs EXT (now an enum, currently **EXT**; promote to CORE-when-present?)
- `AnalysisMethod` enum: may need expansion after reviewing more reports (align with r vs g)
- "Are all report fields captured?" — Amanda flagged a field-completeness audit against a full report
- Oluwaseun's gold-standard validation study design: sampling strategy and IRR metric selection TBD

**Resolved**
- ~~Cohen's d / p-values~~ → platform uses **Pearson's r** (correlative) or
  **Hedge's g** (experimental/quasi-experimental); modeled as `effect_size_type`.
  Significance = 95% CI excludes 0 (`confidence_level` field, default 0.95).
- ~~`subgroup_category` free text vs enum~~ → **enum** of 6 fixed categories
  (school, grade_level, ell, gender, race_ethnicity, frl_status) + `custom` with
  `subgroup_category_custom`. None required; only a categorical usage metric is.
- ~~Chart extraction ownership~~ → **Claude is primary**; Gemini Enterprise retained
  in parallel (Amanda) with the spatial-drift protocol as a shared spec, prompt
  tuning ongoing.
- ~~Asset placement~~ → assets stay under `contributors/sherman/` until Amanda
  reviews; canonical homes noted with `→` arrows in Repository Structure.
- ~~Spot-check vs. leader artifact naming~~ → `deliverables/spot_check.html` (QA gate)
  vs. `deliverables/artifact.html` (leader brief).

---

## Notes for Claude Code

- Kyle is the engineering lead — default to Python solutions
- Pydantic v2 syntax only (no v1 compatibility shims)
- All new scripts go in `contributors/sherman/` during development; move to `shared/` or `deliverables/` when ready
- Do not commit data files to the repo — `data/sample_reports/` is gitignored for sensitive content
- Run `pytest shared/tests/` before moving anything to `deliverables/`
- Schema smoke-check before committing schema or fixture changes (current paths;
  update once assets move to `deliverables/` + `data/annotations/`):
  ```bash
  python3 -c "import json,sys; \
  base='contributors/sherman/rce-extraction/references'; sys.path.insert(0,base); \
  from rce_schema import RCEReport; \
  d=json.load(open(base+'/aleks_worked_example.json')); d.pop('_comment',None); \
  print('SCHEMA OK' if RCEReport(**d) else 'FAIL')"
  ```
- `status_report.py` prints a Slack-ready project digest; `--post` sends it if `SLACK_WEBHOOK_URL` is set
- `.DS_Store` is globally gitignored — do not re-add

---

## Glossary

- **RCE** — Rapid Cycle Evaluation (one LearnPlatform report).
- **ESSA tiers** — evidence levels I–IV (Strong / Moderate / Promising / Rationale); ALEKS is Level III, "Promising Evidence."
- **BOY / MOY / EOY** — beginning / middle / end of year testing windows.
- **Subgroups** — Grade, Gender, Ethnicity, School, SpEd Status, Prior Performance.
- **Effect size** — here, a partial correlation (ALEKS overall = +0.20).
- **Usage compliance** — share of students meeting recommended dosage (ALEKS = 27%; a low-usage/high-impact pattern).
