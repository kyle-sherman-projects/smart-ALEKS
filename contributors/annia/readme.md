# ALEKS Effect Size Scatterplot

This project contains a Python script to parse and visualize effect sizes and confidence intervals from ALEKS student subgroup outcome exports. It generates a clean, presentation-ready scatter plot mapping learning outcomes across student groups of interest.

## What does this do
- Automatically parses effect sizes (`ES`) and confidence intervals (`CI`) from JSON format.
- Color-codes subgroups by statistical significance (Positive, Undetermined, Negative).
- Automatically detects the most recent JSON data export in the directory.
- Saves the output as a high-quality PNG image (`effect_sizes.png`).

---

## Prerequisites & Installation

Instead of managing packages inside the script, install the required libraries using `pip`. 

Ensure you have Python installed, then run:

```bash
pip install pandas matplotlib