# Run Final Pipeline (Component 3)

This document defines the exact commands to regenerate final Component 3 artifacts.

## Prerequisites

- Python environment with project dependencies installed.
- From repository root:
  - Ensure `backend/comp3/dataset_cleaned_v2.csv` is present.
  - Ensure `backend/comp3/bert_embeddings_all.npy` is present if BERT features are required.

## 1) Open terminal at comp3 directory

```powershell
cd "C:\Users\shant\OneDrive\Desktop\Research_final\Smart-Criminal-Judgement-Analysis-System\backend\comp3"
```

## 2) Install/verify required packages

```powershell
python -m pip install imbalanced-learn
```

Optional modern model packages:

```powershell
python -m pip install lightgbm catboost
```

## 3) Run feature engineering (leakage-safe)

```powershell
$env:PYTHONIOENCODING="utf-8"
python improved_feature_engineering.py
```

Expected outputs:

- `X_train_improved.csv`
- `X_test_improved.csv`
- `y_train_improved.npy`
- `y_test_improved.npy`
- `improved_tfidf_vectorizer.pkl`
- `improved_scaler.pkl`
- `improved_label_encoder.pkl`
- `improved_selected_features.pkl`
- `improved_feature_metadata.json`

## 4) Run model training/tuning

```powershell
$env:PYTHONIOENCODING="utf-8"
python improved_modeling.py
```

Expected outputs:

- `improved_ensemble_model.pkl`
- `improved_model_metadata.json`
- `improved_confusion_matrix.png`
- `improved_cv_comparison.png`

## 5) Quick sanity check

Confirm model metadata exists and has latest values:

```powershell
python -c "import json; d=json.load(open('improved_model_metadata.json')); print({k:d.get(k) for k in ['test_accuracy','test_f1_score','test_macro_f1_score','test_balanced_accuracy','test_brier_score','overfitting_gap','partly_allowed_threshold']})"
```

## 6) Backend API alignment check

Make sure these files are in sync with latest artifacts:

- `backend/comp3/api/config.py`
- `backend/comp3/src/core/models.py`
- `backend/comp3/api/services/prediction_service.py`
- `backend/comp3/api/models/schemas.py`
- `backend/comp3/api/models/enhanced_schemas.py`

## 7) Final run log capture (recommended)

Save console outputs from both scripts in your report appendix:

- Feature engineering run log
- Modeling run log

This helps viva/review reproducibility.
