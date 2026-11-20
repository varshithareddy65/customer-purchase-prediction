
import duckdb

con = duckdb.connect()

query = """
SELECT
    COUNT(*) AS positive_cart_events,
    COUNT(DISTINCT (client_id, sku, cart_time))
        AS unique_positive_events,
    COUNT(DISTINCT (client_id, sku))
        AS unique_customer_product_pairs
FROM read_parquet(
    'datasets/valid_training.parquet'
)
WHERE purchased_within_24h = 1
"""

print("Auditing repeated positive labels...")
print(con.execute(query).fetchdf().to_string(index=False))

con.close()
