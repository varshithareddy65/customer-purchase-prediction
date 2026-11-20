
import duckdb

con = duckdb.connect()

query = """
WITH carts AS (
    SELECT
        client_id,
        sku,
        cart_time,
        data_split
    FROM read_parquet('datasets/ml_features.parquet')
    WHERE purchased_within_24h = 1
),
purchases AS (
    SELECT DISTINCT
        client_id,
        sku,
        CAST(timestamp AS TIMESTAMP) AS purchase_time
    FROM read_parquet(
        'datasets/synerise_dataset/product_buy.parquet'
    )
),
matched AS (
    SELECT
        c.client_id,
        c.sku,
        c.cart_time,
        c.data_split,
        p.purchase_time
    FROM carts c
    ASOF LEFT JOIN purchases p
        ON c.client_id = p.client_id
        AND c.sku = p.sku
        AND c.cart_time <= p.purchase_time
),
purchase_splits AS (
    SELECT
        client_id,
        sku,
        purchase_time,
        STRING_AGG(DISTINCT data_split, ', '
                   ORDER BY data_split) AS splits,
        COUNT(DISTINCT data_split) AS split_count
    FROM matched
    WHERE purchase_time IS NOT NULL
      AND purchase_time <= cart_time + INTERVAL '24 hours'
    GROUP BY client_id, sku, purchase_time
)
SELECT
    splits,
    COUNT(*) AS shared_purchases
FROM purchase_splits
WHERE split_count > 1
GROUP BY splits
ORDER BY shared_purchases DESC
"""

print("Cross-split purchase breakdown:")
print(con.execute(query).fetchdf().to_string(index=False))

con.close()
