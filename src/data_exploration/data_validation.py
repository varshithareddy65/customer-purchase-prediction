
import os
import pyarrow.parquet as pq
import pandas as pd

DATA_DIR = "datasets/synerise_dataset"

files = [
    "search_query.parquet",
    "add_to_cart.parquet",
    "remove_from_cart.parquet",
    "product_buy.parquet",
    "product_properties.parquet"
]

for filename in files:
    path = os.path.join(DATA_DIR, filename)

    print("\n" + "=" * 65)
    print("FILE:", filename)

    parquet_file = pq.ParquetFile(path)

    print("Total rows:", f"{parquet_file.metadata.num_rows:,}")
    print("Row groups:", parquet_file.num_row_groups)

    columns = parquet_file.schema.names
    print("Columns:", columns)

    # Read only the timestamp column for event files
    if "timestamp" in columns:
        timestamps = []

        for batch in parquet_file.iter_batches(
            batch_size=100000,
            columns=["timestamp"]
        ):
            values = batch.column(0).to_pylist()
            timestamps.extend(v for v in values if v is not None)

        if timestamps:
            print("First timestamp:", min(timestamps))
            print("Last timestamp:", max(timestamps))

    # Check embedding dimensions using sample records
    embedding_column = None

    if "query" in columns:
        embedding_column = "query"
    elif "name" in columns:
        embedding_column = "name"

    if embedding_column:
        table = pq.read_table(
            path,
            columns=[embedding_column]
        ).slice(0, 10)

        for value in table.column(0).to_pylist():
            if value:
                dimensions = len(
                    value.strip("[]").split()
                )
                print("Embedding dimensions:", dimensions)
                break

    print("=" * 65)

print("\nVALIDATION COMPLETED")
