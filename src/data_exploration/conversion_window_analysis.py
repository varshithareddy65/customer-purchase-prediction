
import duckdb

con = duckdb.connect()

DATA = "datasets/synerise_dataset"

purchase = f"'{DATA}/product_buy.parquet'"
cart = f"'{DATA}/add_to_cart.parquet'"

query = f"""
WITH purchases AS (
    SELECT
        client_id,
        sku,
        MIN(CAST(timestamp AS TIMESTAMP)) AS purchase_time
    FROM read_parquet({purchase})
    GROUP BY client_id, sku
),
cart_events AS (
    SELECT
        client_id,
        sku,
        CAST(timestamp AS TIMESTAMP) AS cart_time
    FROM read_parquet({cart})
),
matched AS (
    SELECT
        p.client_id,
        p.sku,
        p.purchase_time,
        c.cart_time,
        DATE_DIFF(
            'second',
            c.cart_time,
            p.purchase_time
        ) AS seconds_before_purchase
    FROM purchases p
    ASOF LEFT JOIN cart_events c
    ON p.client_id = c.client_id
    AND p.sku = c.sku
    AND p.purchase_time >= c.cart_time
)
SELECT
    COUNT(*) AS total_customer_product_purchases,

    COUNT(cart_time) AS purchases_with_prior_cart,

    COUNT(*) FILTER (
        WHERE seconds_before_purchase BETWEEN 0 AND 86400
    ) AS cart_within_1_day,

    COUNT(*) FILTER (
        WHERE seconds_before_purchase BETWEEN 0 AND 604800
    ) AS cart_within_7_days,

    COUNT(*) FILTER (
        WHERE seconds_before_purchase BETWEEN 0 AND 2592000
    ) AS cart_within_30_days,

    ROUND(
        AVG(seconds_before_purchase) / 3600.0,
        2
    ) AS average_hours_before_purchase

FROM matched
"""

result = con.execute(query).fetchdf()

print("\n===== CART TO PURCHASE CONVERSION WINDOWS =====")
print(result.to_string(index=False))

con.close()
