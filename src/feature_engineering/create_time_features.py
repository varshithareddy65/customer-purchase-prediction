
import duckdb

con = duckdb.connect()

input_path = "datasets/training_with_splits.parquet"
output_path = "datasets/time_features.parquet"

con.execute(f"""
COPY (
    SELECT
        client_id,
        sku,
        cart_time,
        category,
        price,
        purchased_within_24h,
        data_split,

        EXTRACT(HOUR FROM cart_time)::INTEGER
            AS hour,

        EXTRACT(ISODOW FROM cart_time)::INTEGER
            AS day_of_week,

        EXTRACT(DAY FROM cart_time)::INTEGER
            AS day_of_month,

        EXTRACT(MONTH FROM cart_time)::INTEGER
            AS month,

        CASE
            WHEN EXTRACT(ISODOW FROM cart_time) IN (6, 7)
            THEN 1
            ELSE 0
        END AS is_weekend

    FROM read_parquet('{input_path}')
)
TO '{output_path}'
(FORMAT PARQUET)
""")

print("\nTIME FEATURES CREATED")

print(con.execute(f"""
SELECT
    COUNT(*) AS total_rows,
    MIN(hour) AS minimum_hour,
    MAX(hour) AS maximum_hour,
    COUNT(DISTINCT day_of_week) AS weekdays_present,
    COUNT(*) FILTER (
        WHERE is_weekend = 1
    ) AS weekend_events
FROM read_parquet('{output_path}')
""").fetchdf().to_string(index=False))

print("\nSAMPLE FEATURES")

print(con.execute(f"""
SELECT *
FROM read_parquet('{output_path}')
LIMIT 5
""").fetchdf().to_string(index=False))

print("\nSaved:", output_path)

con.close()
