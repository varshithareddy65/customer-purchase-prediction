
import duckdb

con = duckdb.connect()

query = """
SELECT
    t.client_id,
    t.sku,
    t.cart_time,
    p.category,
    p.price,
    t.purchased_within_24h
FROM read_parquet(
    'datasets/cart_purchase_training.parquet'
) AS t
LEFT JOIN read_parquet(
    'datasets/synerise_dataset/product_properties.parquet'
) AS p
ON t.sku = p.sku
"""

result = con.execute(query)

con.execute("""
COPY (
    SELECT * FROM (
        SELECT
            t.client_id,
            t.sku,
            t.cart_time,
            p.category,
            p.price,
            t.purchased_within_24h
        FROM read_parquet(
            'datasets/cart_purchase_training.parquet'
        ) AS t
        LEFT JOIN read_parquet(
            'datasets/synerise_dataset/product_properties.parquet'
        ) AS p
        ON t.sku = p.sku
    )
) TO 'datasets/enriched_training.parquet'
(FORMAT PARQUET)
""")

print("Enriched dataset created successfully!")

print(
    con.execute("""
        SELECT
            COUNT(*) AS total_rows,
            COUNT(*) FILTER (
                WHERE category IS NULL
            ) AS missing_categories,
            COUNT(*) FILTER (
                WHERE price IS NULL
            ) AS missing_prices,
            AVG(price) AS average_price,
            AVG(purchased_within_24h) AS purchase_rate
        FROM read_parquet(
            'datasets/enriched_training.parquet'
        )
    """).fetchdf()
)

con.close()
