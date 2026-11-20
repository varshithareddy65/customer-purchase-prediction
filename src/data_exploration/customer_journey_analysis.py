
import pandas as pd
import pyarrow.parquet as pq
import os

DATA_DIR = "datasets/synerise_dataset"

def load_ids(filename):
    path = os.path.join(DATA_DIR, filename)
    table = pq.read_table(path, columns=["client_id"])
    return set(table.column("client_id").to_pylist())

print("\n========== CUSTOMER OVERLAP ANALYSIS ==========\n")

search_users = load_ids("search_query.parquet")
cart_users = load_ids("add_to_cart.parquet")
purchase_users = load_ids("product_buy.parquet")

print("Search customers:", f"{len(search_users):,}")
print("Cart customers:", f"{len(cart_users):,}")
print("Purchase customers:", f"{len(purchase_users):,}")

print("\nCUSTOMER OVERLAPS")

print(
    "Search AND purchase:",
    f"{len(search_users & purchase_users):,}"
)

print(
    "Cart AND purchase:",
    f"{len(cart_users & purchase_users):,}"
)

print(
    "Search AND cart:",
    f"{len(search_users & cart_users):,}"
)

print(
    "All three activities:",
    f"{len(search_users & cart_users & purchase_users):,}"
)

print("\nPURCHASE WITHOUT RECORDED SEARCH:")
print(f"{len(purchase_users - search_users):,}")

print("\n========== DAILY DATA QUALITY ==========\n")

for filename in [
    "search_query.parquet",
    "add_to_cart.parquet",
    "product_buy.parquet"
]:
    path = os.path.join(DATA_DIR, filename)

    table = pq.read_table(path, columns=["timestamp"])
    df = table.to_pandas()

    df["timestamp"] = pd.to_datetime(
        df["timestamp"], errors="coerce"
    )

    daily = df.groupby(df["timestamp"].dt.date).size()

    print("\n", filename)
    print("Lowest activity dates:")
    print(daily.nsmallest(5))

    print("Highest activity dates:")
    print(daily.nlargest(5))

print("\nANALYSIS COMPLETED")
