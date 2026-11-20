
import duckdb

con = duckdb.connect()

path = "datasets/valid_training.parquet"

query = f"""
WITH daily AS (
    SELECT
        CAST(cart_time AS DATE) AS event_date,
        COUNT(*) AS daily_events
    FROM read_parquet('{path}')
    GROUP BY CAST(cart_time AS DATE)
),
cumulative AS (
    SELECT
        event_date,
        daily_events,
        SUM(daily_events) OVER (
            ORDER BY event_date
        ) AS cumulative_events,
        SUM(daily_events) OVER () AS total_events
    FROM daily
),
targets AS (
    SELECT *
    FROM (VALUES (0.70), (0.85))
    AS t(target_fraction)
)
SELECT
    target_fraction,
    event_date AS cutoff_date,
    cumulative_events,
    total_events,
    ROUND(
        cumulative_events * 100.0 / total_events, 2
    ) AS cumulative_percent
FROM cumulative
CROSS JOIN targets
WHERE cumulative_events >= total_events * target_fraction
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY target_fraction
    ORDER BY event_date
) = 1
ORDER BY target_fraction
"""

print("\nCHRONOLOGICAL SPLIT BOUNDARIES")
print(con.execute(query).fetchdf().to_string(index=False))

print("\nDAILY DATA COVERAGE")
print(con.execute(f"""
SELECT
    MIN(CAST(cart_time AS DATE)) AS first_date,
    MAX(CAST(cart_time AS DATE)) AS last_date,
    COUNT(DISTINCT CAST(cart_time AS DATE)) AS active_days
FROM read_parquet('{path}')
""").fetchdf().to_string(index=False))

con.close()
