
import duckdb

con = duckdb.connect()

source = "datasets/ml_features.parquet"
output = "datasets/ml_features_purged.parquet"

print("Creating leakage-controlled dataset...")

query = f"""
COPY (
    SELECT *
    FROM read_parquet('{source}')
    WHERE
        (
            data_split = 'train'
            AND cart_time < TIMESTAMP '2022-10-31 00:00:00'
        )
        OR
        (
            data_split = 'validation'
            AND cart_time < TIMESTAMP '2022-11-19 00:00:00'
        )
        OR
        data_split = 'test'
) TO '{output}'
(FORMAT PARQUET, COMPRESSION ZSTD)
"""

con.execute(query)

result = con.execute(f"""
SELECT
    data_split,
    COUNT(*) AS total_rows,
    SUM(purchased_within_24h) AS positives,
    COUNT(*) - SUM(purchased_within_24h) AS negatives,
    ROUND(AVG(purchased_within_24h) * 100, 2)
        AS purchase_rate_percent
FROM read_parquet('{output}')
GROUP BY data_split
ORDER BY
    CASE data_split
        WHEN 'train' THEN 1
        WHEN 'validation' THEN 2
        WHEN 'test' THEN 3
    END
""").fetchdf()

print("\nPurged dataset summary:")
print(result.to_string(index=False))

con.close()
print("\nCreated:", output)
