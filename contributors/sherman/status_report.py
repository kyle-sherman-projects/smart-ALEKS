#!/usr/bin/env python3
"""
status_report.py — ISEA RCE Extraction project pulse.

Computes a live status digest from the repo (git state + file inventory +
a schema-validation health check + open ambiguity flags) and prints it as
Slack-ready text. Copy/paste it into Slack, or set SLACK_WEBHOOK_URL to post.

Usage:
    python3 status_report.py              # print digest to stdout
    python3 status_report.py --post       # also POST to $SLACK_WEBHOOK_URL
    python3 status_report.py --plain      # no Slack markup (terminal reading)

Stdlib only. Run it from anywhere; paths resolve relative to this file.
"""

from __future__ import annotations
import argparse, json, os, subprocess, sys, datetime, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ── Editable narrative ────────────────────────────────────────────────────────
# The dynamic facts below are computed; this is the one part you maintain by hand.
PHASES = [
    ("Harvest (Phase 3)", "done",     "rce-extraction skill + schema; ALEKS slice validated"),
    ("Spot-check gate",    "done",     "reviewer QA artifact exports verified JSON"),
    ("Synthesize (Phase 4)","wip",     "leader-view demo exists; wire verified JSON into it next"),
    ("Detect (anomalies)", "todo",     "cross-product outlier flagging — not started"),
    ("Generalize",         "todo",     "extend beyond ALEKS to Amplify / Lexia / i-Ready"),
]
STATUS_ICON = {"done": "✅", "wip": "🟡", "todo": "⬜"}

EXPECTED = [
    "rce-extraction/SKILL.md",
    "rce-extraction/references/rce_schema.py",
    "rce-extraction/references/field_source_map.md",
    "rce-extraction/references/aleks_worked_example.json",
    "spot_check.html",
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def sh(args: list[str]) -> str | None:
    try:
        return subprocess.run(args, cwd=HERE, capture_output=True, text=True,
                              timeout=10).stdout.strip() or None
    except Exception:
        return None

def git_state() -> dict:
    if sh(["git", "rev-parse", "--is-inside-work-tree"]) != "true":
        return {"available": False}
    week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    return {
        "available": True,
        "branch": sh(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
        "last": sh(["git", "log", "-1", "--format=%h · %s · %cr"]),
        "commits_7d": sh(["git", "rev-list", "--count", f"--since={week_ago}", "HEAD"]) or "0",
        "dirty": bool(sh(["git", "status", "--porcelain"])),
        "recent": (sh(["git", "log", "-5", "--format=%h %s"]) or "").splitlines(),
    }

def inventory() -> list[tuple[str, bool]]:
    return [(rel, (HERE / rel).exists()) for rel in EXPECTED]

def schema_health() -> tuple[str, dict]:
    """Validate the worked example against RCEReport; count subgroups + flags."""
    ex = HERE / "rce-extraction/references/aleks_worked_example.json"
    if not ex.exists():
        return ("missing", {})
    data = json.loads(ex.read_text())
    data.pop("_comment", None)
    subs = data.get("subgroup_findings") or []
    flags = sum(1 for s in subs
                if (s.get("notes") or "").lower().startswith("visual ambiguity")
                or s.get("effectiveness") == "not_reported")
    counts = {"subgroups": len(subs), "open_flags": flags,
              "effect_size": data.get("effect_size_value"),
              "n": data.get("sample_size_max")}
    schema_dir = str(HERE / "rce-extraction/references")
    try:
        sys.path.insert(0, schema_dir)
        from rce_schema import RCEReport  # type: ignore
        RCEReport(**data)
        return ("pass", counts)
    except ImportError:
        return ("skipped", counts)   # pydantic not installed
    except Exception as e:
        counts["error"] = str(e).splitlines()[0][:140]
        return ("fail", counts)

# ── Rendering ─────────────────────────────────────────────────────────────────
def render(plain: bool) -> str:
    b  = (lambda s: s) if plain else (lambda s: f"*{s}*")
    code = (lambda s: s) if plain else (lambda s: f"`{s}`")
    today = datetime.date.today().strftime("%a %b %-d, %Y")
    g = git_state()
    health, c = schema_health()
    inv = inventory()

    L = []
    L.append(b(f"ISEA · RCE Extraction — status {today}"))
    L.append("")

    L.append(b("Pipeline"))
    for name, st, note in PHASES:
        L.append(f"{STATUS_ICON[st]} {name} — {note}")
    L.append("")

    L.append(b("Health check"))
    hmark = {"pass":"✅ schema valid", "fail":"❌ schema INVALID",
             "skipped":"⚠️ schema check skipped (no pydantic)",
             "missing":"❓ example not found"}[health]
    L.append(f"{hmark}")
    if c:
        es, n = c.get("effect_size"), c.get("n")
        L.append(f"ALEKS slice: effect size {es}, n={n}, "
                 f"{c.get('subgroups',0)} subgroup rows, "
                 f"{code(str(c.get('open_flags',0)) + ' open ambiguity flag(s)')}")
        if health == "fail" and c.get("error"):
            L.append(f"   error: {c['error']}")
    L.append("")

    present = sum(1 for _, ok in inv if ok)
    L.append(b(f"Files ({present}/{len(inv)} present)"))
    for rel, ok in inv:
        L.append(f"{'✓' if ok else '✗'} {rel}")
    L.append("")

    L.append(b("Repo"))
    if g.get("available"):
        L.append(f"branch {code(g['branch'])} · {g['commits_7d']} commit(s) in last 7d"
                 f"{' · uncommitted changes' if g['dirty'] else ' · clean'}")
        if g.get("last"):
            L.append(f"latest: {g['last']}")
    else:
        L.append("_not a git checkout (run from inside the repo for commit info)_")

    return "\n".join(L)

def post_to_slack(text: str) -> None:
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        print("\n[!] SLACK_WEBHOOK_URL not set — printed above, nothing posted.",
              file=sys.stderr)
        return
    req = urllib.request.Request(
        url, data=json.dumps({"text": text}).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            print(f"\n[✓] Posted to Slack (HTTP {r.status}).", file=sys.stderr)
    except Exception as e:
        print(f"\n[x] Slack post failed: {e}", file=sys.stderr)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="ISEA RCE Extraction status digest.")
    ap.add_argument("--post", action="store_true", help="POST to $SLACK_WEBHOOK_URL")
    ap.add_argument("--plain", action="store_true", help="plain text (no Slack markup)")
    a = ap.parse_args()
    text = render(plain=a.plain)
    print(text)
    if a.post:
        post_to_slack(text)
