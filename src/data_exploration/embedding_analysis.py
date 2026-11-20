
import pandas as pd
import numpy as np
import pyarrow.parquet as pq

DATA_DIR = "datasets/synerise_dataset"

# Load a small sample
search = pd.read_parquet(
    f"{DATA_DIR}/search_query.parquet"
).head(1000)

products = pd.read_parquet(
    f"{DATA_DIR}/product_properties.parquet"
).head(1000)


def parse_embedding(value):
    return np.fromstring(
        value.strip("[]"),
        sep=" ",
        dtype=np.float32
    )


search_vectors = np.vstack(
    search["query"].apply(parse_embedding)
)

product_vectors = np.vstack(
    products["name"].apply(parse_embedding)
)

print("SEARCH EMBEDDINGS")
print("Shape:", search_vectors.shape)
print("Min:", search_vectors.min())
print("Max:", search_vectors.max())
print("Unique values:", len(np.unique(search_vectors)))

print("\nPRODUCT EMBEDDINGS")
print("Shape:", product_vectors.shape)
print("Min:", product_vectors.min())
print("Max:", product_vectors.max())
print("Unique values:", len(np.unique(product_vectors)))

print("\nSEARCH VECTOR EXAMPLE:")
print(search_vectors[0])

print("\nPRODUCT VECTOR EXAMPLE:")
print(product_vectors[0])
