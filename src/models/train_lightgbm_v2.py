
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
    classification_report,
    precision_recall_curve
)

# --------------------------------------------------
# 1. Configuration
# --------------------------------------------------

DATA_PATH = "datasets/ml_features_v2.parquet"
MODEL_DIR = "models"

os.makedirs(MODEL_DIR, exist_ok=True)

FEATURES = [
    # Original 12 features
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
    "category_previous_purchases",

    # New 8 rolling and recency features
    "product_carts_7d",
    "product_carts_30d",
    "product_purchases_7d",
    "product_purchases_30d",
    "category_purchases_7d",
    "category_purchases_30d",
    "customer_purchase_recency_days",
    "product_purchase_recency_days"
]

TARGET = "purchased_within_24h"

con = duckdb.connect()

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

    df["category"] = df["category"].astype(
        category_dtype
    )

    numeric_features = [
        feature for feature in FEATURES
        if feature != "category"
    ]

    for col in numeric_features:
        df[col] = df[col].astype("float32")

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

print("\nStarting LightGBM V2 training...")

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

precision, recall, thresholds = precision_recall_curve(
    y_val, val_prob
)

f1_values = (
    2 * precision[:-1] * recall[:-1]
    / (precision[:-1] + recall[:-1] + 1e-12)
)

best_index = np.argmax(f1_values)
best_threshold = float(thresholds[best_index])

print("\nV2 VALIDATION RESULTS")
print("---------------------")
print("ROC-AUC:", round(val_roc_auc, 5))
print("PR-AUC:", round(val_pr_auc, 5))
print("Best F1:", round(float(f1_values[best_index]), 5))
print("Selected threshold:", round(best_threshold, 5))

# --------------------------------------------------
# 5. Final test evaluation
# --------------------------------------------------

del X_train, y_train, X_val, y_val
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

test_precision = precision_score(y_test, test_pred)
test_recall = recall_score(y_test, test_pred)
test_f1 = f1_score(y_test, test_pred)

print("\nV2 FINAL TEST RESULTS")
print("---------------------")
print("ROC-AUC:", round(test_roc_auc, 5))
print("PR-AUC:", round(test_pr_auc, 5))
print("Precision:", round(test_precision, 5))
print("Recall:", round(test_recall, 5))
print("F1:", round(test_f1, 5))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, test_pred))

print("\nClassification Report:")
print(classification_report(y_test, test_pred))

# --------------------------------------------------
# 6. Save V2 model and results
# --------------------------------------------------

model_path = os.path.join(
    MODEL_DIR,
    "lightgbm_purchase_model_v2.txt"
)

model.booster_.save_model(model_path)

results = {
    "model_version": "V2",
    "feature_count": len(FEATURES),
    "features": FEATURES,
    "best_iteration": int(model.best_iteration_),
    "validation_roc_auc": float(val_roc_auc),
    "validation_pr_auc": float(val_pr_auc),
    "selected_threshold": best_threshold,
    "test_roc_auc": float(test_roc_auc),
    "test_pr_auc": float(test_pr_auc),
    "test_precision": float(test_precision),
    "test_recall": float(test_recall),
    "test_f1": float(test_f1)
}

with open(
    os.path.join(MODEL_DIR, "training_results_v2.json"),
    "w"
) as f:
    json.dump(results, f, indent=4)

print("\nV2 model saved:", model_path)
print("V2 metrics saved: models/training_results_v2.json")

con.close()
