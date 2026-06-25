# RCE Extraction + Spot-Check (ISEA Hackweek — Phase 3 → 4)

Contributor drop for the "Automating the Meta-Analysis" project. Turns a
LearnPlatform RCE report into reviewed, structured data.

## What's here

```
rce-extraction/                  # A Claude skill: RCE Full Report PDF → structured JSON
├── SKILL.md                     #   workflow + the anti-"spatial-drift" chart protocol
└── references/
    ├── rce_schema.py            #   the RCEReport Pydantic model (extraction target)
    ├── field_source_map.md      #   where each field lives on the page (ALEKS anchor)
    └── aleks_worked_example.json #   a correct, schema-validated ALEKS extraction
ISEA_RCE_SpotCheck.html          # Reviewer QA gate: verify/sign-off + export verified JSON
status_report.py                 # Live project pulse → Slack-ready digest (stdlib only)
CLAUDE.md                        # Context for Claude Code working in this subtree
```

## The pieces, and how they connect

1. **`rce-extraction` skill (Phase 3 — Harvest).** Parses the chart-heavy "View
   Usage & Outcomes" PDF into one `RCEReport` per report. Its core is a
   chart-reading protocol that prevents the documented failure mode: misreading
   bar charts / effect-size dot plots where the same subgroups are reordered
   chart-to-chart and callouts float off their bars ("spatial drift"). Low-
   confidence reads are flagged, not guessed.

2. **`ISEA_RCE_SpotCheck.html` (Phase 3 → 4 handoff).** Open in any browser. Loads
   an extracted record and lets a reviewer verify each value against the source —
   confidence-tiered, with a citation to the source card/chart/page, ambiguity
   flags floated to the top. Exports a verified JSON + review log.

3. **`status_report.py`.** Computes a live status digest (git state, file
   inventory, schema-validation health check, open ambiguity flags) and prints it
   Slack-ready. `python3 status_report.py` to print; set `SLACK_WEBHOOK_URL` and
   add `--post` to push it.

## Quick start

```bash
# validate the worked example against the schema
cd rce-extraction
python3 -c "import json,sys; sys.path.insert(0,'references'); \
from rce_schema import RCEReport; \
d=json.load(open('references/aleks_worked_example.json')); d.pop('_comment',None); \
print('OK' if RCEReport(**d) else 'FAIL')"
```

Then open `ISEA_RCE_SpotCheck.html` to see the reviewer gate (pre-loaded with the
ALEKS slice).

## Status

Draft for group exploration. ALEKS is the live vertical slice; the same pattern
generalizes to Amplify / Lexia / i-Ready as harvesting comes online.
