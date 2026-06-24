#!/usr/bin/env python3
"""
extract_rce.py
==============
Extract RCEReport JSON from ALEKS LearnPlatform dashboard PDFs via Claude Vision.

Each PDF is a pure-image export (dashboard screenshots); there is no text layer.
This script renders each page to JPEG, batches all images into a single Claude
API call, and validates the response against the RCEReport Pydantic schema.

Usage
-----
# All 5 ALEKS files as one logical report:
.venv/bin/python3 contributors/sherman/extract_rce.py \
    "data/sample_reports/ALEKS 1.pdf" \
    "data/sample_reports/ALEKS 2.pdf" \
    "data/sample_reports/ALEKS 3.pdf" \
    "data/sample_reports/ALEKS 4.pdf" \
    "data/sample_reports/ALEKS 5.pdf"

# Custom output path:
... --output data/annotations/aleks_extracted.json

# Skip schema validation (useful for debugging raw LLM output):
... --no-validate
"""

import argparse
import base64
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pdfplumber
from dotenv import load_dotenv
from PIL import Image

load_dotenv()  # loads ANTHROPIC_API_KEY from .env if present

# ── Paths ──────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_PATH = REPO_ROOT / "shared/prompts/SKILL.md"
FIELD_MAP_PATH = REPO_ROOT / "shared/prompts/field_source_map.md"

sys.path.insert(0, str(REPO_ROOT / "deliverables"))
from rce_schema import RCEReport  # noqa: E402 (must be after sys.path insert)

# ── Image extraction ───────────────────────────────────────────────────────────

MAX_WIDTH = 1568  # px — Claude's recommended max for legible high-res images


def page_to_jpeg_bytes(pdf_path: str, page_num: int) -> bytes:
    """Return JPEG bytes for one PDF page, resized to MAX_WIDTH if wider."""
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num]
        if not page.images:
            raise ValueError(f"No embedded image on page {page_num + 1} of {pdf_path}")

        raw = page.images[0]["stream"].get_data()
        img = Image.open(io.BytesIO(raw))

        if img.width > MAX_WIDTH:
            ratio = MAX_WIDTH / img.width
            img = img.resize((MAX_WIDTH, int(img.height * ratio)), Image.LANCZOS)

        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=85)
        return buf.getvalue()


# ── Prompt construction ────────────────────────────────────────────────────────

def build_prompt(pdf_paths: list) -> str:
    skill = SKILL_PATH.read_text()
    field_map = FIELD_MAP_PATH.read_text()
    filenames = [Path(p).name for p in pdf_paths]
    file_list = "\n".join(f"  - {f}" for f in filenames)

    return f"""You are extracting structured data from LearnPlatform ALEKS dashboard PDF exports.

## Extraction Skill
{skill}

## Field Source Map
{field_map}

## Your Task

The images above are all pages from these {len(pdf_paths)} PDF file(s), treated as one logical report:
{file_list}

These are dashboard screenshots of the same ALEKS report with different subgroup toggles active:
- File 1 is the primary file; extract all header-level fields from it.
- Files 2–5 each show a different subgroup toggle (Grade Level, Gender, Ethnicity, School, SpEd Status).
- Merge all subgroup findings into a single `subgroup_findings` list.

Return a single JSON object conforming to the RCEReport schema. Set META fields:
- source_filename: "{filenames[0]}"
- extraction_model: "claude-sonnet-4-6"
- extraction_timestamp: "PIPELINE_TIMESTAMP"  (the pipeline will replace this)
- extraction_schema_version: "0.1"

Two fields that are commonly missed — include both:
- report_title: the full title as it appears in the dashboard header (e.g. "ALEKS Usage & Outcomes Analysis — BOY-MOY 2025-26, <district>"). Do NOT omit this field.
- overall_statistical_significance: the significance of the primary finding ("significant" / "not_significant" / "not_reported"). The field is named overall_statistical_significance — do NOT shorten it to statistical_significance.

Return ONLY valid JSON — no markdown fences, no explanation, no comments."""


# ── Extraction ─────────────────────────────────────────────────────────────────

def extract(pdf_paths: list, model: str = "claude-sonnet-4-6") -> dict:
    """Send all PDF pages to Claude Vision and return the parsed JSON dict."""
    import anthropic
    client = anthropic.Anthropic()

    content = []

    for pdf_path in pdf_paths:
        filename = Path(pdf_path).name
        with pdfplumber.open(pdf_path) as pdf:
            num_pages = len(pdf.pages)

        content.append({"type": "text", "text": f"--- {filename} ({num_pages} pages) ---"})

        for page_num in range(num_pages):
            jpeg = page_to_jpeg_bytes(pdf_path, page_num)
            b64 = base64.standard_b64encode(jpeg).decode()
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": b64},
            })
            content.append({"type": "text", "text": f"(Page {page_num + 1} of {filename})"})

    content.append({"type": "text", "text": build_prompt(pdf_paths)})

    print(f"  Sending {sum(1 for c in content if c['type'] == 'image')} images to {model}...")
    response = client.messages.create(
        model=model,
        max_tokens=8192,
        messages=[{"role": "user", "content": content}],
    )

    raw = response.content[0].text.strip()

    # Strip markdown code fences if the model wraps the JSON
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0].strip()

    return json.loads(raw)


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Extract RCEReport JSON from ALEKS dashboard PDFs via Claude Vision"
    )
    parser.add_argument("pdfs", nargs="+", help="PDF paths (treated as one logical report)")
    parser.add_argument(
        "--output", "-o",
        default="data/annotations/aleks_extracted.json",
        help="Output JSON path (default: data/annotations/aleks_extracted.json)",
    )
    parser.add_argument("--model", default="claude-sonnet-4-6", help="Claude model to use")
    parser.add_argument("--no-validate", action="store_true", help="Skip Pydantic validation")
    args = parser.parse_args()

    print(f"Processing {len(args.pdfs)} PDF(s)...")
    for p in args.pdfs:
        print(f"  {p}")

    result = extract(args.pdfs, model=args.model)

    result["extraction_timestamp"] = datetime.now(timezone.utc).isoformat()

    if not args.no_validate:
        try:
            report = RCEReport(**result)
            print("Schema validation: OK")
            result = json.loads(report.model_dump_json())
        except Exception as e:
            print(f"Schema validation FAILED: {e}", file=sys.stderr)
            print("Writing raw output anyway (run with --no-validate to suppress this warning).")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"Written to {out_path}")


if __name__ == "__main__":
    main()
