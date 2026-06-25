
import re
import glob
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

def generate_effect_size_json(json_path: str, output_img_path: str="effect_sizes.png") -> str:
    """ 
    Parses subgroup outcome data export JSON and saves an effect size scatter plot with CIs.
    Define parameters:
    json_path (str): Path to the input JSON file
    output_img_path (str): Path output rewulting plot saved

    Returns:
    str: path to saved image file.
    """

    # 1. Load and clean data
    df = pd.read_json(json_path).dropna(subset=["Subgroup Category"])
    df = df[df["Correlational Association Outcomes"].notna()]
    
    # 2. Parse ES and CI strings using regex
    def parse_metrics(val):
        es = float(re.search(r"ES:\s*([-\d.]+)", val).group(1))
        lo = float(re.search(r"CI:\s*\(([-\d.]+)", val).group(1))
        hi = float(re.search(r",\s*([-\d.]+)\s*\)", val).group(1))
        return pd.Series({"ES": es, "CI_lo": lo, "CI_hi": hi})
    
    df[["ES", "CI_lo", "CI_hi"]] = df["Correlational Association Outcomes"].apply(parse_metrics)
    tidy = df[["Subgroup Category", "Sample Size (N)", "Statistical Significance", "ES", "CI_lo", "CI_hi"]].reset_index(drop=True)
    
    # 3. Setup Plotting Elements
    color_map = {"Positive": "#4CAF50", "Undetermined": "#FFC107", "Negative": "#F44336"}
    colors = tidy["Statistical Significance"].map(color_map).fillna("#F44336")
    
    fig, ax = plt.subplots(figsize=(13, 8))
    x = range(len(tidy))
    
    # 4. Generate Plot
    ax.scatter(list(x), tidy["ES"], color=colors, s=120, zorder=2, edgecolors="white", linewidths=0.8)
    
    for i, row in tidy.iterrows():
        label = f"ES: {row.ES:.2f}\nCI: ({row.CI_lo:.2f}, {row.CI_hi:.2f})\nn={int(row['Sample Size (N)'])}"
        ax.text(i, row.ES + 0.02, label, ha="left", va="bottom", fontsize=7.5, color="#333333")
        
    ax.margins(x=0.20, y=0.35)  
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_xticks(list(x))
    ax.set_xticklabels(tidy["Subgroup Category"], rotation=25, ha="right", fontsize=9)
    ax.set_ylabel("Effect Size (ES)")
    ax.set_title(
        "Is greater usage of 'ALEKS' related to favorable outcomes\nfor different student groups?",
        fontsize=12, pad=25
    )
    
    # Caption
    ax.text(0.40, -0.2, 'ES = Effect Size, CI = Confidence Interval, n = Sample Size', 
            transform=ax.transAxes, ha='center', va='top', fontsize=10, color='black')
    
    # Legend
    legend_labels = {
        "Positive":     "Green: Students had better learning outcomes",
        "Undetermined": "Yellow: All students had similar learning outcomes",
        "Negative":     "Red: Other students had better learning outcomes",
    }
    legend_elements = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=color_map[sig], markersize=9, label=legend_labels[sig]) 
        for sig in legend_labels
    ]
    ax.legend(handles=legend_elements, loc="center left", bbox_to_anchor=(1.02, 0.5),
              fontsize=8.5, frameon=False, title="Significance", alignment="left")
    
    # 5. Save and Close Context
    plt.tight_layout(rect=[0, 0, 0.78, 1])
    plt.savefig(output_img_path, dpi=150, bbox_inches="tight")
    plt.close(fig)  # Prevents notebook memory leaks
    
    return output_img_path
