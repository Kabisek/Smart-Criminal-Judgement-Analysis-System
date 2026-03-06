import streamlit as st
import pandas as pd
import numpy as np
import pickle
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Appeal Outcome Predictor",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 42px;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 20px;
        background: linear-gradient(90deg, #f0f2f6 0%, #e8eaf0 100%);
        border-radius: 10px;
        margin-bottom: 30px;
    }
    .prediction-box {
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #1f77b4;
        background-color: #f0f8ff;
        margin: 10px 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-size: 18px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Load model
# Load model
@st.cache_resource
def load_model():
    try:
        with open('appeal_outcome_imbalance_week7.pkl', 'rb') as f:
            model_data = pickle.load(f)
        
        # FIX: Check if model_data is a dict or the model itself
        if isinstance(model_data, dict):
            model = model_data['model']
            feature_selector = model_data.get('feature_selector')
            label_encoder = model_data.get('label_encoder')
            selected_features = model_data.get('selected_features')
            scaler = model_data.get('scaler')
        else:
            # If model_data is directly the model object
            model = model_data
            feature_selector = None
            label_encoder = None
            selected_features = None
            scaler = None
        
        # Load metadata
        try:
            with open('model_metadata.json', 'r') as f:
                metadata = json.load(f)
        except:
            metadata = {
                'accuracy': 0.6255,
                'model_name': 'XGBoost Custom Weights',
                'training_date': '2026-01-06',
                'training_samples': 1000,
                'num_features': 150
            }
        
        return model, feature_selector, label_encoder, selected_features, scaler, metadata
        
    except FileNotFoundError:
        st.error("❌ Model file 'appeal_outcome_imbalance_week7.pkl' not found!")
        st.info("📁 Please place the model file in the same directory as this script.")
        
        # Show current directory
        import os
        st.write(f"**Current directory:** `{os.getcwd()}`")
        st.write("**Files in directory:**")
        files = [f for f in os.listdir('.') if f.endswith('.pkl')]
        if files:
            st.write(files)
        else:
            st.warning("No .pkl files found in current directory!")
        
        return None, None, None, None, None, None
        
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        st.write("**Error type:**", type(e).__name__)
        
        # Debug info
        with st.expander("🐛 Debug Information"):
            st.write("Model file exists, but structure issue detected.")
            st.write("Trying to inspect model file...")
            
            try:
                with open('appeal_outcome_imbalance_week7.pkl', 'rb') as f:
                    test_load = pickle.load(f)
                st.write(f"**Type of loaded object:** {type(test_load)}")
                if isinstance(test_load, dict):
                    st.write(f"**Keys in model file:** {list(test_load.keys())}")
            except:
                pass
        
        return None, None, None, None, None, None


# Header
st.markdown('<div class="main-header">⚖️ Sri Lankan Court of Appeal<br/>Appeal Outcome Prediction System</div>', unsafe_allow_html=True)

# Load model
with st.spinner('🔄 Loading AI Model...'):
    model, feature_selector, label_encoder, selected_features, scaler, metadata = load_model()

if model is None:
    st.error("❌ Model file 'appeal_outcome_imbalance_week7.pkl' not found!")
    st.info("📁 Please place the model file in the same directory as this script.")
    st.stop()

# Sidebar - SAFE VERSION
with st.sidebar:
    st.title("📊 System Info")
    
    # Get metadata values safely
    try:
        accuracy = metadata.get('accuracy', 0.6255) if metadata else 0.6255
        model_name = metadata.get('model_name', 'XGBoost') if metadata else 'XGBoost'
        training_date = metadata.get('training_date', '2026-01-06') if metadata else '2026-01-06'
        training_samples = metadata.get('training_samples', 1000) if metadata else 1000
        num_features = metadata.get('num_features', 150) if metadata else 150
    except:
        # Fallback defaults
        accuracy = 0.6255
        model_name = 'XGBoost Custom Weights'
        training_date = '2026-01-06'
        training_samples = 1000
        num_features = 150
    
    # Display metrics
    st.metric("Model Accuracy", f"{accuracy*100:.2f}%")
    st.metric("Model Type", model_name)
    st.metric("Last Updated", training_date)
    
    st.markdown("---")
    st.subheader("📈 Performance")
    st.write(f"**Training Samples:** {training_samples:,}")
    st.write(f"**Features:** {num_features}")
    st.write("**Classes:** 3 outcomes")
    
    st.markdown("---")
    st.info("""
    **Class Performance:**
    - Appeal Dismissed: 79.4%
    - Appeal Allowed: 67.8%
    - Partly Allowed: 37.1%
    """)
    
    st.markdown("---")
    st.warning("⚠️ **Disclaimer**\n\nThis is a decision support tool, not legal advice. Consult legal professionals.")


# Main tabs
tab1, tab2, tab3 = st.tabs(["📝 Predict", "📊 Performance", "ℹ️ Guide"])

with tab1:
    st.header("📋 Enter Case Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏛️ Basic Information")
        
        offense_type = st.selectbox(
            "Offense Category",
            ["Murder", "Drug Trafficking", "Rape", "Robbery", "Grave Sexual Abuse", 
             "Bribery", "Attempted Murder", "Fraud", "Other"],
            index=0
        )
        
        hc_sentence = st.text_input(
            "High Court Sentence",
            placeholder="e.g., Life Imprisonment, 10 years rigorous imprisonment"
        )
        
        appeal_duration = st.slider(
            "Appeal Duration (days)",
            min_value=0,
            max_value=2000,
            value=365,
            step=30
        )
        
        st.markdown("---")
        st.subheader("📋 Grounds of Appeal")
        
        col1a, col1b = st.columns(2)
        
        with col1a:
            gnd_contradictions = st.checkbox("Contradictions")
            gnd_chain = st.checkbox("Chain of custody")
            gnd_identification = st.checkbox("Wrong ID")
            gnd_medical = st.checkbox("Medical issues")
        
        with col1b:
            gnd_misdirection = st.checkbox("Misdirection")
            gnd_procedural = st.checkbox("Procedural error")
            gnd_sentence = st.checkbox("Sentence issue")
            gnd_circumstantial = st.checkbox("Weak evidence")
    
    with col2:
        st.subheader("🔍 Evidence Analysis")
        
        eyewitness = st.radio("Eyewitness Testimony", ["Yes", "No"], horizontal=True)
        expert_evidence = st.radio("Expert Evidence", ["Yes", "No"], horizontal=True)
        forensic = st.radio("Forensic Evidence", ["Yes", "No"], horizontal=True)
        
        medical_strength = st.select_slider(
            "Medical Evidence Strength",
            options=["None", "Weak", "Moderate", "Strong"]
        )
        
        chain_quality = st.select_slider(
            "Chain of Custody Quality",
            options=["None", "Weak", "Moderate", "Good"]
        )
        
        st.markdown("---")
        
        dying_declaration = st.radio("Dying Declaration", ["Yes", "No"], horizontal=True)
        confession = st.radio("Confession Present", ["Yes", "No"], horizontal=True)
        
        st.markdown("---")
        st.subheader("📄 Case Summary")
        
        case_description = st.text_area(
            "Brief Description (optional)",
            placeholder="Enter key facts of the case...",
            height=150
        )
    
    st.markdown("---")
    
    # Predict button
    predict_btn = st.button("🔮 PREDICT APPEAL OUTCOME", type="primary")
    
    if predict_btn:
        with st.spinner('🤖 AI Model is analyzing the case...'):
            # Create feature dictionary
            features = {}
            
            # Ground-of-appeal features
            features['gnd_contradictions'] = 1 if gnd_contradictions else 0
            features['gnd_chain'] = 1 if gnd_chain else 0
            features['gnd_identification'] = 1 if gnd_identification else 0
            features['gnd_medical'] = 1 if gnd_medical else 0
            features['gnd_misdirection'] = 1 if gnd_misdirection else 0
            features['gnd_procedural'] = 1 if gnd_procedural else 0
            features['gnd_sentence'] = 1 if gnd_sentence else 0
            features['gnd_circumstantial'] = 1 if gnd_circumstantial else 0
            
            # Evidence features
            features['eyewitness'] = 1 if eyewitness == "Yes" else 0
            features['expert_evidence'] = 1 if expert_evidence == "Yes" else 0
            features['forensic'] = 1 if forensic == "Yes" else 0
            features['dying_declaration'] = 1 if dying_declaration == "Yes" else 0
            features['confession'] = 1 if confession == "Yes" else 0
            
            # Numeric features
            features['appeal_duration'] = appeal_duration
            features['total_grounds'] = sum([gnd_contradictions, gnd_chain, gnd_identification,
                                           gnd_medical, gnd_misdirection, gnd_procedural,
                                           gnd_sentence, gnd_circumstantial])
            
            # Evidence scores
            medical_scores = {"None": 0, "Weak": 1, "Moderate": 2, "Strong": 3}
            custody_scores = {"None": 0, "Weak": 1, "Moderate": 2, "Good": 3}
            
            features['medical_score'] = medical_scores[medical_strength]
            features['custody_score'] = custody_scores[chain_quality]
            
            # Fill remaining features with zeros (to match 150 features)
            for i in range(len(features), 150):
                features[f'feat_{i}'] = 0.0
            
            # Create DataFrame
            input_df = pd.DataFrame([features])
            
            try:
                # Apply feature selection if exists
                if selected_features is not None:
                    # Ensure we have all required features
                    for feat in selected_features:
                        if feat not in input_df.columns:
                            input_df[feat] = 0.0
                    input_df = input_df[selected_features]
                
                # Scale if scaler exists
                if scaler is not None:
                    input_scaled = scaler.transform(input_df)
                else:
                    input_scaled = input_df.values
                
                # Make prediction
                probabilities = model.predict_proba(input_scaled)[0]
                prediction = model.predict(input_scaled)[0]
                
                # Decode label
                if label_encoder is not None:
                    prediction_label = label_encoder.inverse_transform([prediction])[0]
                    class_labels = list(label_encoder.classes_)
                else:
                    class_labels = ['Appeal Allowed', 'Appeal Dismissed', 'Partly Allowed']
                    prediction_label = class_labels[prediction]
                
                # Display results
                
                # Main prediction box
                outcome_colors = {
                    'Appeal Allowed': '#2ca02c',
                    'Appeal Dismissed': '#d62728',
                    'Partly Allowed': '#ff7f0e'
                }
                
                outcome_color = outcome_colors.get(prediction_label, '#1f77b4')
                
                st.markdown(f"""
                <div class="prediction-box">
                    <h2 style="color: #1f77b4; margin-bottom: 15px;">🎯 Predicted Outcome</h2>
                    <h1 style="color: {outcome_color}; font-size: 52px; margin: 20px 0; text-align: center;">
                        {prediction_label}
                    </h1>
                    <p style="font-size: 20px; text-align: center; color: #666;">
                        Confidence: <strong>{probabilities[prediction]*100:.1f}%</strong>
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Probability breakdown
                st.subheader("📊 Probability Breakdown")
                
                cols = st.columns(3)
                
                for idx, (label, prob) in enumerate(zip(class_labels, probabilities)):
                    with cols[idx]:
                        delta = f"+{prob*100 - 33.3:.1f}%" if prob > 0.33 else f"{prob*100 - 33.3:.1f}%"
                        st.metric(
                            label=label,
                            value=f"{prob*100:.1f}%",
                            delta=delta
                        )
                
                # Bar chart
                st.markdown("---")
                
                prob_df = pd.DataFrame({
                    'Outcome': class_labels,
                    'Probability': probabilities * 100
                })
                
                st.bar_chart(prob_df.set_index('Outcome'))
                
                # Key factors
                st.markdown("---")
                st.subheader("🔑 Key Factors Analysis")
                
                col_fav, col_unfav = st.columns(2)
                
                with col_fav:
                    st.markdown("**✅ Favorable Factors:**")
                    favorable = []
                    
                    if gnd_misdirection:
                        favorable.append("• Misdirection on law claimed")
                    if gnd_contradictions:
                        favorable.append("• Prosecution contradictions noted")
                    if medical_strength in ["Weak", "None"]:
                        favorable.append("• Weak medical evidence")
                    if chain_quality in ["Weak", "None"]:
                        favorable.append("• Poor chain of custody")
                    if features['total_grounds'] >= 3:
                        favorable.append("• Multiple strong grounds raised")
                    
                    if favorable:
                        for f in favorable:
                            st.write(f)
                    else:
                        st.info("No significant favorable factors")
                
                with col_unfav:
                    st.markdown("**❌ Unfavorable Factors:**")
                    unfavorable = []
                    
                    if eyewitness == "Yes":
                        unfavorable.append("• Eyewitness testimony present")
                    if expert_evidence == "Yes":
                        unfavorable.append("• Expert evidence available")
                    if medical_strength == "Strong":
                        unfavorable.append("• Strong medical evidence")
                    if chain_quality == "Good":
                        unfavorable.append("• Good chain of custody")
                    if confession == "Yes":
                        unfavorable.append("• Confession on record")
                    
                    if unfavorable:
                        for f in unfavorable:
                            st.write(f)
                    else:
                        st.info("No significant unfavorable factors")
                
            except Exception as e:
                st.error(f"❌ Prediction Error: {str(e)}")
                st.write("**Debug Info:**")
                st.write(f"- Features created: {len(features)}")
                st.write(f"- Model type: {type(model)}")
                if selected_features:
                    st.write(f"- Selected features: {len(selected_features)}")

with tab2:
    st.header("📊 Model Performance Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Overall Accuracy", "62.55%", delta="+3.59%")
    with col2:
        st.metric("Training Samples", "1,000")
    with col3:
        st.metric("Features", "150")
    with col4:
        st.metric("Model", "XGBoost")
    
    st.markdown("---")
    
    st.subheader("📈 Class-wise Performance")
    
    perf_data = {
        'Outcome': ['Appeal Allowed', 'Appeal Dismissed', 'Partly Allowed'],
        'Recall (%)': [67.8, 79.4, 37.1],
        'Precision (%)': [65.2, 63.8, 52.0]
    }
    
    perf_df = pd.DataFrame(perf_data)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.dataframe(perf_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.info("**Best Performance:**\n\nAppeal Dismissed\n(79.4% recall)")
    
    st.markdown("---")
    
    st.subheader("🔧 Model Details")
    
    st.markdown("""
    **Algorithm:** XGBoost with Custom Class Weights
    
    **Feature Engineering:**
    - BERT embeddings (768 dimensions)
    - Feature selection (top 150 features)
    - Ground-of-appeal indicators
    - Evidence quality metrics
    - Case characteristics
    
    **Class Imbalance Handling:**
    - Custom class weights applied
    - PartlyAllowed weight: 2.0x
    - SMOTE alternatives tested
    
    **Training Details:**
    - Train-test split: 80-20 (stratified)
    - Baseline (Week 6): 58.96%
    - Current (Week 7): 62.55%
    - **Improvement: +3.59%**
    """)

with tab3:
    st.header("ℹ️ User Guide")
    
    st.markdown("""
    ### 🚀 How to Use This System
    
    #### Step 1: Enter Basic Information
    - Select the **offense category** from the dropdown
    - Provide **High Court sentence** details
    - Adjust the **appeal duration** slider
    
    #### Step 2: Select Grounds of Appeal
    Check all applicable grounds being raised:
    - **Contradictions:** Inconsistencies in prosecution evidence
    - **Chain of custody:** Evidence handling issues
    - **Wrong ID:** Identification challenges
    - **Medical issues:** Medical evidence problems
    - **Misdirection:** Judge's legal errors
    - **Procedural error:** Court procedure violations
    - **Sentence issue:** Disproportionate sentencing
    - **Weak evidence:** Insufficient circumstantial evidence
    
    #### Step 3: Evidence Assessment
    - Indicate presence of **eyewitness**, **expert**, and **forensic** evidence
    - Rate the **strength** of medical evidence
    - Assess **chain of custody quality**
    - Note if **dying declaration** or **confession** exists
    
    #### Step 4: Add Description (Optional)
    - Provide a brief summary of key case facts
    - Mention critical evidence points
    - Note any unique circumstances
    
    #### Step 5: Get Prediction
    - Click **"PREDICT APPEAL OUTCOME"**
    - Review probability breakdown
    - Consider key factors highlighted
    - Use results to inform legal strategy
    
    ---
    
    ### ⚠️ Important Disclaimers
    
    1. **Decision Support Tool:** This system provides predictions to **assist** legal professionals, not replace them.
    
    2. **Not Legal Advice:** Output should not be considered formal legal advice.
    
    3. **Accuracy Limitations:** Model accuracy is 62.55% based on training data. Individual cases may vary.
    
    4. **Historical Data:** Based on past Sri Lankan Court of Appeal cases. Legal standards may evolve.
    
    5. **Professional Consultation:** Always consult qualified legal professionals for case strategy.
    
    ---
    
    ### 📞 Contact & Support
    
    For questions, feedback, or technical issues, please contact the research team.
    
    **Version:** 1.0  
    **Last Updated:** January 2026  
    **Institution:** [Your University Name]
    """)

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #888; padding: 15px; font-size: 14px;">'
    '⚖️ Sri Lankan Court of Appeal Decision Support System<br/>'
    'Powered by AI/ML Research | © 2026 | Version 1.0'
    '</div>',
    unsafe_allow_html=True
)
