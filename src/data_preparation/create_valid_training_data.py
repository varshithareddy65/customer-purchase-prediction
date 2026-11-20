
import duckdb

con = duckdb.connect()

cart_path = "datasets/synerise_dataset/add_to_cart.parquet"
buy_path = "datasets/synerise_dataset/product_buy.parquet"
input_path = "datasets/enriched_training.parquet"
output_path = "datasets/valid_training.parquet"

query = f"""
COPY (
    WITH endpoints AS (
        SELECT GREATEST(
            (SELECT MAX(CAST(timestamp AS TIMESTAMP))
             FROM read_parquet('{cart_path}')),
            (SELECT MAX(CAST(timestamp AS TIMESTAMP))
             FROM read_parquet('{buy_path}'))
        ) - INTERVAL '24 hours' AS valid_cutoff
    )
    SELECT
        t.client_id,
        t.sku,
        CAST(t.cart_time AS TIMESTAMP) AS cart_time,
        t.category,
        t.price,
        t.purchased_within_24h
    FROM read_parquet('{input_path}') t
    CROSS JOIN endpoints e
    WHERE CAST(t.cart_time AS TIMESTAMP) <= e.valid_cutoff
)
TO '{output_path}'
(FORMAT PARQUET)
"""

con.execute(query)

print("\nCORRECTED TRAINING DATASET")

print(con.execute(f"""
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT client_id) AS unique_customers,
    COUNT(DISTINCT sku) AS unique_products,
    COUNT(*) FILTER (
        WHERE purchased_within_24h = 1
    ) AS positive_rows,
    COUNT(*) FILTER (
        WHERE purchased_within_24h = 0
    ) AS negative_rows,
    ROUND(
        AVG(purchased_within_24h) * 100, 2
    ) AS positive_rate_percent
FROM read_parquet('{output_path}')
""").fetchdf().to_string(index=False))

print("\nSaved:", output_path)

con.close()
