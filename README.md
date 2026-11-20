# Customer Purchase Behaviour Prediction Using Machine Learning

A machine learning project that predicts whether a customer will purchase a product within 24 hours after adding it to their shopping cart, using real-world e-commerce interaction data and LightGBM.

## 1. Project Overview

Understanding customer purchase behaviour helps e-commerce platforms identify purchase intent and improve decision-making.

This project develops a binary classification model to predict whether a cart addition will result in a purchase within the next 24 hours.

The project uses the **Synerise RecSys 2025 dataset**, which contains real-world customer interaction events, including product searches, cart additions, cart removals, purchases and page visits.

Two LightGBM models were developed and evaluated to study the impact of historical behavioural and rolling-window features on prediction performance.

## 2. Problem Statement

Given a customer-product cart event, predict whether the customer purchases that product within 24 hours.

**Target variable:**
- `1` – Purchase occurs within 24 hours.
- `0` – No purchase occurs within 24 hours.

This is formulated as a binary classification problem.

## 3. Dataset

**Dataset:** Synerise RecSys 2025

The dataset contains the following interaction records:

| Dataset | Description |
|---|---|
| `search_query.parquet` | Customer search events |
| `add_to_cart.parquet` | Product additions to cart |
| `remove_from_cart.parquet` | Product removals from cart |
| `product_buy.parquet` | Product purchase events |
| `product_properties.parquet` | Product attributes |
| `page_visit.parquet` | Customer page visits |

The original Parquet files are stored in `datasets/synerise_dataset/`.

Processed datasets and model-ready features are stored directly in `datasets/`.

**Note:** The original dataset is not included in this GitHub repository because of its large size. Obtain it from the original Synerise RecSys 2025 dataset provider and place the files in the expected directory.

## 4. Data Processing and Preparation

The data processing workflow includes:

1. Exploring and validating customer interaction events.
2. Processing cart addition and purchase records.
3. Matching cart events with subsequent purchases.
4. Generating binary purchase labels using a 24-hour conversion window.
5. Creating the cart-to-purchase training dataset.
6. Enriching records with product properties.
7. Generating customer, product and time-based features.
8. Creating chronological training, validation and test datasets.
9. Preventing purchase leakage across dataset splits.
10. Generating additional historical behavioural features.

The processed training dataset contains millions of customer-product interaction records.

## 5. Chronological Data Splitting

To evaluate the model on future interactions, chronological splitting was used instead of random splitting.

| Dataset | Period |
|---|---|
| Training | June 23 – October 31, 2022 |
| Validation | November 1 – November 19, 2022 |
| Testing | November 20 – December 7, 2022 |

Cross-split purchase leakage was audited and purged to prevent the same purchase from improperly influencing multiple dataset splits.

Historical features were generated using information available before the corresponding cart event.

## 6. Feature Engineering

Behavioural features were created to capture customer and product purchase patterns.

**Customer features**
- Previous customer purchases
- Previous customer cart activity
- Customer purchase recency

**Product features**
- Previous product cart activity
- Previous product purchases
- Product purchase recency

**Category features**
- Category-level purchase history

**Time-based features**
- Hour
- Day of week
- Month

**Rolling behavioural features**
- Product carts over 7 and 30 days
- Product purchases over 7 and 30 days
- Category purchases over 7 and 30 days

These features help the model capture historical purchasing patterns and changes in customer behaviour.

## 7. Machine Learning Models

LightGBM was used for binary classification.

### Model V1 – Baseline Behavioural Model

The first model uses customer, product, category and time-based behavioural features.

- Number of features: 12
- Algorithm: LightGBM Classifier
- Evaluation: Chronological validation and test datasets

### Model V2 – Enhanced Behavioural Model

The second model introduces additional rolling-window behavioural features and historical purchase information.

- Number of features: 20
- Algorithm: LightGBM Classifier
- Evaluation: Same chronological evaluation framework

The objective was to evaluate whether additional behavioural history improves purchase prediction performance.

## 8. Model Evaluation

The following results were obtained on the chronological test dataset.

| Evaluation Metric | Model V1 | Model V2 |
|---|---:|---:|
| ROC-AUC | 0.68655 | **0.69706** |
| PR-AUC | 0.40178 | **0.42533** |
| Precision | 0.38628 | **0.40041** |
| Recall | **0.51125** | 0.50384 |
| F1-score | 0.44006 | **0.44621** |

### Key Observations

- Model V2 improved ROC-AUC from 0.68655 to 0.69706.
- PR-AUC improved from 0.40178 to 0.42533.
- Precision improved from 0.38628 to 0.40041.
- F1-score improved from 0.44006 to 0.44621.
- Recall decreased slightly from 0.51125 to 0.50384.

Overall, Model V2 achieved better ROC-AUC, PR-AUC, precision and F1-score, indicating an improvement from the additional behavioural features.

## 9. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Programming and model development |
| Pandas | Data manipulation |
| NumPy | Numerical operations |
| DuckDB | Large-scale Parquet data processing |
| PyArrow | Parquet data handling |
| Scikit-learn | Model evaluation and preprocessing |
| LightGBM | Gradient boosting classification |

## 10. Project Structure

```text
customer-purchase-prediction/
│
├── datasets/
│   ├── synerise_dataset/
│   │   ├── add_to_cart.parquet
│   │   ├── remove_from_cart.parquet
│   │   ├── product_buy.parquet
│   │   ├── product_properties.parquet
│   │   ├── page_visit.parquet
│   │   └── search_query.parquet
│   │
│   ├── cart_purchase_training.parquet
│   ├── enriched_training.parquet
│   ├── valid_training.parquet
│   ├── training_with_splits.parquet
│   ├── customer_features.parquet
│   ├── product_features.parquet
│   ├── product_features_corrected.parquet
│   ├── time_features.parquet
│   ├── ml_features.parquet
│   ├── ml_features_purged.parquet
│   ├── rolling_demand_features.parquet
│   └── ml_features_v2.parquet
│
├── src/
│   ├── data_exploration/
│   ├── data_preparation/
│   ├── feature_engineering/
│   ├── models/
│   └── validation/
│
├── models/
│   ├── feature_importance.csv
│   ├── permutation_importance_v2.csv
│   ├── training_results.json
│   └── training_results_v2.json
│
├── outputs/
│
├── requirements.txt
├── .gitignore
└── README.md
```

## 11. Installation and Setup

### Prerequisites

- Python 3.10 or later
- pip
- Synerise RecSys 2025 dataset

### Step 1: Clone the repository

```bash
git clone https://github.com/varshithareddy65/customer-purchase-prediction.git

cd customer-purchase-prediction
```

### Step 2: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Add the dataset

Place the original Synerise Parquet files inside:

```text
datasets/synerise_dataset/
```

### Step 4: Run the processing pipeline

The Python scripts are organized into data exploration, data preparation, feature engineering, model training and validation stages.

Run the scripts from the project root after ensuring the required input datasets and preceding processing outputs are available.

### Step 5: Train the models

```bash
python src/models/train_lightgbm.py
```

```bash
python src/models/train_lightgbm_v2.py
```

The training scripts generate model artifacts and evaluation results in the `models/` directory.

**Note:** The trained LightGBM model files are excluded from this GitHub repository because of their size. Run the training scripts to regenerate them.

## 12. Key Learning Outcomes

- Processing large-scale e-commerce interaction datasets.
- Analysing customer purchase behaviour.
- Generating classification labels from event sequences.
- Creating customer and product behavioural features.
- Implementing chronological train-validation-test splitting.
- Identifying and preventing data leakage.
- Engineering rolling-window historical features.
- Training and comparing LightGBM classification models.
- Evaluating models using ROC-AUC, PR-AUC, precision, recall and F1-score.

## 13. Future Improvements

- Experiment with additional behavioural features.
- Explore model calibration and threshold optimization.
- Evaluate alternative classification algorithms.
- Develop a customer purchase prediction interface.
- Investigate recommendation strategies using predicted purchase probabilities.

## 14. Dataset Attribution

**Synerise RecSys 2025**

The dataset is used for machine learning experimentation and customer purchase behaviour analysis. Refer to the original dataset provider for licensing and usage conditions.