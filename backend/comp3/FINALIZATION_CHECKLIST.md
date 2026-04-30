# Component 3 Finalization Checklist

Use this checklist to lock the final research + project state for Appeal Outcome Prediction.

## 1) Scope Freeze

- [ ] Finalize project claim: decision-support only (not autonomous legal decision making).
- [ ] Freeze target variable definition (`outcome_clean` classes).
- [ ] Freeze final split/evaluation policy.

## 2) Data and Leakage Controls

- [ ] Confirm dataset version used: `dataset_cleaned_v2.csv`.
- [ ] Confirm leakage-forbidden columns remain excluded in preprocessing.
- [ ] Confirm only approved pre-appeal text columns are used in feature generation.
- [ ] Confirm duplicate-case handling strategy is documented.

## 3) Reproducibility

- [ ] Run feature engineering from script (not ad-hoc notebook cells).
- [ ] Run modeling from script (not ad-hoc notebook cells).
- [ ] Save all generated artifacts:
  - [ ] `X_train_improved.csv`
  - [ ] `X_test_improved.csv`
  - [ ] `y_train_improved.npy`
  - [ ] `y_test_improved.npy`
  - [ ] `improved_tfidf_vectorizer.pkl`
  - [ ] `improved_scaler.pkl`
  - [ ] `improved_label_encoder.pkl`
  - [ ] `improved_selected_features.pkl`
  - [ ] `improved_ensemble_model.pkl`
  - [ ] `improved_feature_metadata.json`
  - [ ] `improved_model_metadata.json`
- [ ] Confirm `improved_model_metadata.json` includes tuning and threshold fields.

## 4) Safety and Usability

- [ ] Confirm API includes:
  - [ ] `confidence_band`
  - [ ] `manual_review_required`
  - [ ] `reliability_note`
  - [ ] `abstained`
  - [ ] `review_priority`
- [ ] Confirm abstention and manual-review policy is described in report/demo.

## 5) Final Metrics Package

- [ ] Capture final metrics from latest run:
  - [ ] Accuracy
  - [ ] Weighted F1
  - [ ] Macro F1
  - [ ] Balanced Accuracy
  - [ ] Brier Score
  - [ ] Overfitting Gap
  - [ ] Per-class recall (especially `Partly_Allowed`)
- [ ] Export confusion matrix figure.
- [ ] Export CV comparison figure.

## 6) Report and Viva Readiness

- [ ] Include leakage-control paragraph in methodology.
- [ ] Include model limitations section.
- [ ] Include ethical/safety statement (human-in-the-loop).
- [ ] Include future work with concrete next steps.

## 7) Final Freeze

- [ ] Stop changing modeling logic after final metrics are accepted.
- [ ] Keep one final experiment notebook for evidence.
- [ ] Keep scripts as source of truth for reproducible backend behavior.
