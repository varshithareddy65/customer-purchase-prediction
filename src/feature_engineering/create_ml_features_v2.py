
import duckdb
from pathlib import Path

Path("datasets/duckdb_tmp").mkdir(parents=True, exist_ok=True)

con = duckdb.connect()
con.execute("SET memory_limit='8GB'")
con.execute("SET threads=4")
con.execute("SET temp_directory='datasets/duckdb_tmp'")

base = "datasets/ml_features_purged.parquet"
rolling = "datasets/rolling_demand_features.parquet"
output = "datasets/ml_features_v2.parquet"

features = [
    "product_carts_7d",
    "product_carts_30d",
    "product_purchases_7d",
    "product_purchases_30d",
    "category_purchases_7d",
    "category_purchases_30d",
    "customer_purchase_recency_days",
    "product_purchase_recency_days",
]

columns = ", ".join("r." + f for f in features)

query = f"""
SELECT m.*, {columns}
FROM read_parquet('{base}') AS m
LEFT JOIN read_parquet('{rolling}') AS r
    ON m.client_id = r.client_id
    AND m.sku = r.sku
    AND m.cart_time = r.cart_time
"""

con.execute(
    f"COPY ({query}) TO '{output}' "
    "(FORMAT PARQUET, COMPRESSION ZSTD)"
)

result = con.execute(f"""
SELECT
    COUNT(*),
    COUNT(DISTINCT (client_id, sku, cart_time)),
    COUNT(*) FILTER (
        WHERE product_carts_7d IS NULL
        OR product_carts_30d IS NULL
        OR product_purchases_7d IS NULL
        OR product_purchases_30d IS NULL
        OR category_purchases_7d IS NULL
        OR category_purchases_30d IS NULL
    ),
    COUNT(*) FILTER (WHERE data_split = 'train'),
    COUNT(*) FILTER (WHERE data_split = 'validation'),
    COUNT(*) FILTER (WHERE data_split = 'test')
FROM read_parquet('{output}')
""").fetchone()

names = [
    "total_rows",
    "unique_events",
    "missing_rolling_counts",
    "train_rows",
    "validation_rows",
    "test_rows",
]

print("\nV2 DATASET CREATED")
for name, value in zip(names, result):
    print(f"{name}: {value}")

con.close()
