
import os
import pandas as pd

DATA_DIR = "datasets/synerise_dataset"

print("\n========== SYNERISE DATASET INSPECTION ==========\n")

for file in os.listdir(DATA_DIR):

    if file.endswith(".parquet"):

        path = os.path.join(DATA_DIR, file)
        size_mb = os.path.getsize(path) / (1024 * 1024)

        print(f"\nFILE: {file}")
        print(f"SIZE: {size_mb:.2f} MB")

        df = pd.read_parquet(path)

        print(f"ROWS: {len(df):,}")
        print(f"COLUMNS: {list(df.columns)}")
        print("\nDATA TYPES:")
        print(df.dtypes)

        print("\nSAMPLE RECORDS:")
        print(df.head(3).to_string())

        print("-" * 65)

print("\n========== INSPECTION COMPLETED ==========")
