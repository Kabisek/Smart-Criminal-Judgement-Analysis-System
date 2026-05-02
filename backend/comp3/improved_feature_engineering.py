"""
Improved Feature Engineering for Appeal Outcome Prediction
Fixes TF-IDF issues and implements hybrid feature selection
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.preprocessing import StandardScaler, LabelEncoder
import pickle
import re
from datetime import datetime

LEAKAGE_FORBIDDEN_COLUMNS = [
    'court_of_appeal_analysis_summary',
    'coa_final_outcome_class',
    'coa_conviction_status',
    'coa_sentence_type',
    'release_ordered',
    'final_charge_after_appeal',
    'combined_outcome',
    'conviction_clean'
]

PRE_APPEAL_TEXT_COLUMNS = [
    'brief_facts_summary',
    'grounds_of_appeal_raw_text_summary',
    'hc_judgment_summary',
    'defence_version_summary',
    'witness_evidence_analysis_summary'
]

def improved_feature_engineering():
    """Run improved feature engineering pipeline"""
    
    print("=" * 70)
    print("IMPROVED FEATURE ENGINEERING PIPELINE")
    print("=" * 70)
    print()
    
    # Load cleaned dataset
    print("Loading cleaned dataset...")
    df = pd.read_csv('dataset_cleaned_v2.csv')
    print(f"Loaded: {len(df)} records")
    print()

    # Apply a strict leakage-safe policy for feature generation.
    present_forbidden = [c for c in LEAKAGE_FORBIDDEN_COLUMNS if c in df.columns]
    if present_forbidden:
        print("Leakage guard: excluding post-judgment/proxy columns from inputs")
        print(f"Excluded columns: {present_forbidden}")
        df = df.drop(columns=present_forbidden)
        print()
    
    # 1. FIXED TF-IDF with proper parameters
    print("Step 1: Improved TF-IDF Vectorization")
    print("-" * 50)
    
    # Combine text columns
    text_columns = [col for col in PRE_APPEAL_TEXT_COLUMNS if col in df.columns]
    if not text_columns:
        raise ValueError("No valid pre-appeal text columns found for feature engineering.")
    df['combined_text'] = df[text_columns].fillna('').agg(' '.join, axis=1)
    
    # Remove empty texts
    df = df[df['combined_text'].str.len() > 10].copy()
    print(f"Records after filtering empty text: {len(df)}")
    
    # IMPROVED TF-IDF parameters
    tfidf_vectorizer = TfidfVectorizer(
        max_features=1000,      # Increased from 500
        min_df=1,               # Decreased from 2 (was causing the error)
        max_df=0.95,            # Increased from 0.8
        ngram_range=(1,2),      # Include bigrams
        stop_words='english',
        lowercase=True,
        strip_accents='ascii'
    )
    
    try:
        # Fit TF-IDF
        tfidf_matrix = tfidf_vectorizer.fit_transform(df['combined_text'])
        tfidf_features = tfidf_vectorizer.get_feature_names_out()
        
        print(f"✅ TF-IDF SUCCESS!")
        print(f"   Features created: {len(tfidf_features)}")
        print(f"   Sample features: {list(tfidf_features[:10])}")
        print()
        
        # Save TF-IDF
        with open('improved_tfidf_vectorizer.pkl', 'wb') as f:
            pickle.dump(tfidf_vectorizer, f)
        
    except Exception as e:
        print(f"❌ TF-IDF failed: {e}")
        tfidf_matrix = None
        tfidf_features = []
    
    # 2. Extract traditional features
    print("Step 2: Extract Traditional Legal Features")
    print("-" * 50)
    
    traditional_features = extract_all_legal_features(df)
    print(f"Traditional features extracted: {len(traditional_features.columns)}")
    print(f"Sample features: {list(traditional_features.columns[:10])}")
    print()
    
    # 3. Combine all features
    print("Step 3: Combine All Features")
    print("-" * 50)
    
    # Start with traditional features
    all_features = traditional_features.copy()
    
    # Add TF-IDF if successful
    if tfidf_matrix is not None:
        tfidf_df = pd.DataFrame(
            tfidf_matrix.toarray(),
            columns=[f'tfidf_{f}' for f in tfidf_features],
            index=df.index
        )
        all_features = pd.concat([all_features, tfidf_df], axis=1)
        print(f"Added {len(tfidf_features)} TF-IDF features")
    
    print(f"Total features before BERT: {len(all_features.columns)}")
    print()
    
    # 4. Add BERT embeddings (if available)
    try:
        bert_embeddings = np.load('bert_embeddings_all.npy')
        if len(bert_embeddings) == len(df):
            bert_df = pd.DataFrame(
                bert_embeddings,
                columns=[f'bert_{i}' for i in range(bert_embeddings.shape[1])],
                index=df.index
            )
            all_features = pd.concat([all_features, bert_df], axis=1)
            print(f"Added {bert_embeddings.shape[1]} BERT features")
        else:
            print("BERT embeddings size mismatch - skipping")
    except FileNotFoundError:
        print("BERT embeddings not found - skipping")
    
    print(f"Final feature count: {len(all_features.columns)}")
    print()
    
    # 5. Prepare targets
    print("Step 4: Prepare Target Variables")
    print("-" * 50)
    
    # Clean target variable
    df = df.dropna(subset=['outcome_clean'])
    # Keep feature matrix aligned with the filtered target rows.
    all_features = all_features.loc[df.index]
    y = df['outcome_clean'].values
    
    # Encode target
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    print(f"Target classes: {list(label_encoder.classes_)}")
    print(f"Class distribution: {np.bincount(y_encoded)}")
    print()
    
    # 6. HYBRID FEATURE SELECTION
    print("Step 5: HYBRID Feature Selection")
    print("-" * 50)
    
    selected_features = hybrid_feature_selection(all_features, y_encoded)
    print(f"Selected {len(selected_features)} features")
    
    # Analyze feature composition
    bert_count = sum(1 for f in selected_features if f.startswith('bert_'))
    tfidf_count = sum(1 for f in selected_features if f.startswith('tfidf_'))
    legal_count = len(selected_features) - bert_count - tfidf_count
    
    print(f"Feature composition:")
    print(f"  Legal features: {legal_count} ({legal_count/len(selected_features)*100:.1f}%)")
    print(f"  BERT embeddings: {bert_count} ({bert_count/len(selected_features)*100:.1f}%)")
    print(f"  TF-IDF features: {tfidf_count} ({tfidf_count/len(selected_features)*100:.1f}%)")
    print()
    
    # 7. Train-test split with grouped temporal validation
    print("Step 6: Grouped Temporal Train/Test Split")
    print("-" * 50)

    split_meta = {}
    if 'coa_year' not in df.columns:
        raise ValueError("coa_year is required for temporal split.")

    case_col = 'court_of_appeal_case_no' if 'court_of_appeal_case_no' in df.columns else None
    years = pd.to_numeric(df['coa_year'], errors='coerce')
    years = years.fillna(years.median() if years.notna().any() else 0)

    if case_col:
        case_year_df = pd.DataFrame({
            'case_id': df[case_col].fillna('unknown_case'),
            'coa_year': years,
        })
        # Assign each case to its latest observed year to avoid train/test leakage.
        case_year_summary = case_year_df.groupby('case_id', as_index=False)['coa_year'].max()
        # Strict temporal cutoff (80th percentile of case-level years).
        cutoff_year = float(np.quantile(case_year_summary['coa_year'].values, 0.8))

        train_cases = set(case_year_summary[case_year_summary['coa_year'] < cutoff_year]['case_id'])
        test_cases = set(case_year_summary[case_year_summary['coa_year'] >= cutoff_year]['case_id'])

        # Fallback safety if one side becomes empty.
        if not train_cases or not test_cases:
            case_year_summary = case_year_summary.sort_values(['coa_year', 'case_id']).reset_index(drop=True)
            split_case_idx = int(len(case_year_summary) * 0.8)
            train_cases = set(case_year_summary.iloc[:split_case_idx]['case_id'])
            test_cases = set(case_year_summary.iloc[split_case_idx:]['case_id'])
            cutoff_year = float(case_year_summary.iloc[split_case_idx]['coa_year']) if split_case_idx < len(case_year_summary) else float(case_year_summary['coa_year'].max())

        train_mask = case_year_df['case_id'].isin(train_cases).values
        test_mask = case_year_df['case_id'].isin(test_cases).values
        split_meta['split_strategy'] = 'grouped_temporal_by_case'
        split_meta['temporal_cutoff_year'] = cutoff_year
        split_meta['n_train_cases'] = len(train_cases)
        split_meta['n_test_cases'] = len(test_cases)
    else:
        # Fallback: strict temporal split by year ordering.
        df_sorted = df.assign(_coa_year_num=years).sort_values('_coa_year_num')
        split_idx = int(len(df_sorted) * 0.8)
        train_idx = df_sorted.iloc[:split_idx].index
        test_idx = df_sorted.iloc[split_idx:].index
        train_mask = df.index.isin(train_idx)
        test_mask = df.index.isin(test_idx)
        split_meta['split_strategy'] = 'temporal_row_split_fallback'

    X_train = all_features.loc[df.index[train_mask]]
    X_test = all_features.loc[df.index[test_mask]]
    y_train = y_encoded[train_mask]
    y_test = y_encoded[test_mask]

    if len(np.unique(y_train)) < len(label_encoder.classes_) or len(np.unique(y_test)) < 2:
        raise ValueError("Temporal/grouped split produced insufficient class coverage. Adjust split strategy.")

    train_years = years[train_mask]
    test_years = years[test_mask]

    print(f"Training set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    print(f"Years in train: {train_years.min()}-{train_years.max()}")
    print(f"Years in test: {test_years.min()}-{test_years.max()}")
    print()
    
    # 8. Scale features
    print("Step 7: Feature Scaling")
    print("-" * 50)
    
    # Select features before scaling
    X_train_selected = X_train[selected_features]
    X_test_selected = X_test[selected_features]
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_selected)
    X_test_scaled = scaler.transform(X_test_selected)
    
    # Convert back to DataFrame
    X_train_final = pd.DataFrame(X_train_scaled, columns=selected_features)
    X_test_final = pd.DataFrame(X_test_scaled, columns=selected_features)
    
    print("Features scaled using StandardScaler")
    print()
    
    # 9. Save all artifacts
    print("Step 8: Save Processed Data")
    print("-" * 50)
    
    # Save datasets
    X_train_final.to_csv('X_train_improved.csv', index=False)
    X_test_final.to_csv('X_test_improved.csv', index=False)
    
    # Save targets
    np.save('y_train_improved.npy', y_train)
    np.save('y_test_improved.npy', y_test)
    
    # Save preprocessing objects
    with open('improved_scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    with open('improved_label_encoder.pkl', 'wb') as f:
        pickle.dump(label_encoder, f)
    with open('improved_selected_features.pkl', 'wb') as f:
        pickle.dump(selected_features, f)
    
    # Save metadata
    metadata = {
        'total_samples': len(df),
        'train_samples': len(X_train),
        'test_samples': len(X_test),
        'total_features': len(all_features.columns),
        'selected_features': len(selected_features),
        'feature_composition': {
            'legal': legal_count,
            'bert': bert_count,
            'tfidf': tfidf_count
        },
        'target_classes': list(label_encoder.classes_),
        **split_meta,
        'creation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    import json
    with open('improved_feature_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=4)
    
    print("✅ All files saved successfully!")
    print()
    print("=" * 70)
    print("IMPROVED FEATURE ENGINEERING COMPLETE!")
    print("=" * 70)
    print(f"📊 Summary:")
    print(f"   • Samples: {len(df)}")
    print(f"   • Features: {len(selected_features)} selected from {len(all_features.columns)}")
    print(f"   • Legal features: {legal_count} ({legal_count/len(selected_features)*100:.1f}%)")
    print(f"   • BERT embeddings: {bert_count} ({bert_count/len(selected_features)*100:.1f}%)")
    print(f"   • TF-IDF features: {tfidf_count} ({tfidf_count/len(selected_features)*100:.1f}%)")
    print("=" * 70)
    
    return X_train_final, X_test_final, y_train, y_test, selected_features, label_encoder

def extract_all_legal_features(df):
    """Extract comprehensive legal features"""
    
    features = pd.DataFrame(index=df.index)
    
    # 1. Text statistics
    text_cols = [col for col in PRE_APPEAL_TEXT_COLUMNS if col in df.columns]
    for col in text_cols:
        if col in df.columns:
            features[f'{col}_length'] = df[col].fillna('').str.len()
            features[f'{col}_word_count'] = df[col].fillna('').str.split().str.len()
    
    # 2. Grounds of appeal features
    ground_keywords = {
        'contradictions': ['contradiction', 'inconsistent', 'conflicting', 'discrepancy'],
        'chain_of_custody': ['chain of custody', 'custody', 'preservation', 'handling'],
        'illegal_search': ['illegal search', 'unlawful search', 'search raid', 'illegal raid'],
        'wrong_identification': ['identification', 'identify', 'mistaken identity', 'id parade'],
        'dying_declaration': ['dying declaration', 'deathbed statement', 'dying declaration'],
        'circumstantial': ['circumstantial', 'indirect evidence', 'circumstantial evidence'],
        'medical_inconsistency': ['medical', 'jmo', 'post-mortem', 'autopsy', 'medical evidence'],
        'misdirection': ['misdirection', 'wrong direction', 'legal error', 'direction'],
        'procedural_error': ['procedural', 'procedure', 'process error', 'procedural defect'],
        'new_evidence': ['new evidence', 'fresh evidence', 'additional evidence'],
        'excessive_sentence': ['excessive', 'harsh', 'inadequate sentence', 'sentence'],
        'delay_prejudice': ['delay', 'prejudice', 'lapse of time', 'delay'],
        'judicial_bias': ['bias', 'unfair', 'prejudiced judge', 'bias']
    }
    
    for ground, keywords in ground_keywords.items():
        feature_name = f'gnd_{ground}'
        features[feature_name] = 0
        
        for col in text_cols:
            if col in df.columns:
                text = df[col].fillna('').str.lower()
                for keyword in keywords:
                    features[feature_name] = features[feature_name] | text.str.contains(keyword, na=False)
        features[feature_name] = features[feature_name].astype(float)
    
    # 3. Evidence presence features
    evidence_keywords = {
        'eyewitness': ['eyewitness', 'witness', 'testimony', 'eye witness'],
        'child_witness': ['child witness', 'minor witness', 'child testimony'],
        'expert_evidence': ['expert', 'jmo', 'analyst', 'specialist', 'expert testimony'],
        'forensic_evidence': ['forensic', 'dna', 'fingerprint', 'ballistic', 'forensic evidence'],
        'dying_declaration': ['dying declaration'],
        'confession': ['confession', 'admitted', 'dock statement', 'confessed'],
        'procedural_defects': ['procedural defect', 'process error', 'procedural'],
        'digital_evidence': ['cctv', 'phone', 'digital', 'video', 'recording', 'digital evidence'],
        'hospital_treatment': ['hospital', 'medical treatment', 'admitted to hospital']
    }
    
    for evidence, keywords in evidence_keywords.items():
        feature_name = f'{evidence}_present'
        features[feature_name] = 0
        
        for col in text_cols:
            if col in df.columns:
                text = df[col].fillna('').str.lower()
                for keyword in keywords:
                    features[feature_name] = features[feature_name] | text.str.contains(keyword, na=False)
        features[feature_name] = features[feature_name].astype(float)
    
    # 4. Medical evidence strength score
    medical_terms = ['medical', 'jmo', 'post-mortem', 'autopsy', 'pathologist', 'medical evidence']
    features['medical_evidence_score'] = 0
    
    for col in text_cols:
        if col in df.columns:
            text = df[col].fillna('').str.lower()
            for term in medical_terms:
                features['medical_evidence_score'] += text.str.contains(term, na=False).astype(int)
    
    # 5. Offence category (one-hot encoding if available)
    if 'offence_category_grouped' in df.columns:
        offence_dummies = pd.get_dummies(df['offence_category_grouped'], prefix='offence_category')
        features = pd.concat([features, offence_dummies], axis=1)
    
    # 6. Appeal type (one-hot encoding if available)
    if 'appeal_type_simplified' in df.columns:
        appeal_dummies = pd.get_dummies(df['appeal_type_simplified'], prefix='appeal_type')
        features = pd.concat([features, appeal_dummies], axis=1)
    
    # 7. Temporal features
    if 'coa_year' in df.columns:
        features['coa_year'] = df['coa_year']
    
    if 'appeal_duration_days' in df.columns:
        features['appeal_duration_days'] = df['appeal_duration_days']
    
    # 8. Interaction features
    if 'eyewitness_present' in features.columns and 'murder_present' in features.columns:
        features['murder_with_eyewitness'] = features['eyewitness_present'] * features.get('murder_present', 0)
    
    if 'drug_present' in features.columns and 'forensic_evidence_present' in features.columns:
        features['drug_with_forensic'] = features['drug_present'] * features['forensic_evidence_present']
    
    # Evidence count
    evidence_cols = [col for col in features.columns if col.endswith('_present')]
    if evidence_cols:
        features['evidence_count'] = features[evidence_cols].sum(axis=1)
    
    return features

def hybrid_feature_selection(X, y):
    """Implement hybrid feature selection combining domain knowledge and statistical tests"""
    
    print("Implementing hybrid feature selection...")
    
    # 1. Identify feature types
    all_features = X.columns.tolist()
    
    legal_features = []
    bert_features = []
    tfidf_features = []
    
    for feature in all_features:
        if feature.startswith('bert_'):
            bert_features.append(feature)
        elif feature.startswith('tfidf_'):
            tfidf_features.append(feature)
        else:
            legal_features.append(feature)
    
    print(f"Feature inventory:")
    print(f"  Legal features: {len(legal_features)}")
    print(f"  BERT embeddings: {len(bert_features)}")
    print(f"  TF-IDF features: {len(tfidf_features)}")
    
    # 2. Keep ALL legal features (domain knowledge)
    selected_features = legal_features.copy()
    print(f"Keeping all {len(legal_features)} legal features")
    
    # 3. Select top BERT features
    if bert_features:
        n_bert_to_select = min(100, len(bert_features))  # Limit BERT features
        print(f"Selecting top {n_bert_to_select} BERT features...")
        
        X_bert = X[bert_features]
        selector_bert = SelectKBest(score_func=f_classif, k=n_bert_to_select)
        selector_bert.fit(X_bert, y)
        
        selected_bert_mask = selector_bert.get_support()
        selected_bert = [bert_features[i] for i, selected in enumerate(selected_bert_mask) if selected]
        
        selected_features.extend(selected_bert)
        print(f"Selected {len(selected_bert)} BERT features")
    
    # 4. Select top TF-IDF features
    if tfidf_features:
        n_tfidf_to_select = min(50, len(tfidf_features))  # Limit TF-IDF features
        print(f"Selecting top {n_tfidf_to_select} TF-IDF features...")
        
        X_tfidf = X[tfidf_features]
        selector_tfidf = SelectKBest(score_func=f_classif, k=n_tfidf_to_select)
        selector_tfidf.fit(X_tfidf, y)
        
        selected_tfidf_mask = selector_tfidf.get_support()
        selected_tfidf = [tfidf_features[i] for i, selected in enumerate(selected_tfidf_mask) if selected]
        
        selected_features.extend(selected_tfidf)
        print(f"Selected {len(selected_tfidf)} TF-IDF features")
    
    print(f"Total selected features: {len(selected_features)}")
    
    return selected_features

if __name__ == "__main__":
    improved_feature_engineering()
