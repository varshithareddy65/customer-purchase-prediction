
import duckdb

con = duckdb.connect()

customer_path = "datasets/customer_features.parquet"
product_path = "datasets/product_features_corrected.parquet"
output_path = "datasets/ml_features.parquet"

print("Combining customer and product features...")

con.execute(f"""
COPY (
    SELECT
        c.client_id,
        c.sku,
        c.cart_time,
        c.category,
        c.price,
        c.hour,
        c.day_of_week,
        c.day_of_month,
        c.month,
        c.is_weekend,

        c.customer_previous_carts,
        c.customer_previous_purchases,

        p.product_previous_carts,
        p.product_previous_purchases,
        p.category_previous_purchases,

        c.purchased_within_24h,
        c.data_split

    FROM read_parquet('{customer_path}') c

    INNER JOIN read_parquet('{product_path}') p
        ON c.client_id = p.client_id
        AND c.sku = p.sku
        AND c.cart_time = p.cart_time
)
TO '{output_path}'
(FORMAT PARQUET)
""")

print("\nFINAL ML FEATURE SUMMARY")

print(con.execute(f"""
SELECT
    COUNT(*) AS total_rows,

    COUNT(DISTINCT (client_id, sku, cart_time))
        AS unique_events,

    COUNT(*) FILTER (
        WHERE customer_previous_carts IS NULL
           OR customer_previous_purchases IS NULL
           OR product_previous_carts IS NULL
           OR product_previous_purchases IS NULL
           OR category_previous_purchases IS NULL
    ) AS rows_with_missing_features

FROM read_parquet('{output_path}')
""").fetchdf().to_string(index=False))

print("\nSPLIT COUNTS")

print(con.execute(f"""
SELECT
    data_split,
    COUNT(*) AS rows
FROM read_parquet('{output_path}')
GROUP BY data_split
ORDER BY data_split
""").fetchdf().to_string(index=False))

print("\nSaved:", output_path)

con.close()
