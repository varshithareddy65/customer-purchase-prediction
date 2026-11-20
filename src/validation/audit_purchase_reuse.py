
import duckdb

con = duckdb.connect()

query = """
WITH carts AS (
    SELECT
        client_id,
        sku,
        cart_time
    FROM read_parquet('datasets/valid_training.parquet')
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
        p.purchase_time
    FROM carts c
    ASOF LEFT JOIN purchases p
        ON c.client_id = p.client_id
        AND c.sku = p.sku
        AND c.cart_time <= p.purchase_time
),
purchase_groups AS (
    SELECT
        client_id,
        sku,
        purchase_time,
        COUNT(*) AS cart_events
    FROM matched
    WHERE purchase_time IS NOT NULL
      AND purchase_time <= cart_time + INTERVAL '24 hours'
    GROUP BY client_id, sku, purchase_time
)
SELECT
    SUM(cart_events) AS matched_positive_cart_events,
    COUNT(*) AS distinct_matched_purchases,
    COUNT(*) FILTER (
        WHERE cart_events > 1
    ) AS purchases_linked_to_multiple_carts,
    MAX(cart_events) AS maximum_carts_per_purchase
FROM purchase_groups
"""

print("Checking whether purchases are reused...")
print(con.execute(query).fetchdf().to_string(index=False))

con.close()
