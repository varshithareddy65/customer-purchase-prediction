
import duckdb

con = duckdb.connect()

cart_path = "datasets/time_features.parquet"
purchase_path = "datasets/synerise_dataset/product_buy.parquet"
properties_path = "datasets/synerise_dataset/product_properties.parquet"

output_path = "datasets/product_features_corrected.parquet"

query = f"""
COPY (
    WITH cart_events AS (
        SELECT
            sku,
            CAST(cart_time AS TIMESTAMP) AS event_time,
            COUNT(*) AS cart_count,
            0 AS purchase_count
        FROM read_parquet('{cart_path}')
        GROUP BY sku, event_time
    ),

    purchase_events AS (
        SELECT
            sku,
            CAST(timestamp AS TIMESTAMP) AS event_time,
            0 AS cart_count,
            COUNT(*) AS purchase_count
        FROM read_parquet('{purchase_path}')
        GROUP BY sku, event_time
    ),

    combined_product_events AS (
        SELECT * FROM cart_events
        UNION ALL
        SELECT * FROM purchase_events
    ),

    product_timeline AS (
        SELECT
            sku,
            event_time,
            SUM(cart_count) AS cart_count,
            SUM(purchase_count) AS purchase_count
        FROM combined_product_events
        GROUP BY sku, event_time
    ),

    product_history AS (
        SELECT
            sku,
            event_time,

            COALESCE(
                SUM(cart_count) OVER (
                    PARTITION BY sku
                    ORDER BY event_time
                    ROWS BETWEEN UNBOUNDED PRECEDING
                    AND 1 PRECEDING
                ), 0
            ) AS product_previous_carts,

            COALESCE(
                SUM(purchase_count) OVER (
                    PARTITION BY sku
                    ORDER BY event_time
                    ROWS BETWEEN UNBOUNDED PRECEDING
                    AND 1 PRECEDING
                ), 0
            ) AS product_previous_purchases

        FROM product_timeline
    ),

    category_purchase_events AS (
        SELECT
            p.category,
            CAST(b.timestamp AS TIMESTAMP) AS event_time,
            COUNT(*) AS purchase_count
        FROM read_parquet('{purchase_path}') b
        INNER JOIN read_parquet('{properties_path}') p
            ON b.sku = p.sku
        GROUP BY p.category, event_time
    ),

    category_history AS (
        SELECT
            category,
            event_time,

            SUM(purchase_count) OVER (
                PARTITION BY category
                ORDER BY event_time
                ROWS BETWEEN UNBOUNDED PRECEDING
                AND CURRENT ROW
            ) AS category_previous_purchases

        FROM category_purchase_events
    ),

    cart_with_product AS (
        SELECT
            t.*,
            COALESCE(ph.product_previous_carts, 0)
                AS product_previous_carts,
            COALESCE(ph.product_previous_purchases, 0)
                AS product_previous_purchases

        FROM read_parquet('{cart_path}') t

        LEFT JOIN product_history ph
            ON t.sku = ph.sku
            AND CAST(t.cart_time AS TIMESTAMP) = ph.event_time
    )

    SELECT
        cp.*,
        COALESCE(ch.category_previous_purchases, 0)
            AS category_previous_purchases

    FROM cart_with_product cp

    ASOF LEFT JOIN category_history ch
        ON cp.category = ch.category
        AND CAST(cp.cart_time AS TIMESTAMP) > ch.event_time

)
TO '{output_path}'
(FORMAT PARQUET)
"""

print("Recalculating product and category history...")
con.execute(query)

print("\nCORRECTED FEATURE SUMMARY")

print(con.execute(f"""
SELECT
    COUNT(*) AS total_rows,

    AVG(product_previous_carts)
        AS avg_previous_product_carts,

    AVG(product_previous_purchases)
        AS avg_previous_product_purchases,

    AVG(category_previous_purchases)
        AS avg_previous_category_purchases,

    COUNT(*) FILTER (
        WHERE category_previous_purchases > 0
    ) AS rows_with_category_history,

    MAX(category_previous_purchases)
        AS max_category_previous_purchases

FROM read_parquet('{output_path}')
""").fetchdf().to_string(index=False))

print("\nSAMPLE RECORDS")

print(con.execute(f"""
SELECT
    sku,
    category,
    cart_time,
    product_previous_carts,
    product_previous_purchases,
    category_previous_purchases
FROM read_parquet('{output_path}')
LIMIT 10
""").fetchdf().to_string(index=False))

print("\nSaved:", output_path)

con.close()
