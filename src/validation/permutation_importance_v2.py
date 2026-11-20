
import duckdb
import lightgbm as lgb
import pandas as pd
import numpy as np

from sklearn.metrics import (
    roc_auc_score,
    average_precision_score
)

DATA_PATH = "datasets/ml_features_v2.parquet"
MODEL_PATH = "models/lightgbm_purchase_model_v2.txt"

model = lgb.Booster(model_file=MODEL_PATH)
features = model.feature_name()
target = "purchased_within_24h"

con = duckdb.connect()

categories = con.execute(f"""
    SELECT DISTINCT category
    FROM read_parquet('{DATA_PATH}')
    ORDER BY category
""").fetchdf()["category"].tolist()

query = f"""
    SELECT {", ".join(features)}, {target}
    FROM read_parquet('{DATA_PATH}')
    WHERE data_split = 'validation'
"""

df = con.execute(query).fetchdf()
con.close()

df["category"] = pd.Categorical(
    df["category"],
    categories=categories
)

X = df[features].copy()
y = df[target].astype("int8")

print("Validation rows:", len(X))

baseline_prob = model.predict(X)
baseline_roc = roc_auc_score(y, baseline_prob)
baseline_pr = average_precision_score(y, baseline_prob)

print("\nBaseline ROC-AUC:", round(baseline_roc, 5))
print("Baseline PR-AUC:", round(baseline_pr, 5))

rng = np.random.default_rng(42)
results = []

for feature in features:
    print("\nTesting:", feature)

    shuffled = X.copy()
    permutation = rng.permutation(len(shuffled))

    shuffled[feature] = (
        X[feature].iloc[permutation].reset_index(drop=True)
    )

    if feature == "category":
        shuffled[feature] = pd.Categorical(
            shuffled[feature],
            categories=categories
        )

    predictions = model.predict(shuffled)

    permuted_roc = roc_auc_score(y, predictions)
    permuted_pr = average_precision_score(y, predictions)

    results.append({
        "feature": feature,
        "roc_auc_drop": baseline_roc - permuted_roc,
        "pr_auc_drop": baseline_pr - permuted_pr
    })

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    "pr_auc_drop",
    ascending=False
)

print("\nPERMUTATION IMPORTANCE — V2")
print(results_df.to_string(index=False))

results_df.to_csv(
    "models/permutation_importance_v2.csv",
    index=False
)

print("\nSaved: models/permutation_importance_v2.csv")
