
import duckdb

con = duckdb.connect()

cart_path = "datasets/synerise_dataset/add_to_cart.parquet"
buy_path = "datasets/synerise_dataset/product_buy.parquet"

query = f"""
WITH carts AS (
    SELECT
        client_id,
        sku,
        CAST(timestamp AS TIMESTAMP) AS cart_time
    FROM read_parquet('{cart_path}')
),
purchases AS (
    SELECT
        client_id,
        sku,
        CAST(timestamp AS TIMESTAMP) AS purchase_time
    FROM read_parquet('{buy_path}')
),
matched AS (
    SELECT
        c.client_id,
        c.sku,
        c.cart_time,
        p.purchase_time
    FROM carts c
    ASOF LEFT JOIN purchases p
        ON c.client_id = p.client_id
        AND c.sku = p.sku
        AND c.cart_time <= p.purchase_time
),
summary AS (
    SELECT
        COUNT(*) AS cart_events,
        COUNT(*) FILTER (
            WHERE purchase_time IS NOT NULL
        ) AS carts_with_future_purchase,
        COUNT(DISTINCT (client_id, sku, purchase_time))
            FILTER (WHERE purchase_time IS NOT NULL)
            AS distinct_matched_purchases,
        COUNT(*) FILTER (
            WHERE purchase_time <= cart_time + INTERVAL '24 hours'
        ) AS carts_within_24h
    FROM matched
)
SELECT * FROM summary
"""

print(con.execute(query).fetchdf().to_string(index=False))

con.close()
