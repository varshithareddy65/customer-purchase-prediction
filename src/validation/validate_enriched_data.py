
import duckdb

con = duckdb.connect()

path = "datasets/enriched_training.parquet"

print("\nDATASET OVERVIEW")

print(con.execute(f"""
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT client_id) AS unique_customers,
    COUNT(DISTINCT sku) AS unique_products,
    COUNT(*) FILTER (WHERE category IS NULL) AS missing_categories,
    COUNT(*) FILTER (WHERE price IS NULL) AS missing_prices,
    MIN(price) AS minimum_price,
    MAX(price) AS maximum_price,
    AVG(price) AS average_price
FROM read_parquet('{path}')
""").fetchdf().to_string(index=False))

print("\nTOP 10 PRODUCT CATEGORIES")

print(con.execute(f"""
SELECT
    category,
    COUNT(*) AS cart_events,
    ROUND(AVG(purchased_within_24h) * 100, 2)
        AS purchase_rate_percent
FROM read_parquet('{path}')
GROUP BY category
ORDER BY cart_events DESC
LIMIT 10
""").fetchdf().to_string(index=False))

con.close()
