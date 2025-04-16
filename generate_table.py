import yaml

# Load the YAML content from the file
file_path = '/mnt/data/all_targets.yml'
with open(file_path, 'r') as file:
    data = yaml.safe_load(file)

# Process the data to extract relevant fields
table_rows = []
for entry in data:
    device = entry.get('device', 'N/A')
    os = entry.get('os', 'N/A')
    os_version = entry.get('os_version', 'N/A')
    browser = entry.get('browser', 'N/A')
    browser_version = entry.get('browser_version', 'N/A')
    table_rows.append((device, os, os_version, browser, browser_version))

# Generate LaTeX table rows
latex_rows = "\n".join(
    f"{device} & {os} & {os_version} & {browser} & {browser_version} \\\\ \\hline"
    for device, os, os_version, browser, browser_version in table_rows
)

# Generate LaTeX table using the longtable environment for multipage support
latex_longtable = f"""
\\begin{{longtable}}{{lllll}}
\\toprule
\\textbf{{Device}} & \\textbf{{OS}} & \\textbf{{OS Version}} & \\textbf{{Browser}} & \\textbf{{Browser Version}} \\\\
\\midrule
\\midrule
\\endfirsthead
\\toprule
\\textbf{{Device}} & \\textbf{{OS}} & \\textbf{{OS Version}} & \\textbf{{Browser}} & \\textbf{{Browser Version}} \\\\
\\midrule
\\endhead
\\midrule
\\endfoot
\\bottomrule
\\endlastfoot

{latex_rows}
\\end{{longtable}}
\\end{{document}}
"""

# Save the updated LaTeX content to a file
output_path = "./all_configs.tex"
with open(output_path, "w") as tex_file:
    tex_file.write(latex_longtable)

output_path
