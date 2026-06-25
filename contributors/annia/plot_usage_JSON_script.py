import glob
import os
import pandas as pd
import matplotlib.pyplot as plt

# 1. Dynamically load and clean the dataset (loads latest usage output file)
json_files = glob.glob("ALEKS Usage Output - By Subgroup - *.json")

if not json_files:
    raise FileNotFoundError("No matching ALEKS usage JSON file found in directory")


# Automatically select the most recently moeified JSON file
file_path = max(json_files, key=os.path.getmtime)
print(f"Loading data from: {file_path}")

# Read JSON file as DataFrame
df = pd.read_json(file_path)

# Drop empty rows and "sources" text rows at the bottom
df_clean = df.dropna(subset=['Population Count (n)', 'Average Usage (Minutes)']).copy()

# Separate the aggregate row from individual subgroups for proper bar chart scaling
df_subgroups = df_clean[df_clean['Subgroup Category'] != 'All Grade 6 Students'].copy()


# 2. PLOT SUMMARY REPORT VISUALS
# PLOT 1: Simple Bar Chart of Sample Size (n) by Subgroup
# Bars are sorted in ascending order for readability
df_n_sorted = df_subgroups.sort_values(by='Population Count (n)', ascending=True)

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.barh(df_n_sorted['Subgroup Category'], df_n_sorted['Population Count (n)'], color='#3498db')
ax.set_title('Population Count (n) by Subgroup', fontsize=14, pad=15)
ax.set_xlabel('Population Count (n)', fontsize=12)
ax.set_ylabel('Subgroup Category', fontsize=12)
ax.grid(axis='x', linestyle='--', alpha=0.7)

# Add values as labels to each subgroup bar
for bar in bars:
    width = bar.get_width()
    ax.text(width + 5, bar.get_y() + bar.get_height()/2, f'{int(width)}', 
            va='center', ha='left', fontsize=10)

plt.tight_layout()
plt.savefig('n_by_subgroup.png', dpi=300)
#plt.show()
plt.close()



# TBD VISUALIZATIONS (PLACEHOLDERS BELOW)
def generate_dosage_plot():
    """ PLOT 2: Met-Dosage (% of 665m Target Met) """
# Generate once calculation logic is confirmed OR values added to summary usage output data
print("Notice: Plot 2 (Met-Dosage) TBD")


def generate_usage_donut_chart():
    """ PLOT 3: Used vs. Not Used Donut Chart """
# Generate once calculation logic is confirmed OR values added to summary usage output data
print("Notice: Plot 3 (Used vs Not Used) TBD")

if __name__ == "__main__":
    generate_dosage_plot()
    generate_usage_donut_chart()


