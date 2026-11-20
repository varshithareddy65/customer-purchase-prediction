
import duckdb

con = duckdb.connect()

print("\nRAW CART DATA")

print(con.execute("""
SELECT
    COUNT(*) AS raw_rows,
    COUNT(DISTINCT (
        client_id,
        sku,
        timestamp
    )) AS unique_cart_events,
    COUNT(*) - COUNT(DISTINCT (
        client_id,
        sku,
        timestamp
    )) AS exact_duplicates
FROM read_parquet(
    'datasets/synerise_dataset/add_to_cart.parquet'
)
""").fetchdf().to_string(index=False))


print("\nTRAINING DATA")

print(con.execute("""
SELECT
    COUNT(*) AS training_rows,
    COUNT(DISTINCT (
        client_id,
        sku,
        cart_time
    )) AS unique_training_events,
    COUNT(*) FILTER (
        WHERE purchased_within_24h = 1
    ) AS positive_rows,
    COUNT(*) FILTER (
        WHERE purchased_within_24h = 0
    ) AS negative_rows
FROM read_parquet(
    'datasets/cart_purchase_training.parquet'
)
""").fetchdf().to_string(index=False))


print("\nTIMESTAMP VALIDATION")

print(con.execute("""
SELECT
    COUNT(*) FILTER (
        WHERE timestamp IS NULL
    ) AS missing_timestamps
FROM read_parquet(
    'datasets/synerise_dataset/add_to_cart.parquet'
)
""").fetchdf().to_string(index=False))

con.close()
