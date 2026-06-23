# Automating the Meta-Analysis of Distributed Research Reports

## Project Introduction

This project builds a pipeline to automate the extraction and synthesis of individual Rapid Cycle Evaluation (RCE) reports into an interactive district-level research brief. LearnPlatform generates thousands of RCE reports annually across 100+ school districts — but creating a District Research Brief currently requires a researcher to manually extract and synthesize results across dozens of individual reports. This project explores whether AI/ML can close that synthesis gap.

The MVP pipeline covers:
- **PDF Ingestion**: Parsing RCE report PDFs exported from LearnPlatform
- **Data Extraction**: LLM-assisted extraction of structured metrics (effect sizes, student counts, subgroup results) from semi-structured report text
- **Interactive Output**: Rendering extracted data into an interactive HTML research brief artifact

Two experimental branches extend the MVP in different directions (see [Branch Strategy](#branch-strategy) below).

### Project Sponsor

**Organization:** Instructure (via LearnPlatform)  
**Sponsor Contact:** Amanda Cadran

### Collaborators

| Name | Personal Goals | Can Help With | Role |
|------|---------------|---------------|------|
| Kyle Sherman | Build end-to-end extraction pipeline; apply systematic review methods to AI-assisted synthesis | Python engineering, Pydantic schema design, pipeline architecture, Git/GitHub | Data Engineer / AI-Prompt Engineer |
| Oluwaseun Farotimi | Develop gold-standard validation study; apply meta-analytic methods, and support synthesis | Meta-analysis methods, inter-rater reliability, effect size interpretation | Research / Methods Analyst |
| Annia Yoshizumi | Generalist data work; support extraction, synthesis, and edge-case handling | Data processing, exploratory analysis, documentation | Data Analyst / Generalist |
| Amanda Cadran | Stakeholder guidance; domain expertise on RCE report structure and research brief format | LearnPlatform domain knowledge, variable scoping, QA (virtual) | Project Lead / PM / Domain Expert |

---

## Branch Strategy

This project uses three branches to organize work by scope and ambition:

| Branch | Description | Status |
|--------|-------------|--------|
| `main` | **MVP**: LearnPlatform PDF → extraction → interactive HTML artifact | Active |
| `meta-analysis-full` | Full meta-analysis vision: synthesis at scale, anomaly detection, District Research Brief | Experimental |
| `llm-direct` | Ambitious: raw RCE data fed directly to LLM, bypassing LearnPlatform entirely, output to interactive artifact | Experimental |

All three branches share the PDF parsing and extraction foundation built in Phase 3. Experimental branches diverge at the synthesis and output stages.

---

## Data and Methods

### Data

A starter set of de-identified sample RCE reports provided by Instructure/LearnPlatform (ALEKS selected as the single starting product). Reports are PDF documents containing effect sizes, student engagement metrics, subgroup breakdowns, and cost-effectiveness data at the district level. A variable codebook for the ALEKS report metrics is maintained in the team's shared Google Sheet. The focus is on building extraction and synthesis logic using these representative documents — not on direct platform integration.

### Existing Methods

District Research Briefs are currently produced through manual review: a researcher reads individual reports, extracts key metrics by hand, and writes a narrative synthesis. This process does not scale to LearnPlatform's report volume. The broader systematic review literature (Schmidt & Hunter; otto-SR framework) provides methodological grounding for automated evidence synthesis.

### Proposed Methods

- **PDF Parsing**: `pdfplumber` or `PyMuPDF` for text extraction; Tesseract OCR for scanned pages if needed
- **Structured Extraction**: LLM-assisted extraction (Claude / Gemini Enterprise) using a Pydantic v2 schema with CORE/EXT/META field tiers; target variables include effect size, Cohen's d, p-value, n, grade, subject, district, tool category, cost, and engagement metrics
- **Validation**: Manual spot-check of 5–10 reports against extracted output; gold-standard annotation for IRR metrics (Oluwaseun lead)
- **Output (MVP)**: Interactive HTML research brief artifact populated from extracted data
- **Output (`meta-analysis-full`)**: Rendered District Research Brief (PDF or HTML) with narrative synthesis and visualizations — forest plots, trend lines, subgroup bar charts, heatmaps
- **Output (`llm-direct`)**: Interactive HTML artifact generated from raw RCE data fed directly to LLM, without LearnPlatform PDF intermediary

### Tech Stack

- **Language**: Python (primary); R optional for stats/viz
- **LLM APIs**: Claude, Gemini Enterprise
- **Version control**: Git / GitHub

---

## Project Goals and Tasks

### Goals

1. **Phase 0 — Orient & Align**: Review all project materials; scope team roles; establish shared note-keeping
2. **Phase 1 — Define Scope**: Finalize target variable list; draft workplan and milestones; design District Research Brief output template; confirm ALEKS as starting product
3. **Phase 2 — Tech Setup**: Assemble sample PDFs and codebooks; confirm Python stack and API access; stand up shared Git repo
4. **Phase 3 — PDF → Structured Data**: Build parsing, extraction, and automation scripts; validate output against source reports; produce master dataset
5. **Phase 4 — Automation, Synthesis & Visualization**: Build narrative synthesis module; generate charts; refactor code; run end-to-end integration test
6. **Phase 5 — Output**: Render final interactive HTML artifact; write pipeline documentation; QA output

### Tasks

**Phase 0 — Orient & Align** *(All)*
- 0.1 Review all project overview documents — **DONE**
- 0.2 Review sample full RCE report (Amanda lead)
- 0.3 Scope project team roles during standup, ~15 min (All)
- 0.4 Set up shared doc for decisions and meeting notes (Amanda lead)
- 0.5 Group review of expected research brief output, ~45–60 min (Amanda lead)

**Phase 1 — Define Scope** *(All)*
- 1.1 Identify target variables: effect size, Cohen's d, p-value, n, grade, subject, district, tool category, cost, engagement — *Started* (Amanda lead, Oluwaseun backup)
- 1.2 Draft technical/analytical workplan and milestones — *In progress* (All)
- 1.3 Create District Research Brief output template — *In progress* (Amanda lead, Sherman backup)
- 1.4 Select single starting product — **DONE** (ALEKS)

**Phase 2 — Tech Setup** *(All)*
- 2.1 Gather sample RCE PDFs and codebooks — **DONE** (Amanda lead)
- 2.2 Confirm tech stack (Python) — **DONE**
- 2.3 Confirm API access (Claude, Gemini Enterprise) — **DONE**
- 2.4 Set up Claude API key in env variable and test basic call (Oluwaseun lead, Sherman backup) — **DONE**
- 2.5 Stand up shared Git repo; confirm all members can push — *In progress* (Sherman lead, Annia backup) — **DONE**

**Phase 3 — PDF → Structured Data** *(Sherman lead)*
- 3.1 Build PDF-to-text parsing script with pdfplumber/PyMuPDF; handle OCR if needed (Sherman lead, Annia backup)
- 3.2 Design and iterate LLM extraction skill; target variables → structured JSON (Sherman lead, All) — *Started* 
- 3.3 Build extraction automation script: loop over PDFs, call LLM, collect output (Sherman lead, Annia backup) — *Started* 
- 3.4 Run quick LLM extraction trial on one report to test feasibility (Sherman lead, All)
- 3.5 Validate extracted data against source reports; spot-check 5–10; log discrepancies (Amanda lead, Oluwaseun backup)
- 3.6 Aggregate JSON outputs into master CSV/dataframe (Sherman lead, Annia backup)
- 3.7 Handle edge cases and missing data; define NULL rules (Annia lead, Amanda backup)

**Phase 4 — Automation, Synthesis & Visualization** *(Sherman lead)*
- 4.1 Build LLM narrative synthesis module; prompt for executive summary across dataset (Sherman lead, Oluwaseun backup)
- 4.2 Build visualizations: forest plots, trend lines, subgroup charts, heatmaps (Sherman lead, Amanda & Annia backup)
- 4.3 Refactor scripts into clean, modular, documented code with docstrings (Sherman lead, Oluwaseun backup)
- 4.4 Integration test: run Phase 3 + Phase 4 end-to-end; verify output matches template (Sherman lead, All)

**Phase 5 — Output** *(All)*
- 5.1 Render interactive HTML research brief; populate with extracted data and visualizations (All)
- 5.2 Write README; document pipeline, limitations, and next steps (Sherman lead, Amanda backup)
- 5.3 Final QA of output brief: narrative accuracy, chart labels, data sourcing, formatting (Amanda lead, All)

---

## Project Results

*To be completed at end of hackweek (June 26, 2026).*

---

## Repository Structure

```
meta-analysis-automation/
├── contributors/
│   ├── sherman/          # Sherman's scratch notebooks and explorations
│   ├── oluwaseun/        # Oluwaseun's validation study design and IRR work
│   └── annia/            # Annia's data processing and synthesis explorations
├── data/
│   ├── sample_reports/   # De-identified sample RCE PDFs (source data)
│   └── annotations/      # Gold-standard human annotation files
├── deliverables/
│   ├── rce_schema.py     # Pydantic v2 extraction schema (primary artifact)
│   ├── pipeline.ipynb    # End-to-end extraction pipeline notebook
│   └── artifact.html     # Interactive HTML research brief output
├── shared/
│   ├── prompts/          # LLM prompt templates (extraction, synthesis)
│   ├── utils/            # Shared parsing and serialization utilities
│   └── tests/            # pytest unit tests for schema and pipeline
├── docs/
│   └── Day2_WorkingDoc.docx   # Team scoping and decision document
├── .gitignore
├── README.md
├── model-card.md
└── environment.yml
```

---

## Setup

```bash
# Clone the repo
git clone https://github.com/ISEA-Repositories/cohort-2026.git
cd cohort-2026/projects/meta-analysis-automation

# Create environment
conda env create -f environment.yml
conda activate meta-analysis

# Or with pip
pip install -r requirements.txt
```

Key dependencies: `pydantic>=2.0`, `pdfplumber`, `anthropic`, `pytest`, `pandas`, `jupyter`
