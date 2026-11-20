
import duckdb

con = duckdb.connect()

cart_path = "datasets/synerise_dataset/add_to_cart.parquet"
buy_path = "datasets/synerise_dataset/product_buy.parquet"
train_path = "datasets/cart_purchase_training.parquet"

query = f"""
WITH endpoints AS (
    SELECT GREATEST(
        (SELECT MAX(CAST(timestamp AS TIMESTAMP))
         FROM read_parquet('{cart_path}')),
        (SELECT MAX(CAST(timestamp AS TIMESTAMP))
         FROM read_parquet('{buy_path}'))
    ) AS observation_end
),
training AS (
    SELECT
        CAST(cart_time AS TIMESTAMP) AS cart_time,
        purchased_within_24h
    FROM read_parquet('{train_path}')
)
SELECT
    e.observation_end,
    e.observation_end - INTERVAL '24 hours'
        AS valid_cutoff,

    COUNT(*) AS original_rows,

    COUNT(*) FILTER (
        WHERE t.cart_time <=
              e.observation_end - INTERVAL '24 hours'
    ) AS valid_rows,

    COUNT(*) FILTER (
        WHERE t.cart_time >
              e.observation_end - INTERVAL '24 hours'
    ) AS excluded_rows,

    COUNT(*) FILTER (
        WHERE t.cart_time <=
              e.observation_end - INTERVAL '24 hours'
          AND t.purchased_within_24h = 1
    ) AS valid_positive_rows,

    COUNT(*) FILTER (
        WHERE t.cart_time <=
              e.observation_end - INTERVAL '24 hours'
          AND t.purchased_within_24h = 0
    ) AS valid_negative_rows

FROM training t
CROSS JOIN endpoints e
GROUP BY e.observation_end
"""

print(con.execute(query).fetchdf().to_string(index=False))

con.close()
