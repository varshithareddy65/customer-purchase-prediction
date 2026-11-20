
import duckdb

con = duckdb.connect()

path = "datasets/enriched_training.parquet"

print("\nPRICE DISTRIBUTION")

print(con.execute(f"""
SELECT
    MIN(price) AS min_price,
    APPROX_QUANTILE(price, 0.25) AS q1,
    APPROX_QUANTILE(price, 0.50) AS median,
    APPROX_QUANTILE(price, 0.75) AS q3,
    APPROX_QUANTILE(price, 0.95) AS q95,
    MAX(price) AS max_price,
    COUNT(*) FILTER (WHERE price = 0) AS zero_price_rows
FROM read_parquet('{path}')
""").fetchdf().to_string(index=False))

print("\nCATEGORY DISTRIBUTION")

print(con.execute(f"""
SELECT
    category,
    COUNT(DISTINCT sku) AS unique_products,
    COUNT(*) AS cart_events
FROM read_parquet('{path}')
GROUP BY category
ORDER BY unique_products DESC
LIMIT 10
""").fetchdf().to_string(index=False))

print("\nSAMPLE RECORDS")

print(con.execute(f"""
SELECT *
FROM read_parquet('{path}')
LIMIT 5
""").fetchdf().to_string(index=False))

con.close()
