
import duckdb

con = duckdb.connect()

base = "datasets/time_features.parquet"
features = "datasets/rolling_demand_features.parquet"

query = f"""
WITH feature_stats AS (
    SELECT
        COUNT(*) AS total_rows,

        COUNT(DISTINCT (
            client_id, sku, cart_time
        )) AS unique_events,

        COUNT(*) FILTER (
            WHERE product_carts_7d < 0
               OR product_carts_30d < 0
               OR product_purchases_7d < 0
               OR product_purchases_30d < 0
               OR category_purchases_7d < 0
               OR category_purchases_30d < 0
        ) AS negative_count_rows,

        COUNT(*) FILTER (
            WHERE product_carts_7d > product_carts_30d
        ) AS invalid_product_cart_windows,

        COUNT(*) FILTER (
            WHERE product_purchases_7d >
                  product_purchases_30d
        ) AS invalid_product_purchase_windows,

        COUNT(*) FILTER (
            WHERE category_purchases_7d >
                  category_purchases_30d
        ) AS invalid_category_windows,

        COUNT(*) FILTER (
            WHERE customer_purchase_recency_days < 0
               OR product_purchase_recency_days < 0
        ) AS negative_recency_rows,

        COUNT(*) FILTER (
            WHERE customer_purchase_recency_days IS NULL
        ) AS null_customer_recency,

        COUNT(*) FILTER (
            WHERE product_purchase_recency_days IS NULL
        ) AS null_product_recency

    FROM read_parquet('{features}')
),

missing_events AS (
    SELECT COUNT(*) AS missing_feature_events
    FROM read_parquet('{base}') b
    WHERE NOT EXISTS (
        SELECT 1
        FROM read_parquet('{features}') f
        WHERE f.client_id = b.client_id
          AND f.sku = b.sku
          AND f.cart_time = b.cart_time
    )
)

SELECT *
FROM feature_stats
CROSS JOIN missing_events
"""

result = con.execute(query).fetchdf()

print("\nROLLING FEATURE VALIDATION")
print(result.to_string(index=False))

con.close()
