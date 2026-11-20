
import duckdb

con = duckdb.connect()

cart_path = "datasets/time_features.parquet"
purchase_path = "datasets/synerise_dataset/product_buy.parquet"
output_path = "datasets/customer_features.parquet"

query = f"""
COPY (
    WITH cart_history AS (
        SELECT
            client_id,
            CAST(cart_time AS TIMESTAMP) AS event_time,
            COUNT(*) AS cart_count,
            0 AS purchase_count
        FROM read_parquet('{cart_path}')
        GROUP BY client_id, event_time
    ),

    purchase_history AS (
        SELECT
            client_id,
            CAST(timestamp AS TIMESTAMP) AS event_time,
            0 AS cart_count,
            COUNT(*) AS purchase_count
        FROM read_parquet('{purchase_path}')
        GROUP BY client_id, event_time
    ),

    combined_events AS (
        SELECT * FROM cart_history
        UNION ALL
        SELECT * FROM purchase_history
    ),

    timeline AS (
        SELECT
            client_id,
            event_time,
            SUM(cart_count) AS cart_count,
            SUM(purchase_count) AS purchase_count
        FROM combined_events
        GROUP BY client_id, event_time
    ),

    customer_history AS (
        SELECT
            client_id,
            event_time,

            COALESCE(
                SUM(cart_count) OVER (
                    PARTITION BY client_id
                    ORDER BY event_time
                    ROWS BETWEEN UNBOUNDED PRECEDING
                    AND 1 PRECEDING
                ), 0
            ) AS customer_previous_carts,

            COALESCE(
                SUM(purchase_count) OVER (
                    PARTITION BY client_id
                    ORDER BY event_time
                    ROWS BETWEEN UNBOUNDED PRECEDING
                    AND 1 PRECEDING
                ), 0
            ) AS customer_previous_purchases

        FROM timeline
    )

    SELECT
        t.*,
        h.customer_previous_carts,
        h.customer_previous_purchases

    FROM read_parquet('{cart_path}') t

    LEFT JOIN customer_history h
        ON t.client_id = h.client_id
        AND CAST(t.cart_time AS TIMESTAMP) = h.event_time

)
TO '{output_path}'
(FORMAT PARQUET)
"""

print("Calculating customer historical features...")
con.execute(query)

print("\nCUSTOMER FEATURE SUMMARY")

print(con.execute(f"""
SELECT
    COUNT(*) AS total_rows,
    AVG(customer_previous_carts)
        AS avg_previous_carts,
    AVG(customer_previous_purchases)
        AS avg_previous_purchases,
    MAX(customer_previous_carts)
        AS max_previous_carts,
    MAX(customer_previous_purchases)
        AS max_previous_purchases
FROM read_parquet('{output_path}')
""").fetchdf().to_string(index=False))

print("\nSAMPLE RECORDS")

print(con.execute(f"""
SELECT
    client_id,
    cart_time,
    customer_previous_carts,
    customer_previous_purchases
FROM read_parquet('{output_path}')
LIMIT 10
""").fetchdf().to_string(index=False))

print("\nSaved:", output_path)

con.close()
