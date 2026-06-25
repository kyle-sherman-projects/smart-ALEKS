# Automating the Meta-Analysis of Distributed Research Reports

## Project Introduction

This project builds a pipeline to automate the extraction and synthesis of individual Rapid Cycle Evaluation (RCE) reports into an interactive district-level research brief. LearnPlatform generates thousands of RCE reports annually across 100+ school districts — but creating a District Research Brief currently requires a researcher to manually extract and synthesize results across dozens of individual reports. This project explores whether AI/ML can close that synthesis gap.

The MVP pipeline covers:
- **Data Extraction**: Gemini Enterprise extracts structured metrics from chart-heavy RCE PDFs; output is reviewed and exported as an XLSX
- **Format Conversion**: `xlsx_to_rce.py` converts the Gemini XLSX into a schema-validated JSON (`RCEReport`)
- **QA Gate**: `spot_check.html` lets a reviewer confidence-tier every value and flag ambiguities before anything reaches a decision-maker
- **Interactive Output**: `artifact.html` renders the verified data as an interactive HTML research brief

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

| Branch | Description | Status |
|--------|-------------|--------|
| `main` | **MVP**: Gemini XLSX → RCEReport JSON → spot-check QA → interactive HTML artifact | Active |
| `meta-analysis-full` | Full meta-analysis vision: synthesis at scale, anomaly detection, District Research Brief | Experimental |
| `llm-direct` | Ambitious: raw RCE data fed directly to LLM, bypassing LearnPlatform entirely | Experimental |

All branches share the Phase 3 schema and extraction foundation. Experimental branches diverge at the synthesis and output stages.

---

## Data and Methods

### Data

A starter set of de-identified sample RCE reports provided by Instructure/LearnPlatform (ALEKS selected as the single starting product). Reports are PDF documents containing effect sizes, student engagement metrics, subgroup breakdowns, and cost-effectiveness data at the district level. A variable codebook for the ALEKS report metrics is maintained in the team's shared Google Sheet. The focus is on building extraction and synthesis logic using these representative documents — not on direct platform integration.

### Existing Methods

District Research Briefs are currently produced through manual review: a researcher reads individual reports, extracts key metrics by hand, and writes a narrative synthesis. This process does not scale to LearnPlatform's report volume. The broader systematic review literature (Schmidt & Hunter; otto-SR framework) provides methodological grounding for automated evidence synthesis.

### Proposed Methods

**Extraction approach:**

ALEKS RCE PDFs are image-only exports (each page is an embedded JPEG with no text layer). `pdfplumber` text extraction returns nothing useful, and direct LLM vision extraction introduces spatial drift — chart callout labels shift to neighboring bars, silently swapping values. The mitigation is a two-model approach:

- **Gemini Enterprise** (Amanda): primary chart/dot-plot reader; exports verified results as XLSX
- **`xlsx_to_rce.py`**: converts the Gemini XLSX into a `RCEReport` JSON validated against the Pydantic v2 schema
- **Claude** (Kyle): drives narrative synthesis, QA tooling, schema design, and the Phase 4+ artifact

The spatial-drift protocol in `shared/prompts/SKILL.md` documents the sequential transcription rules both models follow when reading bar charts and effect-size dot plots.

**Structured extraction schema:**

`deliverables/rce_schema.py` (Pydantic v2) defines three models — `RCEReport`, `UsageAnalysis`, `SubgroupFinding` — with CORE/EXT/META field tiers. Effect size type is `pearson_r` (partial correlation) for ALEKS; `hedges_g` for experimental reports. Statistical significance is determined by whether the 95% CI excludes zero.

**Validation:**

`deliverables/spot_check.html` is the QA gate: drag-and-drop an `RCEReport` JSON, review every value with its confidence tier and source citation, flag ambiguities, and export a verified JSON + review log. Only verified data passes into `artifact.html`.

**Output (MVP):** Interactive HTML research brief (`artifact.html`) populated from verified extracted data.  
**Output (`meta-analysis-full`):** Rendered District Research Brief with narrative synthesis and visualizations — forest plots, trend lines, subgroup bar charts, heatmaps.  
**Output (`llm-direct`):** Interactive HTML artifact generated from raw RCE data fed directly to LLM.

### Tech Stack

- **Language**: Python (primary)
- **LLM APIs**: Gemini Enterprise (chart extraction), Claude (synthesis, tooling)
- **Key libraries**: `pydantic>=2.0`, `openpyxl`, `anthropic`, `pytest`, `pandas`, `jupyter`
- **Version control**: Git / GitHub

---

## Project Goals and Tasks

### Goals

1. **Phase 0 — Orient & Align**: Review all project materials; scope team roles; establish shared note-keeping
2. **Phase 1 — Define Scope**: Finalize target variable list; draft workplan and milestones; design District Research Brief output template; confirm ALEKS as starting product
3. **Phase 2 — Tech Setup**: Assemble sample PDFs and codebooks; confirm Python stack and API access; stand up shared Git repo
4. **Phase 3 — Extraction → Structured Data**: Build extraction pipeline; validate output against source reports; produce master dataset
5. **Phase 4 — Automation, Synthesis & Visualization**: Build narrative synthesis module; generate charts; run end-to-end integration test
6. **Phase 5 — Output**: Render final interactive HTML artifact; write pipeline documentation; QA output

### Tasks

**Phase 0 — Orient & Align** *(All)* — **DONE**
- 0.1 Review all project overview documents — **DONE**
- 0.2 Review sample full RCE report — **DONE**
- 0.3 Scope project team roles — **DONE**
- 0.4 Set up shared doc for decisions and meeting notes — **DONE**
- 0.5 Group review of expected research brief output — **DONE**

**Phase 1 — Define Scope** *(All)*
- 1.1 Identify target variables: effect size, Pearson's r / Hedge's g, CI, n, grade, subject, district, tool category, engagement — **DONE**
- 1.2 Draft technical/analytical workplan and milestones — **DONE**
- 1.3 Create District Research Brief output template — *In progress* (artifact.html)
- 1.4 Select single starting product — **DONE** (ALEKS)

**Phase 2 — Tech Setup** *(All)* — **DONE**
- 2.1 Gather sample RCE PDFs and codebooks — **DONE**
- 2.2 Confirm tech stack (Python) — **DONE**
- 2.3 Confirm API access (Claude, Gemini Enterprise) — **DONE**
- 2.4 Set up Claude API key in env variable and test basic call — **DONE**
- 2.5 Stand up shared Git repo; confirm all members can push — **DONE**

**Phase 3 — Extraction → Structured Data** *(Sherman lead)*
- 3.1 Determine PDF parsing approach; handle image-only exports — **DONE** *(ALEKS PDFs are image-only; pdfplumber text extraction not viable; Gemini Enterprise handles chart extraction via visual protocol)*
- 3.2 Design and iterate LLM extraction skill; target variables → structured JSON — **DONE** *(SKILL.md + field_source_map.md; spatial-drift protocol; Pydantic v2 schema)*
- 3.3 Build extraction automation: convert Gemini XLSX output to validated RCEReport JSON — **DONE** *(`xlsx_to_rce.py`; 17 subgroup findings; schema validation passes)*
- 3.4 Run LLM extraction trial on one report to test feasibility — **DONE** *(Claude Vision trial confirmed spatial drift; switched to Gemini XLSX pipeline)*
- 3.5 Validate extracted data against source reports; spot-check; log discrepancies — **DONE** *(Gemini vs. Claude comparison completed; spot_check.html QA gate built with drag-and-drop JSON loader)*
- 3.6 Aggregate JSON outputs into master dataset — *In progress* (single report complete; multi-report aggregation pending)
- 3.7 Handle edge cases and missing data; define NULL rules — **DONE** *(CORE/EXT/META tiers; "Not plotted" rows preserved with notes; null handling in schema validator)*

**Phase 4 — Automation, Synthesis & Visualization** *(Sherman lead)*
- 4.1 Build LLM narrative synthesis module — *Not started*
- 4.2 Build visualizations: forest plots, trend lines, subgroup charts — *In progress* (artifact.html scaffolded)
- 4.3 Refactor scripts into clean, modular code — *Not started*
- 4.4 Integration test: run full pipeline end-to-end; verify output matches template — *In progress* (pending artifact.html smoke test with real data)

**Phase 5 — Output** *(All)*
- 5.1 Render interactive HTML research brief; populate with extracted data — *In progress*
- 5.2 Write README; document pipeline, limitations, and next steps — *In progress*
- 5.3 Final QA of output brief: narrative accuracy, chart labels, data sourcing, formatting — *Not started*

---

## Project Results

*To be completed at end of hackweek (June 26, 2026).*

---

## Repository Structure

```
smart-ALEKS/
├── contributors/
│   ├── sherman/
│   │   ├── rce-extraction/
│   │   │   ├── SKILL.md              # Extraction protocol + spatial-drift rules (→ shared/prompts/)
│   │   │   └── references/           # Working copies of schema and fixtures
│   │   ├── extract_rce.py            # PDF → Claude Vision (explored; spatial drift confirmed — not primary path)
│   │   ├── xlsx_to_rce.py            # Gemini XLSX → RCEReport JSON (primary extraction path)
│   │   ├── populate_spot_check.py    # CLI: RCEReport JSON → populated review HTML in data/reviews/
│   │   ├── CLAUDE.md
│   │   └── README.md
│   ├── oluwaseun/                    # Validation study design and IRR work
│   ├── annia/                        # Data processing and exploratory analysis
│   └── amanda/                       # Domain reference materials
├── data/
│   ├── sample_reports/               # De-identified RCE PDFs — gitignored
│   └── annotations/                  # RCEReport JSON files — gitignored
├── deliverables/
│   ├── rce_schema.py                 # Pydantic v2 extraction schema — source of truth
│   ├── spot_check.html               # QA gate: drag-drop JSON → review → export verified JSON
│   ├── artifact.html                 # Leader-facing interactive HTML research brief
│   └── pipeline.ipynb                # End-to-end pipeline notebook
├── shared/
│   ├── prompts/
│   │   ├── SKILL.md                  # Extraction skill + spatial-drift protocol
│   │   └── field_source_map.md       # Maps every schema field to its source in the PDF
│   ├── utils/
│   │   └── status_report.py          # Project status digest; --post sends to Slack
│   └── tests/                        # pytest unit tests
├── docs/
│   └── Day2_WorkingDoc.docx
├── .env.example                      # Template — copy to .env and add your API key
├── .gitignore
├── README.md
├── model-card.md
└── environment.yml
```

---

## Setup

```bash
# Clone the repo
git clone <repo-url>
cd smart-ALEKS

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Install dependencies
.venv/bin/pip install pydantic>=2.0 openpyxl anthropic pdfplumber pandas jupyter pytest python-dotenv pillow

# Configure your API key (never commit .env)
cp .env.example .env
# Edit .env and set: ANTHROPIC_API_KEY=your-key-here
```

---

## Key Commands

**Convert a Gemini XLSX to RCEReport JSON:**
```bash
.venv/bin/python3 contributors/sherman/xlsx_to_rce.py \
    "/path/to/ALEKS - Variable Mapping....xlsx" \
    --product ALEKS \
    --period "08/25/2025 - 02/20/2026" \
    --output data/annotations/aleks_from_gemini.json
```

**Open the QA gate** — drag the JSON onto `deliverables/spot_check.html` in any browser. No server needed.

**Schema smoke-check:**
```bash
python3 -c "
import json, sys
sys.path.insert(0, 'deliverables')
from rce_schema import RCEReport
d = json.load(open('data/annotations/aleks_worked_example.json')); d.pop('_comment', None)
print('SCHEMA OK' if RCEReport(**d) else 'FAIL')
"
```

**Project status digest:**
```bash
python3 shared/utils/status_report.py          # print to terminal
python3 shared/utils/status_report.py --post   # post to Slack (requires SLACK_WEBHOOK_URL)
```

**Run tests:**
```bash
pytest shared/tests/
```
