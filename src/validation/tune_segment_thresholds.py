
import duckdb
import pandas as pd
import lightgbm as lgb
import numpy as np

from sklearn.metrics import (
    precision_recall_curve,
    average_precision_score,
    roc_auc_score
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
    WHERE data_split = 'validation'
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

print("\nSEGMENT-SPECIFIC VALIDATION THRESHOLDS")

for segment, group in df.groupby("segment"):

    y = group["purchased_within_24h"].to_numpy()
    scores = group["probability"].to_numpy()

    precision, recall, thresholds = (
        precision_recall_curve(y, scores)
    )

    f1 = (
        2 * precision[:-1] * recall[:-1]
        / (precision[:-1] + recall[:-1] + 1e-12)
    )

    best = np.argmax(f1)
    threshold = thresholds[best]

    print(f"\n{segment}")
    print("Rows:", len(group))
    print("PR-AUC:", round(
        average_precision_score(y, scores), 5
    ))
    print("ROC-AUC:", round(
        roc_auc_score(y, scores), 5
    ))
    print("Best threshold:", round(float(threshold), 5))
    print("Best F1:", round(float(f1[best]), 5))
    print("Precision:", round(float(precision[best]), 5))
    print("Recall:", round(float(recall[best]), 5))
