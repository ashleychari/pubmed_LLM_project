"""Build the evaluation results table from scoring_sheet.csv.

Uses your hand scores (faithful, helpful) where you've filled them in,
and falls back to the draft scores for any row you haven't scored yet.
"""

import pandas as pd

sheet = pd.read_csv("scoring_sheet.csv")

# Prefer your own scores. Use the draft score only where yours is blank.
for col in ["faithful", "helpful"]:
    sheet[col] = pd.to_numeric(sheet[col], errors="coerce")
    n_missing = sheet[col].isna().sum()
    if n_missing:
        print(f"Note: {n_missing} rows have no hand-scored '{col}', so draft scores were used.")
    sheet[col] = sheet[col].fillna(sheet[f"draft_{col}"])

types = ["specific", "broad", "unanswerable"]
rows = {}

for t in types:
    group = sheet[sheet["type"] == t]

    # Hit rate at 5 only applies to questions that have correct papers.
    if t == "unanswerable":
        hit = "n/a"
    else:
        hit = f'{int(group["any_retrieved"].sum())} of {len(group)}'

    rows[t.capitalize()] = {
        "Questions": len(group),
        "Hit rate at 5": hit,
        "Faithful (1 to 3)": f'{group["faithful"].mean():.2f}',
        "Helpful (1 to 3)": f'{group["helpful"].mean():.2f}',
    }

answerable = sheet[sheet["type"] != "unanswerable"]
rows["Overall"] = {
    "Questions": len(sheet),
    "Hit rate at 5": f'{int(answerable["any_retrieved"].sum())} of {len(answerable)}',
    "Faithful (1 to 3)": f'{sheet["faithful"].mean():.2f}',
    "Helpful (1 to 3)": f'{sheet["helpful"].mean():.2f}',
}

# Rows are metrics, columns are question types.
table = pd.DataFrame(rows)
table.index.name = "Metric"

table.to_csv("eval_table.csv")
print(table.to_markdown())

# Extra counts that are useful in the write-up.
print(f'\nCut-off answers: {int(sheet["truncated"].sum())} of {len(sheet)}')
declined = (sheet.loc[sheet["type"] == "unanswerable", "helpful"] == 3).sum()
n_unanswerable = (sheet["type"] == "unanswerable").sum()
print(f"Unanswerable questions declined: {declined} of {n_unanswerable}")
