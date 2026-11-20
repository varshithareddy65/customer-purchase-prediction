
import duckdb

con = duckdb.connect()

path = "datasets/ml_features.parquet"

print("\n1. FEATURE DISTRIBUTION BY SPLIT")

print(con.execute(f"""
SELECT
    data_split,
    COUNT(*) AS total_rows,
    ROUND(AVG(purchased_within_24h) * 100, 2)
        AS purchase_rate_percent,

    ROUND(AVG(price), 2) AS avg_price,

    ROUND(AVG(customer_previous_carts), 2)
        AS avg_customer_carts,

    ROUND(AVG(customer_previous_purchases), 2)
        AS avg_customer_purchases,

    ROUND(AVG(product_previous_carts), 2)
        AS avg_product_carts,

    ROUND(AVG(product_previous_purchases), 2)
        AS avg_product_purchases,

    ROUND(AVG(category_previous_purchases), 2)
        AS avg_category_purchases

FROM read_parquet('{path}')
GROUP BY data_split
ORDER BY
    CASE data_split
        WHEN 'train' THEN 1
        WHEN 'validation' THEN 2
        WHEN 'test' THEN 3
    END
""").fetchdf().to_string(index=False))


print("\n2. FEATURE RANGE CHECK")

print(con.execute(f"""
SELECT
    MIN(price) AS min_price,
    MAX(price) AS max_price,

    MIN(hour) AS min_hour,
    MAX(hour) AS max_hour,

    MIN(day_of_week) AS min_weekday,
    MAX(day_of_week) AS max_weekday,

    MIN(customer_previous_carts)
        AS min_customer_carts,

    MIN(product_previous_carts)
        AS min_product_carts,

    MIN(category_previous_purchases)
        AS min_category_purchases

FROM read_parquet('{path}')
""").fetchdf().to_string(index=False))


print("\n3. CATEGORY COVERAGE")

print(con.execute(f"""
SELECT
    COUNT(DISTINCT category) AS unique_categories,
    COUNT(DISTINCT sku) AS unique_products,
    COUNT(DISTINCT client_id) AS unique_customers
FROM read_parquet('{path}')
""").fetchdf().to_string(index=False))

con.close()
