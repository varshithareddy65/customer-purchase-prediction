
import duckdb
import pandas as pd
import numpy as np
import lightgbm as lgb

from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix
)

DATA = "datasets/ml_features_purged.parquet"

FEATURES = [
    "category", "price", "hour", "day_of_week",
    "day_of_month", "month", "is_weekend",
    "customer_previous_carts",
    "customer_previous_purchases",
    "product_previous_carts",
    "product_previous_purchases",
    "category_previous_purchases"
]

con = duckdb.connect()

categories = con.execute(f"""
    SELECT DISTINCT category
    FROM read_parquet('{DATA}')
    ORDER BY category
""").fetchdf()["category"].tolist()

df = con.execute(f"""
    SELECT {", ".join(FEATURES)},
           purchased_within_24h
    FROM read_parquet('{DATA}')
    WHERE data_split = 'test'
""").fetchdf()

con.close()

df["category"] = pd.Categorical(
    df["category"],
    categories=categories
)

model = lgb.Booster(
    model_file="models/lightgbm_purchase_model.txt"
)

prob = model.predict(
    df[FEATURES],
    num_iteration=model.best_iteration
)

df["probability"] = prob

df["segment"] = np.where(
    df["customer_previous_purchases"] > 0,
    "Returning customers",
    "No previous purchases"
)

df["threshold"] = np.where(
    df["segment"] == "Returning customers",
    0.28317,
    0.16682
)

df["prediction"] = (
    df["probability"] >= df["threshold"]
).astype(int)

print("\nFINAL TEST RESULTS BY CUSTOMER SEGMENT")

for segment, group in df.groupby("segment"):

    y = group["purchased_within_24h"]
    pred = group["prediction"]
    scores = group["probability"]

    print(f"\n{segment}")
    print("Rows:", len(group))
    print("ROC-AUC:", round(roc_auc_score(y, scores), 5))
    print("PR-AUC:", round(average_precision_score(y, scores), 5))
    print("Precision:", round(precision_score(y, pred), 5))
    print("Recall:", round(recall_score(y, pred), 5))
    print("F1:", round(f1_score(y, pred), 5))
    print("Confusion matrix:")
    print(confusion_matrix(y, pred))

print("\nSegment-specific test evaluation completed.")
