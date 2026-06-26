# smart-ALEKS

Automates the extraction and synthesis of LearnPlatform Rapid Cycle Evaluation (RCE) reports into a district-facing Research Brief. The starting product is ALEKS.

LearnPlatform generates chart-heavy PDF dashboards for each RCE — one per district/product/period. This project builds a pipeline so that a researcher (Amanda) can go from those PDFs to a finished Google Doc Research Brief with AI assistance, without manual re-entry of data.

**View the pipeline:** open [`deliverables/pipeline_flowchart.html`](deliverables/pipeline_flowchart.html) in any browser.

---

## Pipeline Overview

```
Raw district data
  → P1 structures RCE file → P2 uploads to LearnPlatform → RCE Dashboard PDFs
  → P2 + Gemini Enterprise extracts XLSX → P2 QA loop (vs. source PDFs)
  → Verified XLSX → Amanda + Agent 2 build Client-Specific Agent
  → Client-Specific Agent + prior Research Briefs → Research Brief (Google Doc)
```

**Why Gemini:** ALEKS PDFs are image-only exports (no text layer). Claude Vision introduced spatial drift errors on bar charts — callout labels shift to neighboring bars, silently swapping values. Gemini Enterprise handles chart extraction reliably.

---

## Project Sponsor and Team

**Organization:** Instructure (via LearnPlatform)
**Sponsor Contact:** Amanda Cadran

| Name | Role |
|------|------|
| Kyle Sherman | Data Engineer / AI-Prompt Engineer |
| Amanda Cadran | Project Lead / Domain Expert / Researcher |
| Oluwaseun Farotimi | Research / Methods Analyst |
| Annia Yoshizumi | Data Analyst / Generalist |

---

## Repository Structure

```
smart-ALEKS/
├── contributors/
│   ├── sherman/          # Working scripts (active development)
│   ├── annia/            # Data processing and analysis
│   ├── oluwaseun/        # Research and methods work
│   └── amanda/           # Domain reference materials
├── data/
│   └── sample_reports/   # De-identified RCE PDFs — gitignored
├── deliverables/
│   └── pipeline_flowchart.html   # Interactive pipeline diagram
├── docs/
│   └── Research_Brief_Agent_Instructions.md  # Agent instruction template
├── shared/
│   └── prompts/
│       ├── SKILL.md              # Gemini extraction skill + spatial-drift protocol
│       └── field_source_map.md   # Maps schema fields to PDF source locations
├── .env.example
├── .gitignore
├── CLAUDE.md
└── README.md
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
.venv/bin/pip install pydantic>=2.0 openpyxl anthropic pandas jupyter pytest python-dotenv

# Configure your API key (never commit .env)
cp .env.example .env
# Edit .env: ANTHROPIC_API_KEY=your-key-here
```

---

## Key Files

| File | Purpose |
|---|---|
| `deliverables/pipeline_flowchart.html` | Interactive diagram of the full pipeline — click any node |
| `docs/Research_Brief_Agent_Instructions.md` | Instruction template for the Client-Specific Agent |
| `shared/prompts/SKILL.md` | Gemini extraction skill and spatial-drift protocol |
| `shared/prompts/field_source_map.md` | Maps every extracted field to its location in the PDF |

---

## Project Results

*To be completed at end of engagement.*
