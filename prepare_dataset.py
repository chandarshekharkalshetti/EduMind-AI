
from pathlib import Path

import pandas as pd


# ---------------- CONFIGURATION ----------------

DATA_DIR = Path("data")
INPUT_FILE = DATA_DIR / "career_recommender.csv"
OUTPUT_FILE = DATA_DIR / "career_training_clean.csv"
REPORT_FILE = DATA_DIR / "career_class_counts.csv"


# ---------------- COLUMN NAMES ----------------

JOB_COLUMN = (
    "If yes, then what is/was your first Job title in your "
    "current field of work? If not applicable, write NA."
)

# Only these input columns will be retained.
FEATURE_COLUMNS = [
    "What was your course in UG?",
    "What is your UG specialization? Major Subject (Eg; Mathematics)",
    "What are your interests?",
    "What are your skills ? (Select multiple if necessary)",
    "What was the average CGPA or Percentage obtained in under graduation?",
    "Did you do any certification courses additionally?",
    "If yes, please specify your certificate course title.",
]


# ---------------- STRICT LABEL MAPPING ----------------

# Match only explicit, unambiguous titles.
# Do not automatically map generic Software Engineer or Developer roles.
STRICT_TITLE_MAP = {
    # Python Developer
    "python developer": "Python Developer",

    # Web Developer
    "web developer": "Web Developer",
    "front end developer": "Web Developer",
    "frontend developer": "Web Developer",
    "front-end developer": "Web Developer",
    "back end developer": "Web Developer",
    "backend developer": "Web Developer",
    "back-end developer": "Web Developer",
    "full stack developer": "Web Developer",
    "full-stack developer": "Web Developer",

    # Data Analyst
    "data analyst": "Data Analyst",

    # Data Scientist
    "data scientist": "Data Scientist",

    # AI/ML Engineer
    "machine learning engineer": "AI/ML Engineer",
    "ml engineer": "AI/ML Engineer",
    "artificial intelligence engineer": "AI/ML Engineer",
    "ai engineer": "AI/ML Engineer",

    # Software Tester / QA Engineer
    "software tester": "Software Tester / QA Engineer",
    "qa engineer": "Software Tester / QA Engineer",
    "quality assurance engineer": "Software Tester / QA Engineer",
    "quality assurance tester": "Software Tester / QA Engineer",
    "test automation engineer": "Software Tester / QA Engineer",
}


def normalize_title(title):
    """Normalize case and whitespace without guessing job meaning."""
    if pd.isna(title):
        return ""

    return " ".join(str(title).strip().lower().split())


def main():
    # Validate input.
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {INPUT_FILE.resolve()}\n"
            "Place career_recommender.csv in the data folder."
        )

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_FILE)
    df.columns = df.columns.str.strip()

    # Validate required columns.
    required_columns = [JOB_COLUMN] + FEATURE_COLUMNS
    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing expected dataset columns:\n"
            + "\n".join(missing_columns)
        )

    print("========== ORIGINAL DATASET ==========")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    # Normalize job titles and map only exact title matches.
    df["_normalized_title"] = df[JOB_COLUMN].apply(
        normalize_title
    )

    df["career_label"] = df["_normalized_title"].map(
        STRICT_TITLE_MAP
    )

    # Exclude titles that are not explicitly mapped.
    clean = df[df["career_label"].notna()].copy()

    # Retain only approved features and the target.
    clean = clean[FEATURE_COLUMNS + ["career_label"]].copy()

    # Remove records with no usable feature information.
    feature_columns = FEATURE_COLUMNS

    for column in feature_columns:
        clean[column] = clean[column].fillna("").astype(str).str.strip()

    has_features = clean[feature_columns].apply(
        lambda column: column.ne("")
    ).any(axis=1)

    clean = clean[has_features].copy()

    # Remove duplicate feature/label rows.
    before_deduplication = len(clean)
    clean = clean.drop_duplicates().reset_index(drop=True)
    duplicates_removed = before_deduplication - len(clean)

    # Save cleaned dataset.
    clean.to_csv(OUTPUT_FILE, index=False)

    # Generate class counts, including categories with zero examples.
    categories = [
        "Python Developer",
        "Web Developer",
        "Data Analyst",
        "Data Scientist",
        "AI/ML Engineer",
        "Software Tester / QA Engineer",
    ]

    counts = clean["career_label"].value_counts()

    report = pd.DataFrame({
        "career_label": categories,
        "record_count": [
            int(counts.get(category, 0))
            for category in categories
        ],
    })

    report.to_csv(REPORT_FILE, index=False)

    # Report unmapped titles for transparency.
    unmapped = df.loc[
        df["career_label"].isna(),
        JOB_COLUMN
    ].fillna("").astype(str).str.strip()

    print("\n========== STRICT MAPPING RESULTS ==========")
    print(f"Original rows: {len(df)}")
    print(f"Rows mapped to target careers: {len(df[df['career_label'].notna()])}")
    print(f"Rows excluded by strict mapping: {len(df[df['career_label'].isna()])}")
    print(f"Duplicates removed: {duplicates_removed}")
    print(f"Final training rows: {len(clean)}")

    print("\n========== CAREER CLASS COUNTS ==========")
    print(report.to_string(index=False))

    print("\n========== EXAMPLES OF EXCLUDED TITLES ==========")
    print(unmapped[unmapped.ne("")].value_counts().head(15).to_string())

    print("\n========== OUTPUT FILES ==========")
    print(f"Clean dataset: {OUTPUT_FILE.resolve()}")
    print(f"Class report: {REPORT_FILE.resolve()}")

    if clean.empty:
        print(
            "\nWARNING: No records remain. Do not train a model "
            "until the mapping rules or dataset are reviewed."
        )
    elif (report["record_count"] == 0).any():
        print(
            "\nWARNING: At least one target career has no examples. "
            "A reliable six-class model cannot be trained from "
            "this prepared dataset as it stands."
        )

    print("\nDataset preparation complete. No model was trained.")


if __name__ == "__main__":
    main()
