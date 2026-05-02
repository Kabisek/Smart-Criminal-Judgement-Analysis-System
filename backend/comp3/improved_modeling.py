"""
Improved Modeling Pipeline with Regularization and Ensemble Methods
Addresses overfitting issues and improves model performance
"""

import pandas as pd
import numpy as np
import pickle
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Scikit-learn imports
from sklearn.model_selection import StratifiedKFold, cross_val_score, GridSearchCV, train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.svm import SVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    classification_report, 
    confusion_matrix, 
    accuracy_score,
    precision_recall_fscore_support,
    f1_score,
    balanced_accuracy_score,
    make_scorer
)
from imblearn.over_sampling import SMOTE
import matplotlib.pyplot as plt
import seaborn as sns

try:
    from lightgbm import LGBMClassifier
except Exception:
    LGBMClassifier = None

try:
    from catboost import CatBoostClassifier
except Exception:
    CatBoostClassifier = None

def multiclass_brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Compute multiclass Brier score (lower is better)."""
    y_onehot = np.eye(y_prob.shape[1])[y_true]
    return float(np.mean(np.sum((y_prob - y_onehot) ** 2, axis=1)))

def confidence_bin_report(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> list:
    """Return calibration-like confidence bins for quick reliability checks."""
    max_conf = np.max(y_prob, axis=1)
    correct = (y_true == y_pred).astype(int)
    bins = [(0.0, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.01)]
    report = []
    for low, high in bins:
        mask = (max_conf >= low) & (max_conf < high)
        count = int(mask.sum())
        if count == 0:
            continue
        report.append({
            'bin': f"[{low:.1f}, {min(high, 1.0):.1f})",
            'count': count,
            'avg_confidence': float(max_conf[mask].mean()),
            'empirical_accuracy': float(correct[mask].mean())
        })
    return report

def apply_partly_threshold(y_prob: np.ndarray, partly_idx: int, threshold: float) -> np.ndarray:
    """
    Force Partly_Allowed when its probability crosses a tuned threshold.
    """
    preds = np.argmax(y_prob, axis=1)
    partly_mask = y_prob[:, partly_idx] >= threshold
    preds[partly_mask] = partly_idx
    return preds

def partly_recall_score(y_true: np.ndarray, y_pred: np.ndarray, partly_idx: int) -> float:
    """Compute recall for Partly_Allowed class."""
    mask = (y_true == partly_idx)
    denom = int(mask.sum())
    if denom == 0:
        return 0.0
    return float((y_pred[mask] == partly_idx).sum() / denom)

def improved_modeling_pipeline():
    """Run improved modeling pipeline with proper regularization"""
    
    print("=" * 70)
    print("IMPROVED MODELING PIPELINE")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Load improved data
    print("Step 1: Loading Improved Data")
    print("-" * 50)
    
    try:
        X_train = pd.read_csv('X_train_improved.csv')
        X_test = pd.read_csv('X_test_improved.csv')
        y_train = np.load('y_train_improved.npy')
        y_test = np.load('y_test_improved.npy')
        
        with open('improved_label_encoder.pkl', 'rb') as f:
            label_encoder = pickle.load(f)
        
        print(f"✅ Data loaded successfully!")
        print(f"   Training: {X_train.shape}")
        print(f"   Test: {X_test.shape}")
        print(f"   Classes: {list(label_encoder.classes_)}")
        print()
        
    except FileNotFoundError as e:
        print(f"❌ Error loading data: {e}")
        print("Please run improved_feature_engineering.py first")
        return
    
    # Analyze class distribution
    print("Class Distribution Analysis:")
    train_dist = np.bincount(y_train)
    test_dist = np.bincount(y_test)
    
    for i, class_name in enumerate(label_encoder.classes_):
        train_pct = train_dist[i] / len(y_train) * 100
        test_pct = test_dist[i] / len(y_test) * 100
        print(f"  {class_name}: {train_dist[i]} ({train_pct:.1f}%) train, {test_dist[i]} ({test_pct:.1f}%) test")
    print()
    
    # Step 2: Handle class imbalance with SMOTE
    print("Step 2: Handling Class Imbalance")
    print("-" * 50)
    
    # Check for NaN values
    print("Checking for NaN values...")
    nan_count = X_train.isna().sum().sum()
    if nan_count > 0:
        print(f"Found {nan_count} NaN values in training data")
        print("Dropping rows with NaN values...")
        # Remove rows with NaN
        mask = ~X_train.isna().any(axis=1)
        X_train_clean = X_train[mask]
        y_train_clean = y_train[mask]
        print(f"Removed {len(X_train) - len(X_train_clean)} rows with NaN values")
        print(f"Remaining samples: {len(X_train_clean)}")
    else:
        print("No NaN values found")
        X_train_clean = X_train
        y_train_clean = y_train
    
    # Also clean test set for evaluation
    test_mask = ~X_test.isna().any(axis=1)
    X_test_clean = X_test[test_mask]
    y_test_clean = y_test[test_mask]
    if len(X_test_clean) < len(X_test):
        print(f"Removed {len(X_test) - len(X_test_clean)} rows with NaN values from test set")
    
    # Keep a validation split from training for threshold tuning.
    X_fit, X_val, y_fit, y_val = train_test_split(
        X_train_clean,
        y_train_clean,
        test_size=0.2,
        random_state=42,
        stratify=y_train_clean
    )

    # Apply SMOTE only on fit split.
    smote = SMOTE(random_state=42, k_neighbors=5)
    X_train_smote, y_train_smote = smote.fit_resample(X_fit, y_fit)
    
    print(f"Before SMOTE: {np.bincount(y_fit)}")
    print(f"After SMOTE:  {np.bincount(y_train_smote)}")
    print(f"Fit samples: {len(y_fit)} → {len(y_train_smote)}")
    print(f"Validation samples (held-out from train): {len(y_val)}")
    print()
    
    # Step 3: Configure regularized models
    print("Step 3: Configuring Regularized Models")
    print("-" * 50)
    
    # Cross-validation strategy
    cv_strategy = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    # Regularized models with proper hyperparameters
    models = {
        'Logistic Regression': LogisticRegression(
            C=0.1,                    # Strong regularization
            penalty='l2',
            solver='lbfgs',
            max_iter=1000,
            random_state=42,
            class_weight='balanced'   # Handle class imbalance
        ),
        
        'Random Forest': RandomForestClassifier(
            n_estimators=200,         # More trees
            max_depth=8,              # Reduced depth to prevent overfitting
            min_samples_split=20,     # Increased to prevent overfitting
            min_samples_leaf=10,      # Increased to prevent overfitting
            max_features='sqrt',
            random_state=42,
            class_weight='balanced',
            n_jobs=-1
        ),
        
        'Gradient Boosting': GradientBoostingClassifier(
            n_estimators=120,
            max_depth=3,              # Shallower trees for better generalization
            learning_rate=0.05,       # Lower learning rate
            subsample=0.7,            # Stronger stochastic regularization
            min_samples_split=20,
            min_samples_leaf=10,
            random_state=42
        ),
        
        'Support Vector Machine': SVC(
            C=0.5,                    # Regularization parameter
            kernel='rbf',
            gamma='scale',
            probability=True,
            class_weight='balanced',
            random_state=42
        )
    }

    if LGBMClassifier is not None:
        models['LightGBM'] = LGBMClassifier(
            n_estimators=250,
            learning_rate=0.05,
            max_depth=6,
            num_leaves=31,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            class_weight='balanced',
            verbose=-1
        )

    if CatBoostClassifier is not None:
        models['CatBoost'] = CatBoostClassifier(
            iterations=250,
            learning_rate=0.05,
            depth=6,
            loss_function='MultiClass',
            random_seed=42,
            verbose=False
        )

    # Step 3.1: Hyperparameter tuning for top candidate models
    print("Step 3.1: Hyperparameter Tuning (Macro-F1)")
    print("-" * 50)
    tuning_results = {}
    param_grids = {
        'Logistic Regression': {
            'C': [0.05, 0.1, 0.2, 0.5],
            'solver': ['lbfgs'],
            'class_weight': ['balanced']
        },
        'Random Forest': {
            'n_estimators': [150, 200, 300],
            'max_depth': [6, 8, 10],
            'min_samples_split': [10, 20],
            'min_samples_leaf': [5, 10],
            'max_features': ['sqrt', 'log2']
        },
        'Support Vector Machine': {
            'C': [0.25, 0.5, 1.0],
            'kernel': ['rbf'],
            'gamma': ['scale', 'auto'],
            'class_weight': ['balanced'],
            'probability': [True]
        }
    }

    for name in ['Logistic Regression', 'Random Forest', 'Support Vector Machine']:
        base_model = models[name]
        grid = param_grids[name]
        search = GridSearchCV(
            estimator=base_model,
            param_grid=grid,
            cv=cv_strategy,
            scoring='f1_macro',
            n_jobs=-1,
            verbose=0
        )
        search.fit(X_train_smote, y_train_smote)
        models[name] = search.best_estimator_
        tuning_results[name] = {
            'best_score': float(search.best_score_),
            'best_params': search.best_params_
        }
        print(f"{name} tuned: best_macro_f1={search.best_score_:.4f}")

    if LGBMClassifier is not None and 'LightGBM' in models:
        lgbm_grid = {
            'n_estimators': [200, 300],
            'learning_rate': [0.03, 0.05],
            'max_depth': [5, 7],
            'num_leaves': [31, 63]
        }
        lgbm_search = GridSearchCV(
            estimator=models['LightGBM'],
            param_grid=lgbm_grid,
            cv=cv_strategy,
            scoring='f1_macro',
            n_jobs=-1,
            verbose=0
        )
        lgbm_search.fit(X_train_smote, y_train_smote)
        models['LightGBM'] = lgbm_search.best_estimator_
        tuning_results['LightGBM'] = {
            'best_score': float(lgbm_search.best_score_),
            'best_params': lgbm_search.best_params_
        }
        print(f"LightGBM tuned: best_macro_f1={lgbm_search.best_score_:.4f}")

    if CatBoostClassifier is not None and 'CatBoost' in models:
        cat_grid = {
            'iterations': [200, 300],
            'learning_rate': [0.03, 0.05],
            'depth': [5, 6, 7]
        }
        cat_search = GridSearchCV(
            estimator=models['CatBoost'],
            param_grid=cat_grid,
            cv=cv_strategy,
            scoring='f1_macro',
            n_jobs=-1,
            verbose=0
        )
        cat_search.fit(X_train_smote, y_train_smote)
        models['CatBoost'] = cat_search.best_estimator_
        tuning_results['CatBoost'] = {
            'best_score': float(cat_search.best_score_),
            'best_params': cat_search.best_params_
        }
        print(f"CatBoost tuned: best_macro_f1={cat_search.best_score_:.4f}")
    print()
    
    print(f"Configured {len(models)} regularized models:")
    for name in models.keys():
        print(f"  - {name}")
    print()
    
    # Step 4: Cross-validation evaluation
    print("Step 4: Cross-Validation Evaluation")
    print("-" * 50)
    
    cv_results = []
    
    for name, model in models.items():
        print(f"Evaluating {name}...")
        
        # Use SMOTE data for training
        cv_scores = cross_val_score(
            model, X_train_smote, y_train_smote,
            cv=cv_strategy,
            scoring='f1_macro',       # Macro objective for balanced class behavior
            n_jobs=-1
        )
        
        # Fit on full SMOTE data
        model.fit(X_train_smote, y_train_smote)
        
        # Evaluate on original (non-SMOTE) training data
        train_score = model.score(X_fit, y_fit)
        
        # Calculate overfitting gap
        gap = train_score - cv_scores.mean()
        
        cv_results.append({
            'Model': name,
            'CV_Mean': cv_scores.mean(),
            'CV_Std': cv_scores.std(),
            'Train_Score': train_score,
            'Gap': gap,
            'CV_F1': cv_scores.mean(),
            'Selection_Score': cv_scores.mean() - (0.5 * gap)
        })
        
        print(f"  CV Macro F1-Score: {cv_scores.mean():.4f} (±{cv_scores.std():.4f})")
        print(f"  Train Accuracy: {train_score:.4f}")
        print(f"  Overfitting Gap: {gap:.4f}", end="")
        
        if gap < 0.05:
            print(" ✓ (Excellent)")
        elif gap < 0.10:
            print(" (Good)")
        elif gap < 0.15:
            print(" (Acceptable)")
        else:
            print(" ⚠ (High overfitting)")
        print()
    
    # Create results DataFrame
    cv_df = pd.DataFrame(cv_results)
    stable_df = cv_df[cv_df['Gap'] <= 0.20].copy()
    if stable_df.empty:
        stable_df = cv_df.copy()
    cv_df = cv_df.sort_values('CV_Mean', ascending=False)
    
    print("Cross-Validation Summary:")
    print(cv_df[['Model', 'CV_Mean', 'CV_Std', 'Gap']].to_string(index=False))
    print()
    
    # Select best models for ensemble
    top_models = stable_df.sort_values('Selection_Score', ascending=False).head(3)['Model'].tolist()
    print(f"Top 3 models for ensemble: {top_models}")
    print()
    
    # Step 5: Create Ensemble
    print("Step 5: Creating Weighted Ensemble")
    print("-" * 50)
    
    # Select top models
    ensemble_estimators = []
    for name in top_models:
        if name in models:
            ensemble_estimators.append((name.lower().replace(' ', '_'), models[name]))
    
    # Create voting ensemble
    voting_ensemble = VotingClassifier(
        estimators=ensemble_estimators,
        voting='soft',              # Use probabilities
        weights=None                # Equal weights initially
    )
    
    # Calibrate ensemble for better probabilities
    calibrated_ensemble = CalibratedClassifierCV(
        voting_ensemble, 
        cv=3,                       # 3-fold calibration
        method='isotonic'
    )
    
    # Train ensemble on SMOTE data
    print("Training ensemble...")
    calibrated_ensemble.fit(X_train_smote, y_train_smote)

    # Threshold tuning for Partly_Allowed using validation split only.
    class_names = list(label_encoder.classes_)
    partly_idx = class_names.index('Partly_Allowed') if 'Partly_Allowed' in class_names else None
    tuned_partly_threshold = 0.5
    tuned_partly_recall = 0.0
    tuned_val_accuracy = 0.0
    tuned_val_macro_f1 = 0.0
    if partly_idx is not None:
        val_prob = calibrated_ensemble.predict_proba(X_val)
        best_thr = 0.5
        best_score = -1.0
        best_macro = 0.0
        best_acc = 0.0
        best_partly_recall = 0.0
        # Conservative floor so we don't boost minority recall by collapsing overall accuracy.
        min_val_accuracy = 0.58
        for thr in np.arange(0.25, 0.71, 0.03):
            val_pred_thr = apply_partly_threshold(val_prob, partly_idx, float(thr))
            macro_f1 = f1_score(y_val, val_pred_thr, average='macro')
            val_acc = accuracy_score(y_val, val_pred_thr)
            p_recall = partly_recall_score(y_val, val_pred_thr, partly_idx)
            if val_acc < min_val_accuracy:
                continue
            # Balanced target: prioritize partly recall and macro-f1 while protecting accuracy.
            score = (0.50 * p_recall) + (0.30 * macro_f1) + (0.20 * val_acc)
            if score > best_score:
                best_score = score
                best_thr = float(thr)
                best_macro = macro_f1
                best_acc = val_acc
                best_partly_recall = p_recall
        tuned_partly_threshold = best_thr
        tuned_partly_recall = best_partly_recall
        tuned_val_accuracy = best_acc
        tuned_val_macro_f1 = best_macro
        print(
            f"Tuned Partly_Allowed threshold: {tuned_partly_threshold:.2f} "
            f"(val partly-recall={best_partly_recall:.4f}, val macro-F1={best_macro:.4f}, val acc={best_acc:.4f})"
        )
    else:
        print("Partly_Allowed class not found for threshold tuning; using default argmax.")
    
    # Evaluate ensemble
    ensemble_train_score = calibrated_ensemble.score(X_fit, y_fit)
    ensemble_cv_scores = cross_val_score(
        calibrated_ensemble, X_train_smote, y_train_smote,
        cv=cv_strategy, scoring='f1_weighted', n_jobs=-1
    )
    
    print(f"Ensemble CV F1-Score: {ensemble_cv_scores.mean():.4f} (±{ensemble_cv_scores.std():.4f})")
    print(f"Ensemble Train Accuracy: {ensemble_train_score:.4f}")
    print(f"Ensemble Overfitting Gap: {ensemble_train_score - ensemble_cv_scores.mean():.4f}")
    print()
    
    # Step 6: Final Test Evaluation
    print("Step 6: Final Test Evaluation")
    print("-" * 50)
    
    # Predictions on test set
    y_pred_proba_ensemble = calibrated_ensemble.predict_proba(X_test_clean)
    if partly_idx is not None:
        y_pred_ensemble = apply_partly_threshold(y_pred_proba_ensemble, partly_idx, tuned_partly_threshold)
    else:
        y_pred_ensemble = np.argmax(y_pred_proba_ensemble, axis=1)
    
    # Calculate metrics
    test_accuracy = accuracy_score(y_test_clean, y_pred_ensemble)
    test_f1 = f1_score(y_test_clean, y_pred_ensemble, average='weighted')
    test_macro_f1 = f1_score(y_test_clean, y_pred_ensemble, average='macro')
    test_balanced_acc = balanced_accuracy_score(y_test_clean, y_pred_ensemble)
    test_brier = multiclass_brier_score(y_test_clean, y_pred_proba_ensemble)
    test_precision, test_recall, _, _ = precision_recall_fscore_support(
        y_test_clean, y_pred_ensemble, average='weighted'
    )
    
    print("Ensemble Test Performance:")
    print(f"  Accuracy: {test_accuracy:.4f} ({test_accuracy*100:.2f}%)")
    print(f"  F1-Score: {test_f1:.4f}")
    print(f"  Macro F1-Score: {test_macro_f1:.4f}")
    print(f"  Balanced Accuracy: {test_balanced_acc:.4f}")
    print(f"  Brier Score: {test_brier:.4f}")
    print(f"  Precision: {test_precision:.4f}")
    print(f"  Recall: {test_recall:.4f}")
    print()

    conf_report = confidence_bin_report(y_test_clean, y_pred_ensemble, y_pred_proba_ensemble)
    if conf_report:
        print("Confidence Bin Reliability:")
        for row in conf_report:
            print(
                f"  {row['bin']}: n={row['count']}, "
                f"avg_conf={row['avg_confidence']:.3f}, "
                f"acc={row['empirical_accuracy']:.3f}"
            )
        print()
    
    # Detailed classification report
    print("Per-Class Performance:")
    print(classification_report(y_test_clean, y_pred_ensemble, target_names=label_encoder.classes_))
    print()
    
    # Confusion matrix
    cm = confusion_matrix(y_test_clean, y_pred_ensemble)
    print("Confusion Matrix:")
    print(cm)
    print()
    
    # Per-class accuracy
    print("Per-Class Accuracy:")
    for i, class_name in enumerate(label_encoder.classes_):
        class_acc = cm[i, i] / cm[i].sum() if cm[i].sum() > 0 else 0
        print(f"  {class_name}: {class_acc:.4f} ({class_acc*100:.1f}%)")
    print()
    
    # Step 7: Compare with baseline
    print("Step 7: Performance Comparison")
    print("-" * 50)
    
    try:
        # Load baseline model if available
        with open('appeal_outcome_model.pkl', 'rb') as f:
            baseline_model = pickle.load(f)
        
        # Load baseline data
        X_train_baseline = pd.read_csv('X_train.csv')
        X_test_baseline = pd.read_csv('X_test.csv')
        
        # Check if dimensions match
        if X_test_baseline.shape[1] == X_test_clean.shape[1]:
            # Baseline predictions
            y_pred_baseline = baseline_model.predict(X_test_baseline)
            baseline_accuracy = accuracy_score(y_test_clean, y_pred_baseline)
            
            print(f"Baseline Test Accuracy: {baseline_accuracy:.4f} ({baseline_accuracy*100:.2f}%)")
            print(f"Improved Test Accuracy: {test_accuracy:.4f} ({test_accuracy*100:.2f}%)")
            print(f"Improvement: {(test_accuracy - baseline_accuracy)*100:+.2f}%")
        else:
            print(f"Cannot compare: Different feature dimensions")
            print(f"  Baseline: {X_test_baseline.shape[1]} features")
            print(f"  Improved: {X_test_clean.shape[1]} features")
        print()
        
    except FileNotFoundError:
        print("Baseline model not found - skipping comparison")
        print()
    except Exception as e:
        print(f"Error during comparison: {e}")
        print()
    
    # Step 8: Save improved model
    print("Step 8: Save Improved Model")
    print("-" * 50)
    
    # Save ensemble model
    with open('improved_ensemble_model.pkl', 'wb') as f:
        pickle.dump(calibrated_ensemble, f)
    
    # Save model metadata
    metadata = {
        'model_type': 'Calibrated Voting Ensemble',
        'ensemble_models': top_models,
        'cv_f1_score': float(ensemble_cv_scores.mean()),
        'test_accuracy': float(test_accuracy),
        'test_f1_score': float(test_f1),
        'test_macro_f1_score': float(test_macro_f1),
        'test_balanced_accuracy': float(test_balanced_acc),
        'test_brier_score': float(test_brier),
        'test_precision': float(test_precision),
        'test_recall': float(test_recall),
        'n_features': X_train.shape[1],
        'n_train_samples': len(X_train),
        'n_test_samples': len(X_test),
        'target_classes': list(label_encoder.classes_),
        'training_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'overfitting_gap': float(ensemble_train_score - ensemble_cv_scores.mean()),
        'smote_applied': True,
        'feature_engineering': 'improved_hybrid',
        'confidence_bin_reliability': conf_report,
        'partly_allowed_threshold': float(tuned_partly_threshold),
        'validation_partly_recall': float(tuned_partly_recall),
        'validation_macro_f1': float(tuned_val_macro_f1),
        'validation_accuracy': float(tuned_val_accuracy),
        'hyperparameter_tuning': tuning_results
    }
    
    import json
    with open('improved_model_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=4)
    
    print("✅ Improved model saved successfully!")
    print("   - improved_ensemble_model.pkl")
    print("   - improved_model_metadata.json")
    print()
    
    # Step 9: Visualize results
    print("Step 9: Generate Visualizations")
    print("-" * 50)
    
    # Plot confusion matrix
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=label_encoder.classes_,
                yticklabels=label_encoder.classes_)
    plt.title('Improved Model - Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig('improved_confusion_matrix.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Plot CV results
    plt.figure(figsize=(10, 6))
    cv_df_sorted = cv_df.sort_values('CV_Mean', ascending=True)
    
    plt.barh(cv_df_sorted['Model'], cv_df_sorted['CV_Mean'], 
             xerr=cv_df_sorted['CV_Std'], capsize=5, alpha=0.7)
    plt.xlabel('CV F1-Score')
    plt.title('Cross-Validation Performance Comparison')
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig('improved_cv_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("Visualizations saved:")
    print("   - improved_confusion_matrix.png")
    print("   - improved_cv_comparison.png")
    print()
    
    # Final summary
    print("=" * 70)
    print("IMPROVED MODELING COMPLETE!")
    print("=" * 70)
    print()
    print("📊 Final Results:")
    print(f"   • Model: Calibrated Voting Ensemble")
    print(f"   • Test Accuracy: {test_accuracy*100:.2f}%")
    print(f"   • Test F1-Score: {test_f1:.4f}")
    print(f"   • Test Macro F1-Score: {test_macro_f1:.4f}")
    print(f"   • Balanced Accuracy: {test_balanced_acc:.4f}")
    print(f"   • Brier Score: {test_brier:.4f}")
    print(f"   • Overfitting Gap: {ensemble_train_score - ensemble_cv_scores.mean():.4f}")
    print(f"   • Features: {X_train.shape[1]} (hybrid selection)")
    print()
    print("🔧 Improvements Made:")
    print("   • Fixed TF-IDF vectorization")
    print("   • Hybrid feature selection (legal + BERT + TF-IDF)")
    print("   • Proper regularization to prevent overfitting")
    print("   • SMOTE for class imbalance")
    print("   • Calibrated ensemble for better probabilities")
    print("=" * 70)
    
    return calibrated_ensemble, metadata

def hyperparameter_tuning_best_model(X_train, y_train, X_test, y_test, label_encoder):
    """Fine-tune the best performing model"""
    
    print("=" * 70)
    print("HYPERPARAMETER TUNING")
    print("=" * 70)
    print()
    
    # Apply SMOTE
    smote = SMOTE(random_state=42)
    X_train_smote, y_train_smote = smote.fit_resample(X_train, y_train)
    
    # Use Random Forest (usually performs well)
    param_grid = {
        'n_estimators': [150, 200, 250],
        'max_depth': [6, 8, 10],
        'min_samples_split': [15, 20, 25],
        'min_samples_leaf': [8, 10, 12],
        'max_features': ['sqrt', 'log2']
    }
    
    rf = RandomForestClassifier(
        random_state=42,
        class_weight='balanced',
        n_jobs=-1
    )
    
    cv_strategy = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    grid_search = GridSearchCV(
        rf,
        param_grid,
        cv=cv_strategy,
        scoring='f1_weighted',
        n_jobs=-1,
        verbose=1
    )
    
    print("Running grid search...")
    grid_search.fit(X_train_smote, y_train_smote)
    
    print(f"\nBest parameters: {grid_search.best_params_}")
    print(f"Best CV F1-Score: {grid_search.best_score_:.4f}")
    
    # Evaluate on test set
    best_model = grid_search.best_estimator_
    y_pred = best_model.predict(X_test)
    test_accuracy = accuracy_score(y_test, y_pred)
    test_f1 = f1_score(y_test, y_pred, average='weighted')
    
    print(f"\nTest Performance:")
    print(f"  Accuracy: {test_accuracy:.4f} ({test_accuracy*100:.2f}%)")
    print(f"  F1-Score: {test_f1:.4f}")
    
    # Save tuned model
    with open('tuned_random_forest.pkl', 'wb') as f:
        pickle.dump(best_model, f)
    
    print("\n✅ Tuned model saved as 'tuned_random_forest.pkl'")
    
    return best_model, grid_search.best_params_

if __name__ == "__main__":
    improved_modeling_pipeline()
