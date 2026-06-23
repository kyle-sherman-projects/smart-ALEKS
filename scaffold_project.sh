#!/bin/bash
# scaffold_project.sh
# Run from: ~/Documents/ISEA/cohort-2026/projects/meta-analysis-automation
# Or set PROJECT_ROOT below

PROJECT_ROOT="${1:-$(pwd)}"

dirs=(
    "contributors/sherman"
    "contributors/oluwaseun"
    "contributors/annia"
    "data/sample_reports"
    "data/annotations"
    "deliverables"
    "shared/prompts"
    "shared/utils"
    "shared/tests"
    "docs"
)

for dir in "${dirs[@]}"; do
    mkdir -p "$PROJECT_ROOT/$dir"
    echo "Created: $dir"
done

# Add .gitkeep to empty dirs so they appear in git
empty_dirs=(
    "contributors/sherman"
    "contributors/oluwaseun"
    "contributors/annia"
    "data/sample_reports"
    "data/annotations"
    "shared/prompts"
    "shared/utils"
    "shared/tests"
)

for dir in "${empty_dirs[@]}"; do
    touch "$PROJECT_ROOT/$dir/.gitkeep"
done

echo "\nScaffold complete. Don't forget to copy README.md, rce_schema.py, and Day2_WorkingDoc.docx into the right spots."
