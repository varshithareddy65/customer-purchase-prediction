
import duckdb

con = duckdb.connect()

DATA = "datasets/synerise_dataset"

query = f"""
WITH products AS (
    SELECT *
    FROM read_parquet('{DATA}/product_properties.parquet')
),
cart_products AS (
    SELECT DISTINCT sku
    FROM read_parquet('{DATA}/add_to_cart.parquet')
)
SELECT
    COUNT(*) AS total_product_records,
    COUNT(DISTINCT sku) AS unique_skus,
    COUNT(*) - COUNT(DISTINCT sku) AS extra_sku_records,
    COUNT(*) FILTER (WHERE category IS NULL) AS missing_categories,
    COUNT(*) FILTER (WHERE price IS NULL) AS missing_prices
FROM products
"""

print("\nPRODUCT PROPERTY QUALITY")
print(con.execute(query).fetchdf().to_string(index=False))

query = f"""
WITH products AS (
    SELECT DISTINCT sku
    FROM read_parquet('{DATA}/product_properties.parquet')
),
cart_products AS (
    SELECT DISTINCT sku
    FROM read_parquet('{DATA}/add_to_cart.parquet')
)
SELECT COUNT(*) AS cart_skus_without_product_properties
FROM cart_products c
ANTI JOIN products p USING (sku)
"""

print("\nPRODUCT MAPPING CHECK")
print(con.execute(query).fetchdf().to_string(index=False))

con.close()
