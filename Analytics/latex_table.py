import pandas as pd

# Load the dataset
file_path = './statistics/batch_data/all_configs.csv'
df = pd.read_csv(file_path)

# Round the 'blocked' column to 4 decimal places
df['blocked'] = df['blocked'].map(lambda x: f"{x:.4f}" if isinstance(x, (int, float)) else x)
df['os_version'] = df['os_version'].map(lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else x)

# Convert to LaTeX table
latex_table = df.to_latex(index=False, escape=True, longtable=True)

with open('latex_table_generated.txt', 'w') as f:
    f.write(latex_table)