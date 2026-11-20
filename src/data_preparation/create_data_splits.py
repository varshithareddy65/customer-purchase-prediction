
import duckdb

con = duckdb.connect()

input_path = "datasets/valid_training.parquet"
output_path = "datasets/training_with_splits.parquet"

con.execute(f"""
COPY (
    SELECT
        *,
        CASE
            WHEN CAST(cart_time AS DATE)
                <= DATE '2022-10-31'
                THEN 'train'

            WHEN CAST(cart_time AS DATE)
                <= DATE '2022-11-19'
                THEN 'validation'

            ELSE 'test'
        END AS data_split

    FROM read_parquet('{input_path}')
)
TO '{output_path}'
(FORMAT PARQUET)
""")

print("\nSPLIT SUMMARY")

print(con.execute(f"""
SELECT
    data_split,
    COUNT(*) AS total_events,
    COUNT(DISTINCT client_id) AS unique_customers,
    COUNT(*) FILTER (
        WHERE purchased_within_24h = 1
    ) AS positive_events,
    COUNT(*) FILTER (
        WHERE purchased_within_24h = 0
    ) AS negative_events
FROM read_parquet('{output_path}')
GROUP BY data_split
ORDER BY
    CASE data_split
        WHEN 'train' THEN 1
        WHEN 'validation' THEN 2
        WHEN 'test' THEN 3
    END
""").fetchdf().to_string(index=False))

print("\nSaved:", output_path)

con.close()
