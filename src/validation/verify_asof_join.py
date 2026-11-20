
import duckdb

con = duckdb.connect()

query = """
WITH carts AS (
    SELECT DISTINCT
        client_id,
        sku,
        CAST(timestamp AS TIMESTAMP) AS cart_time
    FROM read_parquet(
        'datasets/synerise_dataset/add_to_cart.parquet'
    )
    LIMIT 1000
),
purchases AS (
    SELECT
        client_id,
        sku,
        CAST(timestamp AS TIMESTAMP) AS purchase_time
    FROM read_parquet(
        'datasets/synerise_dataset/product_buy.parquet'
    )
),
asof_result AS (
    SELECT
        c.client_id,
        c.sku,
        c.cart_time,
        p.purchase_time AS asof_purchase
    FROM carts c
    ASOF LEFT JOIN purchases p
        ON c.client_id = p.client_id
        AND c.sku = p.sku
        AND c.cart_time <= p.purchase_time
),
expected AS (
    SELECT
        c.client_id,
        c.sku,
        c.cart_time,
        (
            SELECT MIN(p.purchase_time)
            FROM purchases p
            WHERE p.client_id = c.client_id
              AND p.sku = c.sku
              AND p.purchase_time >= c.cart_time
        ) AS expected_purchase
    FROM carts c
)
SELECT
    COUNT(*) AS checked_cart_events,
    COUNT(*) FILTER (
        WHERE a.asof_purchase IS NOT DISTINCT FROM
              e.expected_purchase
    ) AS matching_results,
    COUNT(*) FILTER (
        WHERE a.asof_purchase IS DISTINCT FROM
              e.expected_purchase
    ) AS mismatched_results
FROM asof_result a
JOIN expected e
USING (client_id, sku, cart_time)
"""

print("Verifying ASOF JOIN...")
print(con.execute(query).fetchdf().to_string(index=False))

con.close()
