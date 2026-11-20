
import os
import json
import gc

import duckdb
import numpy as np
import pandas as pd
import lightgbm as lgb

from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

# --------------------------------------------------
# 1. Configuration
# --------------------------------------------------

DATA_PATH = "datasets/ml_features_purged.parquet"
MODEL_DIR = "models"

os.makedirs(MODEL_DIR, exist_ok=True)

FEATURES = [
    "category",
    "price",
    "hour",
    "day_of_week",
    "day_of_month",
    "month",
    "is_weekend",
    "customer_previous_carts",
    "customer_previous_purchases",
    "product_previous_carts",
    "product_previous_purchases",
    "category_previous_purchases"
]

TARGET = "purchased_within_24h"

con = duckdb.connect()

# Use one consistent set of category levels across splits.
categories = con.execute(f"""
    SELECT DISTINCT category
    FROM read_parquet('{DATA_PATH}')
    ORDER BY category
""").fetchdf()["category"].tolist()

category_dtype = pd.CategoricalDtype(
    categories=categories
)

# --------------------------------------------------
# 2. Load data
# --------------------------------------------------

def load_split(split_name):

    print(f"\nLoading {split_name} data...")

    query = f"""
        SELECT
            {", ".join(FEATURES)},
            {TARGET}
        FROM read_parquet('{DATA_PATH}')
        WHERE data_split = '{split_name}'
    """

    df = con.execute(query).fetchdf()

    # Reduce memory consumption.
    df["category"] = df["category"].astype(
        category_dtype
    )

    for col in [
        "price",
        "customer_previous_carts",
        "customer_previous_purchases",
        "product_previous_carts",
        "product_previous_purchases",
        "category_previous_purchases"
    ]:
        df[col] = df[col].astype("float32")

    for col in [
        "hour",
        "day_of_week",
        "day_of_month",
        "month",
        "is_weekend"
    ]:
        df[col] = df[col].astype("int8")

    X = df[FEATURES]
    y = df[TARGET].astype("int8")

    print("Rows:", len(df))
    print("Purchase rate:", round(y.mean() * 100, 2), "%")

    del df
    gc.collect()

    return X, y


X_train, y_train = load_split("train")
X_val, y_val = load_split("validation")

# --------------------------------------------------
# 3. Build LightGBM model
# --------------------------------------------------

print("\nStarting LightGBM training...")

model = lgb.LGBMClassifier(
    objective="binary",
    boosting_type="gbdt",
    n_estimators=3000,
    learning_rate=0.05,
    num_leaves=31,
    max_depth=-1,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_lambda=1.0,
    random_state=42,
    n_jobs=-1,
    verbosity=-1
)

model.fit(
    X_train,
    y_train,
    eval_set=[(X_val, y_val)],
    eval_metric="auc",
    categorical_feature=["category"],
    callbacks=[
        lgb.early_stopping(100),
        lgb.log_evaluation(100)
    ]
)

print("\nBest iteration:", model.best_iteration_)

# --------------------------------------------------
# 4. Validation evaluation
# --------------------------------------------------

print("\nEvaluating validation data...")

val_prob = model.predict_proba(
    X_val,
    num_iteration=model.best_iteration_
)[:, 1]

val_roc_auc = roc_auc_score(y_val, val_prob)
val_pr_auc = average_precision_score(y_val, val_prob)

precision, recall, thresholds = (
    __import__("sklearn.metrics", fromlist=[
        "precision_recall_curve"
    ]).precision_recall_curve(y_val, val_prob)
)

f1_values = (
    2 * precision[:-1] * recall[:-1]
    / (precision[:-1] + recall[:-1] + 1e-12)
)

best_index = np.argmax(f1_values)
best_threshold = float(thresholds[best_index])

print("\nVALIDATION RESULTS")
print("------------------")
print("ROC-AUC:", round(val_roc_auc, 5))
print("PR-AUC:", round(val_pr_auc, 5))
print("Best F1:", round(float(f1_values[best_index]), 5))
print("Selected threshold:", round(best_threshold, 5))

# --------------------------------------------------
# 5. Final test evaluation
# --------------------------------------------------

del X_train, y_train, X_val
gc.collect()

X_test, y_test = load_split("test")

print("\nEvaluating untouched test data...")

test_prob = model.predict_proba(
    X_test,
    num_iteration=model.best_iteration_
)[:, 1]

test_pred = (
    test_prob >= best_threshold
).astype("int8")

test_roc_auc = roc_auc_score(y_test, test_prob)
test_pr_auc = average_precision_score(y_test, test_prob)

print("\nFINAL TEST RESULTS")
print("------------------")
print("ROC-AUC:", round(test_roc_auc, 5))
print("PR-AUC:", round(test_pr_auc, 5))
print(
    "Precision:",
    round(precision_score(y_test, test_pred), 5)
)
print(
    "Recall:",
    round(recall_score(y_test, test_pred), 5)
)
print(
    "F1:",
    round(f1_score(y_test, test_pred), 5)
)

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, test_pred))

print("\nClassification Report:")
print(classification_report(y_test, test_pred))

# --------------------------------------------------
# 6. Save model and results
# --------------------------------------------------

model_path = os.path.join(
    MODEL_DIR,
    "lightgbm_purchase_model.txt"
)

model.booster_.save_model(model_path)

results = {
    "best_iteration": int(model.best_iteration_),
    "validation_roc_auc": float(val_roc_auc),
    "validation_pr_auc": float(val_pr_auc),
    "selected_threshold": best_threshold,
    "test_roc_auc": float(test_roc_auc),
    "test_pr_auc": float(test_pr_auc),
    "test_precision": float(
        precision_score(y_test, test_pred)
    ),
    "test_recall": float(
        recall_score(y_test, test_pred)
    ),
    "test_f1": float(
        f1_score(y_test, test_pred)
    )
}

with open(
    os.path.join(MODEL_DIR, "training_results.json"),
    "w"
) as f:
    json.dump(results, f, indent=4)

print("\nModel saved:", model_path)
print("Metrics saved: models/training_results.json")

con.close()
