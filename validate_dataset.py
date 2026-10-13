
from pathlib import Path

import pandas as pd

DATA_FILE = Path("data/career_training_clean.csv")
TARGET = "career_label"
MINIMUM_EXAMPLES = 10


def main():
    if not DATA_FILE.exists():
        print("ERROR: Clean dataset not found.")
        print("Run: py prepare_dataset.py")
        return

    df = pd.read_csv(DATA_FILE)

    if TARGET not in df.columns:
        print(f"ERROR: Missing target column: {TARGET}")
        return

    if df.empty:
        print("ERROR: Dataset is empty.")
        return

    df = df.dropna(subset=[TARGET])
    df = df.drop_duplicates()

    print("=" * 45)
    print("EDUMIND AI - DATASET VALIDATION")
    print("=" * 45)
    print(f"Total records: {len(df)}")
    print(f"Total columns: {len(df.columns)}")

    print("\nCareer distribution:")
    counts = df[TARGET].value_counts()

    for career, count in counts.items():
        status = "OK" if count >= MINIMUM_EXAMPLES else "TOO FEW"
        print(f"{career}: {count} records [{status}]")

    feature_columns = [
        column for column in df.columns if column != TARGET
    ]

    missing = df[feature_columns].isna().sum().sum()
    print(f"\nMissing feature values: {missing}")

    if counts.min() < MINIMUM_EXAMPLES:
        print("\nWARNING:")
        print(
            "The dataset is too small or imbalanced "
            "for reliable six-career ML classification."
        )
        print(
            "Use the existing rule-based recommender "
            "for the working application."
        )
    else:
        print("\nAll career classes meet the minimum count.")
        print("This does not guarantee model quality.")

    print("\nDataset validation complete.")


if __name__ == "__main__":
    main()
