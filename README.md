# Customer Purchase Behaviour Prediction Using Machine Learning

## Project Overview

A machine learning project that predicts whether a customer who adds a product to their shopping cart will purchase it within the next 24 hours.

The project uses the real-world Synerise RecSys 2025 dataset and LightGBM classification models.

## Dataset

The dataset contains:
- Product search events
- Add-to-cart events
- Remove-from-cart events
- Product purchase events
- Product properties
- Page visits

Original datasets are stored in `datasets/synerise_dataset/`.

Processed datasets are stored in `datasets/processed/`.

## Problem Statement

Predict whether a cart event results in a purchase within 24 hours.

- 1: Purchase within 24 hours
- 0: No purchase within 24 hours

## Methodology

1. Data exploration and validation
2. Cart and purchase event matching
3. Classification label generation
4. Customer and product feature engineering
5. Chronological train-validation-test splitting
6. Cross-split leakage prevention
7. Rolling behavioural feature generation
8. LightGBM model training and evaluation

## Chronological Data Split

- Training: June 23 – October 31, 2022
- Validation: November 1 – November 19, 2022
- Testing: November 20 – December 7, 2022

## Feature Engineering

- Previous customer purchases
- Previous customer cart activity
- Previous product cart activity
- Previous product purchases
- Category-level purchase history
- Time-based features
- Rolling 7-day and 30-day behavioural statistics
- Customer and product purchase recency

Historical features use information available before each cart event.

## Machine Learning Models

**LightGBM V1:** Initial model using customer, product, category and time-based features.

**LightGBM V2:** Improved model incorporating additional rolling behavioural features.

## Model Evaluation

Results on the chronological test dataset:

| Metric | V1 | V2 |
|---|---:|---:|
| ROC-AUC | 0.68655 | 0.69706 |
| PR-AUC | 0.40178 | 0.42533 |
| Precision | 0.38628 | 0.40041 |
| Recall | 0.51125 | 0.50384 |
| F1-score | 0.44006 | 0.44621 |

V2 improved ROC-AUC, PR-AUC, precision and F1-score compared with V1.

## Technologies Used

Python, Pandas, NumPy, DuckDB, PyArrow, Scikit-learn and LightGBM.

## Project Structure

- `datasets/` – Original and processed datasets
- `src/` – Exploration, preparation, feature engineering, training and validation scripts
- `models/` – Trained LightGBM models and evaluation results
- `outputs/` – Experiment outputs
- `requirements.txt` – Python dependencies

## Installation

Install the dependencies:

```bash
pip install -r requirements.txt
```

Run scripts from the project root after verifying their configured file paths.

## Key Learning Outcomes

- Large-scale Parquet data processing
- Customer behaviour analysis
- Temporal feature engineering
- Classification modelling
- Data leakage prevention
- Chronological model validation
- LightGBM model evaluation

## Dataset Attribution

Dataset: Synerise RecSys 2025. Refer to the original dataset provider for licensing and usage conditions.