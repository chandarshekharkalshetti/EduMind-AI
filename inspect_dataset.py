
import pandas as pd
from pathlib import Path

# Find the dataset in the project's data folder.
DATA_PATH = Path("C:\\Users\\chand\\Downloads\\career_recommender.csv")

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Dataset not found: {DATA_PATH.resolve()}\n"
        "Place career_recommender.csv inside the data folder."
    )

df = pd.read_csv(DATA_PATH)

# Remove accidental spaces from column names.
df.columns = df.columns.str.strip()

job_column = next(
    (
        col for col in df.columns
        if "first Job title" in col
    ),
    None
)

if job_column is None:
    raise ValueError("Could not find the job-title column.")

print("\n========== DATASET OVERVIEW ==========")
print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")

print("\n========== MISSING VALUES ==========")
print(df.isnull().sum().to_string())

# Normalize labels for inspection only.
job_titles = (
    df[job_column]
    .fillna("")
    .astype(str)
    .str.strip()
)

job_titles = job_titles[
    ~job_titles.str.lower().isin(
        ["", "na", "n/a", "none", "nan"]
    )
]

print("\n========== TOP 40 JOB TITLES ==========")
print(job_titles.value_counts().head(40).to_string())

print("\n========== LABEL SUMMARY ==========")
print(f"Rows with usable job titles: {len(job_titles)}")
print(f"Distinct non-empty job titles: {job_titles.nunique()}")

print("\n========== POSSIBLE TARGET LABELS ==========")
keywords = [
    "software", "developer", "programmer", "web",
    "data analyst", "data scientist", "machine learning",
    "artificial intelligence", "tester", "quality assurance"
]

for keyword in keywords:
    matches = job_titles[
        job_titles.str.contains(keyword, case=False, regex=False)
    ]

    print(f"\n{keyword.title()}: {len(matches)} records")
    print(matches.value_counts().head(10).to_string())

print("\nInspection complete. No model was trained.")
