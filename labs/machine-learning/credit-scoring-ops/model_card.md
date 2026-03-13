# Credit Default Prediction Model

## Model version
1.0

## Date
January 2023

## Model type
Logistic regression with preprocessing pipeline (StandardScaler + OneHotEncoder)

## Training data
Loan applications from Q4 2022.

## Features
- income
- employment_length
- loan_amount
- credit_history_length
- num_open_accounts
- debt_to_income
- age_group
- region

## Target
Binary: defaulted (1) or not (0)

## Reported performance
- Accuracy: 0.87
- AUC: 0.76
- Evaluated on a 20% held-out test set from the training data

## Intended use
Support lending decisions by estimating default probability for new applicants.

## Maintainer
Previous ML engineering team (no longer with the company)
