
import duckdb
import pandas as pd
import lightgbm as lgb

from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score
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

categories = con.execute(
    f"SELECT DISTINCT category FROM read_parquet('{DATA}') ORDER BY category"
).fetchdf()["category"].tolist()

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

probabilities = model.predict(
    df[FEATURES],
    num_iteration=model.best_iteration
)

df["probability"] = probabilities
df["prediction"] = (
    df["probability"] >= 0.24409
).astype(int)

df["customer_segment"] = (
    df["customer_previous_purchases"]
    .gt(0)
    .map({
        True: "Returning customers",
        False: "No previous purchases"
    })
)

print("\nCUSTOMER SEGMENT EVALUATION")

for segment, group in df.groupby("customer_segment"):

    y = group["purchased_within_24h"]
    pred = group["prediction"]
    prob = group["probability"]

    print(f"\n{segment}")
    print("Rows:", len(group))
    print("Purchase rate:", round(y.mean() * 100, 2), "%")
    print("ROC-AUC:", round(roc_auc_score(y, prob), 5))
    print("PR-AUC:", round(average_precision_score(y, prob), 5))
    print("Precision:", round(precision_score(y, pred, zero_division=0), 5))
    print("Recall:", round(recall_score(y, pred, zero_division=0), 5))
    print("F1:", round(f1_score(y, pred, zero_division=0), 5))
