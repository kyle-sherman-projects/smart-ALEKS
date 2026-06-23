# RCE Extraction + Spot-Check (ISEA Hackweek — Phase 3 → 4)

Contributor drop for the "Automating the Meta-Analysis" project. Two pieces that
turn a LearnPlatform RCE report into reviewed, structured data.

## What's here

```
rce-extraction/                 # A Claude skill: RCE Full Report PDF → structured JSON
├── SKILL.md                    #   workflow + the anti-"spatial-drift" chart protocol
└── references/
    ├── rce_schema.py           #   the RCEReport Pydantic model (extraction target)
    ├── field_source_map.md     #   where each field lives on the page (ALEKS anchor)
    └── aleks_worked_example.json#   a correct, schema-validated ALEKS extraction
ISEA_RCE_SpotCheck.html         # Reviewer QA gate: verify/sign-off + export verified JSON
```

## The two pieces, and how they connect

1. **`rce-extraction` skill (Phase 3 — Harvest).** Instructions for parsing the
   chart-heavy "View Usage & Outcomes" PDF export into one `RCEReport` per report.
   Its core is a chart-reading protocol that prevents the documented failure mode:
   misreading bar charts / effect-size dot plots where the same subgroups are
   reordered chart-to-chart and value callouts float off their bars ("spatial
   drift"). Low-confidence reads are flagged rather than guessed.

2. **`ISEA_RCE_SpotCheck.html` (Phase 3 → 4 handoff).** A self-contained page
   (open in any browser) that loads an extracted record and lets a reviewer
   verify each value against the source — confidence-tiered, with a citation to
   the source card/chart/page, ambiguity flags floated to the top. Exports a
   verified JSON + review log: the clean record that should feed the leader view.

## Quick start

- Read `rce-extraction/SKILL.md` first — it explains the source-document anatomy
  and the extraction contract.
- Validate the example against the schema:
  ```bash
  cd rce-extraction
  python3 -c "import json,sys; sys.path.insert(0,'references'); \
  from rce_schema import RCEReport; \
  d=json.load(open('references/aleks_worked_example.json')); d.pop('_comment',None); \
  print('OK' if RCEReport(**d) else 'FAIL')"
  ```
- Open `ISEA_RCE_SpotCheck.html` to see the reviewer gate (pre-loaded with the
  ALEKS slice). Mark fields Verified / Needs-fix, then "Export verified JSON".

## Status

Draft for group exploration. ALEKS is the live vertical slice; the same pattern
generalizes to Amplify / Lexia / i-Ready as harvesting comes online.
