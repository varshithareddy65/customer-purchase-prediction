
import duckdb

con = duckdb.connect()

DATA = "datasets/synerise_dataset"

cart = f"'{DATA}/add_to_cart.parquet'"
purchase = f"'{DATA}/product_buy.parquet'"

print("Building purchase prediction dataset...")

query = f"""
COPY (
    WITH carts AS (
        SELECT DISTINCT
            client_id,
            sku,
            CAST(timestamp AS TIMESTAMP) AS cart_time
        FROM read_parquet({cart})
    ),

    purchases AS (
        SELECT
            client_id,
            sku,
            CAST(timestamp AS TIMESTAMP) AS purchase_time
        FROM read_parquet({purchase})
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
    )

    SELECT
        client_id,
        sku,
        cart_time,

        CASE
            WHEN purchase_time IS NOT NULL
            AND purchase_time <=
                cart_time + INTERVAL '24 hours'
            THEN 1
            ELSE 0
        END AS purchased_within_24h,

        CASE
            WHEN purchase_time IS NOT NULL
            THEN DATE_DIFF(
                'second',
                cart_time,
                purchase_time
            )
            ELSE NULL
        END AS seconds_to_next_purchase

    FROM matched

) TO 'datasets/cart_purchase_training.parquet'
(FORMAT PARQUET, COMPRESSION ZSTD)
"""

con.execute(query)

print("\nTraining dataset created!")

result = con.execute("""
SELECT
    COUNT(*) AS total_rows,
    SUM(purchased_within_24h) AS positive_examples,
    COUNT(*) - SUM(purchased_within_24h)
        AS negative_examples
FROM read_parquet(
    'datasets/cart_purchase_training.parquet'
)
""").fetchdf()

print(result.to_string(index=False))

con.close()
