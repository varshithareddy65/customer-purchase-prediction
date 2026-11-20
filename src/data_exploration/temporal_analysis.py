
import duckdb

con = duckdb.connect()

DATA = "datasets/synerise_dataset"

search = f"'{DATA}/search_query.parquet'"
cart = f"'{DATA}/add_to_cart.parquet'"
purchase = f"'{DATA}/product_buy.parquet'"

print("\n===== TEMPORAL CUSTOMER JOURNEY =====")

# First purchase timestamp for each customer
# Check whether a search occurred before that purchase.

query = f"""
WITH first_purchase AS (
    SELECT
        client_id,
        MIN(CAST(timestamp AS TIMESTAMP)) AS purchase_time
    FROM read_parquet({purchase})
    GROUP BY client_id
),
search_events AS (
    SELECT
        client_id,
        CAST(timestamp AS TIMESTAMP) AS search_time
    FROM read_parquet({search})
)
SELECT
    COUNT(*) AS purchasers,
    COUNT(s.search_time) AS customers_with_prior_search
FROM first_purchase p
ASOF LEFT JOIN search_events s
ON p.client_id = s.client_id
AND p.purchase_time >= s.search_time
"""

result = con.execute(query).fetchdf()
print("\nSearch before first purchase:")
print(result.to_string(index=False))


# Match cart additions and purchases by
# the same customer and the same product.

query = f"""
WITH first_purchase AS (
    SELECT
        client_id,
        sku,
        MIN(CAST(timestamp AS TIMESTAMP)) AS purchase_time
    FROM read_parquet({purchase})
    GROUP BY client_id, sku
),
cart_events AS (
    SELECT
        client_id,
        sku,
        CAST(timestamp AS TIMESTAMP) AS cart_time
    FROM read_parquet({cart})
)
SELECT
    COUNT(*) AS customer_product_purchases,
    COUNT(c.cart_time) AS purchases_with_prior_cart
FROM first_purchase p
ASOF LEFT JOIN cart_events c
ON p.client_id = c.client_id
AND p.sku = c.sku
AND p.purchase_time >= c.cart_time
"""

result = con.execute(query).fetchdf()
print("\nCart before purchase for same SKU:")
print(result.to_string(index=False))

con.close()
