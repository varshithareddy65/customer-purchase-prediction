
import pandas as pd

DATA_DIR = "datasets/synerise_dataset"

files = {
    "search": "search_query.parquet",
    "cart": "add_to_cart.parquet",
    "purchase": "product_buy.parquet"
}

for name, filename in files.items():
    df = pd.read_parquet(
        f"{DATA_DIR}/{filename}",
        columns=["client_id", "timestamp"]
    )

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    print(f"\n{name.upper()} ANALYSIS")
    print("-" * 40)

    print("Total events:", f"{len(df):,}")
    print("Unique customers:", f"{df['client_id'].nunique():,}")
    print("Events per customer:", round(
        len(df) / df["client_id"].nunique(), 2
    ))

    print("Daily event count:")
    print(df.groupby(df["timestamp"].dt.date).size().describe())

    del df
