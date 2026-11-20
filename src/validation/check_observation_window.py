
import duckdb

con = duckdb.connect()

path = "datasets/cart_purchase_training.parquet"

print("\nOBSERVATION WINDOW")

print(con.execute(f"""
SELECT
    MIN(CAST(cart_time AS TIMESTAMP)) AS first_cart,
    MAX(CAST(cart_time AS TIMESTAMP)) AS last_cart,
    COUNT(*) AS total_events
FROM read_parquet('{path}')
""").fetchdf().to_string(index=False))


print("\nEVENTS IN FINAL 24 HOURS")

print(con.execute(f"""
WITH data AS (
    SELECT
        CAST(cart_time AS TIMESTAMP) AS cart_time,
        purchased_within_24h
    FROM read_parquet('{path}')
),
limits AS (
    SELECT MAX(cart_time) AS last_cart
    FROM data
)
SELECT
    COUNT(*) AS events_in_final_24h,
    COUNT(*) FILTER (
        WHERE purchased_within_24h = 1
    ) AS positive_events,
    COUNT(*) FILTER (
        WHERE purchased_within_24h = 0
    ) AS negative_events
FROM data, limits
WHERE cart_time > last_cart - INTERVAL '24 hours'
""").fetchdf().to_string(index=False))

con.close()
