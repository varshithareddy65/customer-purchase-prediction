
import duckdb

con = duckdb.connect()

path = "datasets/enriched_training.parquet"

print("\n1. EXACT DUPLICATE CART EVENTS")

print(con.execute(f"""
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT (client_id, sku, cart_time))
        AS unique_cart_events,
    COUNT(*) - COUNT(DISTINCT (client_id, sku, cart_time))
        AS exact_duplicate_rows
FROM read_parquet('{path}')
""").fetchdf().to_string(index=False))


print("\n2. REPEATED CUSTOMER-PRODUCT PAIRS")

print(con.execute(f"""
WITH pair_counts AS (
    SELECT
        client_id,
        sku,
        COUNT(*) AS cart_events,
        SUM(purchased_within_24h) AS positive_events
    FROM read_parquet('{path}')
    GROUP BY client_id, sku
)
SELECT
    COUNT(*) AS unique_customer_product_pairs,
    COUNT(*) FILTER (
        WHERE cart_events > 1
    ) AS pairs_with_repeated_carts,
    SUM(cart_events) FILTER (
        WHERE cart_events > 1
    ) AS events_in_repeated_pairs,
    MAX(cart_events) AS maximum_events_for_one_pair
FROM pair_counts
""").fetchdf().to_string(index=False))


print("\n3. EXAMPLE REPEATED CUSTOMER-PRODUCT PAIRS")

print(con.execute(f"""
SELECT
    client_id,
    sku,
    COUNT(*) AS cart_events,
    SUM(purchased_within_24h) AS positive_events,
    MIN(cart_time) AS first_cart_time,
    MAX(cart_time) AS last_cart_time
FROM read_parquet('{path}')
GROUP BY client_id, sku
HAVING COUNT(*) > 1
ORDER BY cart_events DESC
LIMIT 10
""").fetchdf().to_string(index=False))

con.close()
