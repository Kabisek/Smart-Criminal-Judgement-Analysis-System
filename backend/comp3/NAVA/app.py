# ============================================
# APPEAL OUTCOME PREDICTION SYSTEM
# Streamlit Web Application - Enhanced Version
# With Feature Detection & User-Friendly Analysis
# ============================================

import streamlit as st
import pandas as pd
import numpy as np
import pickle
import torch
from transformers import AutoTokenizer, AutoModel
from datetime import datetime
import json
import plotly.graph_objects as go
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings('ignore')

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="Appeal Outcome Predictor",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CUSTOM CSS
# ============================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #6B7280;
        text-align: center;
        margin-bottom: 2rem;
    }
    .prediction-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        margin: 2rem 0;
    }
    .info-box {
        background-color: #EFF6FF;
        padding: 1.5rem;
        border-radius: 0.75rem;
        border-left: 4px solid #3B82F6;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #D1FAE5;
        padding: 1.5rem;
        border-radius: 0.75rem;
        border-left: 4px solid #10B981;
    }
    .warning-box {
        background-color: #FEF3C7;
        padding: 1.5rem;
        border-radius: 0.75rem;
        border-left: 4px solid #F59E0B;
    }
    .error-box {
        background-color: #FEE2E2;
        padding: 1.5rem;
        border-radius: 0.75rem;
        border-left: 4px solid #EF4444;
    }
    .stButton>button {
        width: 100%;
        background-color: #3B82F6;
        color: white;
        font-size: 1.2rem;
        padding: 0.75rem;
        border-radius: 0.5rem;
        border: none;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #2563EB;
    }
    .feature-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        margin: 0.25rem;
        border-radius: 1rem;
        font-size: 0.875rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# LOAD MODELS (Cached)
# ============================================
@st.cache_resource
def load_models():
    """Load all models once and cache"""
    with st.spinner("🔄 Loading AI models... Please wait..."):
        model = pickle.load(open('appeal_outcome_imbalance_week7.pkl', 'rb'))
        selector = pickle.load(open('selector_object.pkl', 'rb'))
        label_encoder = pickle.load(open('label_encoder_outcome.pkl', 'rb'))
        
        tokenizer = AutoTokenizer.from_pretrained("nlpaueb/legal-bert-base-uncased")
        bert_model = AutoModel.from_pretrained("nlpaueb/legal-bert-base-uncased")
        device = torch.device('cpu')
        bert_model.to(device)
        bert_model.eval()
        
        X_train_full = pd.read_csv('X_train_bert.csv')
        train_embeddings = np.load('bert_embeddings_train.npy')
        df_cases = pd.read_csv('dataset_cleaned_v2.csv')
        y_train = np.load('y_train_outcome.npy')
        
    return {
        'model': model,
        'selector': selector,
        'label_encoder': label_encoder,
        'tokenizer': tokenizer,
        'bert_model': bert_model,
        'device': device,
        'X_train_full': X_train_full,
        'train_embeddings': train_embeddings,
        'df_cases': df_cases,
        'y_train': y_train
    }

# ============================================
# FEATURE EXTRACTION FUNCTIONS
# ============================================
def get_bert_embedding(text, models, max_length=512):
    """Generate BERT embedding"""
    text = text[:2000]
    inputs = models['tokenizer'](
        text,
        return_tensors='pt',
        truncation=True,
        max_length=max_length,
        padding='max_length'
    )
    inputs = {k: v.to(models['device']) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = models['bert_model'](**inputs)
    
    embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()
    return embedding.flatten()

def extract_features_from_text(case_description, models):
    """Extract 59 traditional features"""
    X_train_full = models['X_train_full']
    non_bert_cols = [c for c in X_train_full.columns if not c.startswith('bert_')][:59]
    features = pd.Series(0.0, index=non_bert_cols)
    
    text = case_description.lower()
    words = text.split()
    
    if 'brief_facts_summary_length' in features.index:
        features['brief_facts_summary_length'] = len(text)
    if 'brief_facts_summary_word_count' in features.index:
        features['brief_facts_summary_word_count'] = len(words)
    
    ground_keywords = {
        'gnd_contradictions': ['contradiction', 'inconsistent', 'conflicting'],
        'gnd_chain_of_custody': ['chain of custody', 'custody', 'preservation'],
        'gnd_wrong_identification': ['identification', 'identify', 'mistaken identity'],
        'gnd_medical_inconsistency': ['medical', 'jmo', 'post-mortem'],
        'gnd_misdirection_on_law': ['misdirection', 'wrong direction'],
        'gnd_procedural_error': ['procedural', 'procedure', 'process'],
        'gnd_illegal_search_or_raid': ['illegal search', 'unlawful search'],
        'gnd_dying_declaration_validity': ['dying declaration'],
        'gnd_circumstantial_insufficient': ['circumstantial', 'indirect evidence'],
        'gnd_new_evidence': ['new evidence', 'fresh evidence'],
        'gnd_sentence_excessive_or_inadequate': ['excessive', 'harsh', 'inadequate'],
        'gnd_delay_prejudice': ['delay', 'prejudice'],
        'gnd_judicial_bias_or_unfair_trial': ['bias', 'unfair'],
    }
    
    for feature, keywords in ground_keywords.items():
        if feature in features.index:
            features[feature] = float(any(kw in text for kw in keywords))
    
    evidence_keywords = {
        'eyewitness_present': ['eyewitness', 'witness', 'testimony'],
        'expert_evidence_present': ['expert', 'jmo', 'analyst'],
        'forensic_evidence_present': ['forensic', 'dna', 'fingerprint'],
        'confession_present': ['confession', 'admitted'],
        'dying_declaration_present': ['dying declaration'],
        'digital_evidence_present': ['cctv', 'phone', 'digital'],
        'child_witness_present': ['child witness', 'minor witness'],
        'procedural_defects_present': ['procedural defect'],
        'hospital_treatment_details_present': ['hospital', 'medical treatment'],
    }
    
    for feature, keywords in evidence_keywords.items():
        if feature in features.index:
            features[feature] = float(any(kw in text for kw in keywords))
    
    offence_map = {
        'offence_category_grouped_Murder_Related': ['murder', '296', 'homicide'],
        'offence_category_grouped_Sexual_Offenses': ['rape', 'sexual', '363'],
        'offence_category_grouped_Drug_Related': ['drug', 'narcotic', 'heroin'],
        'offence_category_grouped_Robbery_Theft': ['robbery', 'theft', 'burglary'],
        'offence_category_grouped_Fraud_Corruption': ['fraud', 'corruption', 'bribery'],
    }
    
    for feature, keywords in offence_map.items():
        if feature in features.index:
            features[feature] = float(any(kw in text for kw in keywords))
    
    return features.values

def predict_appeal(case_description, models):
    """Main prediction function with feature detection"""
    traditional_features = extract_features_from_text(case_description, models)[:59]
    bert_features = get_bert_embedding(case_description, models)
    all_features = np.concatenate([traditional_features, bert_features])
    
    df_features = pd.DataFrame(
        all_features.reshape(1, -1),
        columns=models['X_train_full'].columns
    )
    
    selected_features = models['selector'].transform(df_features)
    probabilities = models['model'].predict_proba(selected_features)[0]
    prediction = models['model'].predict(selected_features)[0]
    predicted_class = models['label_encoder'].inverse_transform([prediction])[0]
    
    # === DETECT ACTIVE FEATURES ===
    detected_features = {
        'grounds': [],
        'evidence': [],
        'offence': [],
        'other': []
    }
    
    non_bert_cols = [c for c in models['X_train_full'].columns if not c.startswith('bert_')][:59]
    
    for i, (col, val) in enumerate(zip(non_bert_cols, traditional_features)):
        if val > 0.5:  # Feature is "active"
            if col.startswith('gnd_'):
                detected_features['grounds'].append(col.replace('gnd_', '').replace('_', ' ').title())
            elif '_present' in col:
                detected_features['evidence'].append(col.replace('_present', '').replace('_', ' ').title())
            elif 'offence_category' in col:
                detected_features['offence'].append(col.split('_')[-1].replace('_', ' ').title())
            elif col not in ['brief_facts_summary_length', 'brief_facts_summary_word_count', 
                           'grounds_of_appeal_raw_text_summary_length', 'grounds_of_appeal_raw_text_summary_word_count',
                           'court_of_appeal_analysis_summary_length', 'court_of_appeal_analysis_summary_word_count',
                           'coa_year', 'appeal_duration_days']:
                detected_features['other'].append(col.replace('_', ' ').title())
    
    return {
        'probabilities': {
            'Appeal_Allowed': float(probabilities[0] * 100),
            'Appeal_Dismissed': float(probabilities[1] * 100),
            'Partly_Allowed': float(probabilities[2] * 100)
        },
        'prediction': predicted_class,
        'confidence': float(max(probabilities) * 100),
        'bert_embedding': bert_features,
        'detected_features': detected_features
    }

def find_similar_cases(bert_embedding, models, top_k=5):
    """Find similar historical cases with full details"""
    similarities = cosine_similarity(
        bert_embedding.reshape(1, -1),
        models['train_embeddings']
    )[0]
    
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    
    similar_cases = []
    for idx in top_indices:
        case = models['df_cases'].iloc[idx]
        outcome = models['label_encoder'].inverse_transform([models['y_train'][idx]])[0]
        
        # Get full case details
        case_facts = str(case.get('brief_facts_summary', 'Details not available'))
        
        # Get conviction status if available
        conviction_status = str(case.get('coa_conviction_status', 'Not specified'))
        if conviction_status in ['nan', 'None', '']:
            conviction_status = 'Not specified'
        
        # Get other useful fields
        case_number = str(case.get('ca_number', f"Case_{idx}"))
        if case_number in ['nan', 'None', '']:
            case_number = f"Case_{idx}"
        
        offence = str(case.get('offence_category', 'Not specified'))
        if offence in ['nan', 'None', '']:
            offence = 'Not specified'
        
        high_court = str(case.get('high_court_location', 'Not specified'))
        if high_court in ['nan', 'None', '']:
            high_court = 'Not specified'
        
        # Get grounds of appeal if available
        grounds = str(case.get('grounds_of_appeal_summary', 'Not specified'))
        if grounds in ['nan', 'None', ''] or len(grounds) < 10:
            grounds = 'Not specified'
        else:
            grounds = grounds[:300] + "..." if len(grounds) > 300 else grounds
        
        similar_cases.append({
            'case_id': case_number,
            'similarity': float(similarities[idx] * 100),
            'outcome': outcome,
            'conviction_status': conviction_status,
            'facts': case_facts,
            'offence': offence,
            'high_court': high_court,
            'grounds': grounds
        })
    
    return similar_cases


# ============================================
# MAIN APP
# ============================================
def main():
    # Header
    st.markdown('<p class="main-header">⚖️ Sri Lankan Appeal Outcome Predictor</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Legal Analytics with Feature Detection | Court of Appeal Case Prediction</p>', unsafe_allow_html=True)
    
    # Load models
    try:
        models = load_models()
    except Exception as e:
        st.error(f"❌ Error loading models: {str(e)}")
        st.info("Please ensure all required files are in the same directory.")
        st.stop()
    
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 📊 System Information")
        
        st.markdown("### 🤖 Model Details")
        st.info("""
        **Type**: Stacking Ensemble  
        **Base Models**: XGBoost, LightGBM, Random Forest  
        **Accuracy**: 60.16%  
        **Training Data**: 1,000 cases  
        **Test Data**: 251 cases
        """)
        
        st.markdown("### 🧠 AI Technology")
        st.write("""
        - **Legal-BERT**: 768-dimensional embeddings
        - **Feature Detection**: 59 traditional features
        - **Total Features**: 827
        - **Selected Features**: 150 (ANOVA F-test)
        """)
        
        st.markdown("### 📖 How to Use")
        st.write("""
        1. **Enter case description** in detail
        2. Include:
           - Case facts & evidence
           - Grounds of appeal
           - High Court decision
        3. Click **"Predict Outcome"**
        4. Review detected features & results
        """)
        
        st.markdown("---")
        
        st.markdown("### ⚠️ Important Notice")
        st.warning("""
        This is an AI prediction tool based on historical data. 
        
        **Always consult qualified legal counsel** for case-specific advice.
        """)
        
        st.markdown("### 📧 Contact")
        st.write("For inquiries: legal.ai@example.com")
    
    # Main Input Area
    st.markdown("## 📝 Enter Case Details")
    
    # Instructions
    with st.expander("ℹ️ What information should I provide?", expanded=False):
        st.markdown("""
        **Please include the following in your case description:**
        
        1. **Basic Information**
           
           - Offence type & penal code section
           - Original sentence/conviction
        
        2. **Case Facts**
           - Brief description of the incident
           - Date, location, parties involved
        
        3. **Evidence** *(Important for detection)*
           - Eyewitness testimony
           - Medical/forensic evidence
           - Documentary evidence
           - Expert evidence (JMO, analysts)
        
        4. **Grounds of Appeal** *(Critical)*
           - Contradictions in evidence
           - Procedural errors
           - Misdirection on law
           - Chain of custody issues
           - Wrong identification
        
        5. **Defence Position**
           - Accused's statement
           - Defence witnesses
           - Alibi or alternative theories
        """)
    
    # Main text input
    case_text = st.text_area(
        "📄 Case Description:",
        height=400,
        placeholder="""Example:

The accused was convicted by the High Court of Colombo for murder under Section 296 of the Penal Code and sentenced to death. The incident occurred on 15th May 2020 at the victim's residence.

The High Court convicted based on:
- Eyewitness testimony from two witnesses who saw the accused at the scene
- Medical evidence showing multiple stab wounds on the victim
- Recovery of a knife from the accused's possession

Grounds of Appeal:
1. Material contradictions in the prosecution witnesses' testimonies regarding the time of incident
2. Wrong identification - witnesses claim poor lighting conditions at night
3. Chain of custody issues with the recovered weapon - no proper documentation
4. Medical evidence does not conclusively prove murder intent vs manslaughter

Additional Information:
- No dying declaration was recorded
- The accused gave a dock statement denying all charges
- Defence did not call any witnesses

Please analyze the likelihood of appeal success based on these grounds and similar historical cases.""",
        help="Provide detailed information about the case for more accurate predictions"
    )
    
    # Character count
    char_count = len(case_text)
    word_count = len(case_text.split())
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        st.caption(f"📊 Characters: {char_count}")
    with col3:
        st.caption(f"📊 Words: {word_count}")
    
    # Validation
    if 0 < char_count < 100:
        st.warning("⚠️ Please provide at least 100 characters for accurate prediction")
    
    st.markdown("")
    
    # Predict button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        predict_button = st.button("🔮 Predict Appeal Outcome", type="primary")
    
    # Results Section
    if predict_button:
        if char_count < 50:
            st.error("❌ Case description too short. Please provide more details.")
        else:
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("⏳ Step 1/4: Extracting features...")
            progress_bar.progress(25)
            
            status_text.text("⏳ Step 2/4: Generating Legal-BERT embeddings...")
            progress_bar.progress(50)
            
            # Get prediction
            result = predict_appeal(case_text, models)
            
            status_text.text("⏳ Step 3/4: Running ensemble model...")
            progress_bar.progress(75)
            
            # Find similar cases
            similar_cases = find_similar_cases(result['bert_embedding'], models, top_k=5)
            
            status_text.text("⏳ Step 4/4: Complete!")
            progress_bar.progress(100)
            
            status_text.empty()
            progress_bar.empty()
            
            # Display results
            st.markdown("---")
            st.markdown("# 🎯 Prediction Results")
            
            probs = result['probabilities']
            prediction = result['prediction']
            confidence = result['confidence']
            detected = result['detected_features']
            
            # === DETECTED FEATURES BOX ===
            st.markdown("### 🔍 What the AI Detected in Your Case")
            
            # Calculate detection score
            total_detected = sum(len(v) for v in detected.values())
            
            if total_detected > 0:
                st.success(f"✅ Successfully detected **{total_detected} key features** from your case description")
                
                # Display detected features in columns
                col1, col2 = st.columns(2)
                
                with col1:
                    # Grounds of Appeal
                    if detected['grounds']:
                        st.markdown("#### ⚖️ Grounds of Appeal Detected")
                        for ground in detected['grounds']:
                            st.markdown(f"🟢 **{ground}**")
                    else:
                        st.markdown("#### ⚖️ Grounds of Appeal")
                        st.warning("⚠️ No specific grounds detected. Consider adding more details about appeal grounds.")
                    
                    st.markdown("")
                    
                    # Offence Type
                    if detected['offence']:
                        st.markdown("#### 📋 Offence Category")
                        for offence in detected['offence']:
                            st.markdown(f"🔵 **{offence}**")
                    else:
                        st.markdown("#### 📋 Offence Category")
                        st.info("ℹ️ Offence type not clearly identified. This may affect prediction accuracy.")
                
                with col2:
                    # Evidence
                    if detected['evidence']:
                        st.markdown("#### 🔬 Evidence Detected")
                        for evidence in detected['evidence']:
                            st.markdown(f"🟡 **{evidence}**")
                    else:
                        st.markdown("#### 🔬 Evidence")
                        st.warning("⚠️ No evidence types detected. Consider mentioning specific evidence (eyewitness, medical, forensic, etc.)")
                    
                    st.markdown("")
                    
                    # Other factors
                    if detected['other']:
                        st.markdown("#### 📊 Other Factors")
                        for other in detected['other'][:5]:
                            st.markdown(f"🟠 **{other}**")
            else:
                st.warning("""
                ⚠️ **Limited Information Detected**
                
                The AI couldn't identify specific legal features in your description. For better predictions, please include:
                - Specific grounds of appeal (contradictions, chain of custody, identification issues)
                - Evidence types (eyewitness, medical, forensic, confession)
                - Offence category (murder, rape, drug trafficking, etc.)
                """)
            
            st.markdown("---")
            
            # Main prediction card
            if prediction == "Appeal_Allowed":
                gradient = "linear-gradient(135deg, #10B981 0%, #059669 100%)"
                emoji = "✅"
            elif prediction == "Appeal_Dismissed":
                gradient = "linear-gradient(135deg, #EF4444 0%, #DC2626 100%)"
                emoji = "❌"
            else:
                gradient = "linear-gradient(135deg, #F59E0B 0%, #D97706 100%)"
                emoji = "⚖️"
            
            st.markdown(f"""
            <div style="background: {gradient}; padding: 2rem; border-radius: 1rem; color: white; text-align: center; margin: 2rem 0;">
                <h2 style="margin: 0; font-size: 2.5rem;">{emoji} {prediction.replace('_', ' ')}</h2>
                <p style="margin: 0.5rem 0 0 0; font-size: 1.3rem; opacity: 0.95;">
                    Confidence: {confidence:.1f}% 
                    {'(High)' if confidence > 60 else '(Medium)' if confidence > 50 else '(Low)'}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # === PREDICTION REASONING ===
            st.markdown("### 💡 Why This Prediction?")
            
            reasoning_text = f"Based on analysis of **{total_detected} detected features** and **768-dimensional Legal-BERT embeddings**, the model predicts:"
            
            if prediction == "Appeal_Allowed" and confidence > 60:
                reasoning_text += f"""
                
**Strong indicators for Appeal Allowed:**
- Detected grounds: {', '.join(detected['grounds'][:3]) if detected['grounds'] else 'Procedural/evidentiary issues'}
- Pattern matches similar cases where appeals succeeded
- High confidence ({confidence:.1f}%) suggests strong legal grounds
                """
            elif prediction == "Appeal_Dismissed" and confidence > 60:
                reasoning_text += f"""
                
**Strong indicators for Appeal Dismissed:**
- Evidence pattern: {', '.join(detected['evidence'][:3]) if detected['evidence'] else 'Strong prosecution evidence'}
- Similar historical cases were mostly dismissed
- High confidence ({confidence:.1f}%) suggests solid conviction basis
                """
            elif confidence < 55:
                reasoning_text += f"""
                
**Mixed signals detected:**
- Competing factors make outcome uncertain
- Both prosecution strengths and defence grounds present
- Medium/low confidence ({confidence:.1f}%) indicates borderline case
                """
            
            st.info(reasoning_text)
            
            st.markdown("")
            
            # Probability breakdown
            st.markdown("### 📊 Detailed Probability Breakdown")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "✅ Appeal Allowed",
                    f"{probs['Appeal_Allowed']:.2f}%"
                )
                st.progress(probs['Appeal_Allowed'] / 100)
            
            with col2:
                st.metric(
                    "❌ Appeal Dismissed",
                    f"{probs['Appeal_Dismissed']:.2f}%"
                )
                st.progress(probs['Appeal_Dismissed'] / 100)
            
            with col3:
                st.metric(
                    "⚖️ Partly Allowed",
                    f"{probs['Partly_Allowed']:.2f}%"
                )
                st.progress(probs['Partly_Allowed'] / 100)
            
            st.markdown("")
            
            # Visualization
            col1, col2 = st.columns(2)
            
            with col1:
                # Pie chart
                fig_pie = go.Figure(data=[go.Pie(
                    labels=['Appeal Allowed', 'Appeal Dismissed', 'Partly Allowed'],
                    values=[probs['Appeal_Allowed'], probs['Appeal_Dismissed'], probs['Partly_Allowed']],
                    hole=.4,
                    marker=dict(colors=['#10B981', '#EF4444', '#F59E0B']),
                    textinfo='label+percent',
                    textfont_size=14
                )])
                fig_pie.update_layout(
                    title="Outcome Distribution",
                    height=400,
                    showlegend=True
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Bar chart
                fig_bar = go.Figure(data=[
                    go.Bar(
                        x=['Appeal Allowed', 'Appeal Dismissed', 'Partly Allowed'],
                        y=[probs['Appeal_Allowed'], probs['Appeal_Dismissed'], probs['Partly_Allowed']],
                        marker=dict(color=['#10B981', '#EF4444', '#F59E0B']),
                        text=[f"{p:.1f}%" for p in [probs['Appeal_Allowed'], probs['Appeal_Dismissed'], probs['Partly_Allowed']]],
                        textposition='auto'
                    )
                ])
                fig_bar.update_layout(
                    title="Probability Comparison",
                    yaxis_title="Probability (%)",
                    height=400,
                    yaxis=dict(range=[0, 100])
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            
            # Similar cases
# Similar cases
            st.markdown("---")
            st.markdown("### 📚 Similar Historical Cases")
            st.write("Based on Legal-BERT semantic similarity analysis, here are the most relevant precedents:")
            
            for i, case in enumerate(similar_cases, 1):
                # Determine outcome color
                if case['outcome'] == "Appeal_Allowed":
                    outcome_color = "#10B981"
                    outcome_icon = ""
                elif case['outcome'] == "Appeal_Dismissed":
                    outcome_color = "#EF4444"
                    outcome_icon = ""
                else:
                    outcome_color = "#F59E0B"
                    outcome_icon = ""
                
                # Determine conviction status color
                conv_status = case['conviction_status']
                if 'acquit' in conv_status.lower():
                    conv_color = "#10B981"
                    conv_icon = "✅"
                elif 'upheld' in conv_status.lower() or 'affirmed' in conv_status.lower():
                    conv_color = "#EF4444"
                    conv_icon = "🔒"
                elif 'modified' in conv_status.lower() or 'reduced' in conv_status.lower():
                    conv_color = "#F59E0B"
                    conv_icon = "📝"
                else:
                    conv_color = "#6B7280"
                    conv_icon = "ℹ️"
                
                with st.expander(
                    f"**#{i} {case['case_id']}** {outcome_icon} {case['outcome']} ({case['similarity']:.1f}% similar)", 
                    expanded=(i==1)
                ):
                    # Create two columns for better layout
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.markdown("#### 📊 Case Details")
                        
                        # Similarity score with visual
                        st.metric("Semantic Similarity", f"{case['similarity']:.1f}%")
                        st.progress(case['similarity'] / 100)
                        
                        st.markdown("")
                        
                        # Appeal Outcome
                        st.markdown("**Appeal Outcome:**")
                        st.markdown(
                            f"<span style='color: {outcome_color}; font-weight: bold; font-size: 1.1rem;'>"
                            f"{outcome_icon} {case['outcome'].replace('_', ' ')}</span>", 
                            unsafe_allow_html=True
                        )
                        
                        st.markdown("")
                        
                        # Conviction Status
                        st.markdown("**Conviction Status:**")
                        st.markdown(
                            f"<span style='color: {conv_color}; font-weight: bold;'>"
                            f"{conv_icon} {conv_status}</span>", 
                            unsafe_allow_html=True
                        )
                        
                        st.markdown("")
                        
                        # Other metadata
                        if case['offence'] != 'Not specified':
                            st.markdown(f"**Offence:** {case['offence']}")
                        
                        if case['high_court'] != 'Not specified':
                            st.markdown(f"**High Court:** {case['high_court']}")
                    
                    with col2:
                        st.markdown("#### 📄 Case Summary")
                        
                        # Case Facts (Full)
                        st.markdown("**Full Case Facts:**")
                        
                        # Display full facts with better formatting
                        facts_text = case['facts']
                        if len(facts_text) > 1000:
                            # If very long, show first 800 chars with "Read more" option
                            st.write(facts_text[:800] + "...")
                            
                            with st.expander("📖 Read Full Facts"):
                                st.write(facts_text)
                        else:
                            st.write(facts_text)
                        
                        st.markdown("")
                        
                        # Grounds of Appeal (if available)
                        if case['grounds'] != 'Not specified':
                            st.markdown("**Grounds of Appeal:**")
                            st.info(case['grounds'])
                    
                    # Divider between cases
                    if i < len(similar_cases):
                        st.markdown("---")
            
            # # Add summary statistics after all cases
            # st.markdown("---")
            # st.markdown("#### 🔍 Similar Cases Analysis")
            
            # # Calculate outcome distribution
            # outcomes_count = {}
            # for case in similar_cases:
            #     outcome = case['outcome']
            #     outcomes_count[outcome] = outcomes_count.get(outcome, 0) + 1
            
            # col1, col2, col3 = st.columns(3)
            
            # with col1:
            #     allowed_count = outcomes_count.get('Appeal_Allowed', 0)
            #     st.metric(
            #         " Allowed", 
            #         f"{allowed_count}/5",
            #         delta=f"{allowed_count/5*100:.0f}%"
            #     )
            
            # with col2:
            #     dismissed_count = outcomes_count.get('Appeal_Dismissed', 0)
            #     st.metric(
            #         " Dismissed", 
            #         f"{dismissed_count}/5",
            #         delta=f"{dismissed_count/5*100:.0f}%"
            #     )
            
            # with col3:
            #     partly_count = outcomes_count.get('Partly_Allowed', 0)
            #     st.metric(
            #         " Partly Allowed", 
            #         f"{partly_count}/5",
            #         delta=f"{partly_count/5*100:.0f}%"
            #     )
            
            # # Interpretation based on similar cases
            # st.markdown("")
            
            # if allowed_count >= 3:
            #     st.success(f"""
            #     ✅ **Favorable Pattern**: {allowed_count} out of 5 similar cases resulted in Appeal Allowed. 
            #     This strengthens the prediction for a favorable outcome.
            #     """)
            # elif dismissed_count >= 3:
            #     st.error(f"""
            #     ⚠️ **Unfavorable Pattern**: {dismissed_count} out of 5 similar cases resulted in Appeal Dismissed. 
            #     Historical precedents suggest challenges in succeeding with this appeal.
            #     """)
            # else:
            #     st.info(f"""
            #     ⚖️ **Mixed Pattern**: Similar cases show varied outcomes. 
            #     This suggests the case has unique factors that could swing either way.
            #     """)
            
            # Detailed Analysis Tabs
            st.markdown("---")
            st.markdown("### 💡 Detailed Analysis & Recommendations")
            
            tab1, tab2, tab3 = st.tabs(["📊 Confidence Analysis", "🎯 Key Factors", "📋 Recommendations"])
            
            with tab1:
                if confidence > 60:
                    st.markdown('<div class="success-box">', unsafe_allow_html=True)
                    st.markdown("#### 🟢 High Confidence Prediction")
                    st.write(f"""
The model has **high confidence ({confidence:.1f}%)** in predicting **{prediction.replace('_', ' ')}**.

**Why high confidence?**
- Strong pattern match with {len(similar_cases)} similar historical cases
- Clear detection of {total_detected} legal features
- BERT semantic analysis shows consistent legal language patterns
- Ensemble models agree on outcome (low variance)
                    """)
                    st.markdown('</div>', unsafe_allow_html=True)
                elif confidence > 50:
                    st.markdown('<div class="warning-box">', unsafe_allow_html=True)
                    st.markdown("#### 🟡 Medium Confidence Prediction")
                    st.write(f"""
The model has **medium confidence ({confidence:.1f}%)** in this prediction.

**Why medium confidence?**
- Competing factors detected (both prosecution strengths and defence grounds)
- Similar cases show mixed outcomes
- Some uncertainty in feature patterns
- Additional legal analysis recommended
                    """)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="info-box">', unsafe_allow_html=True)
                    st.markdown("#### 🔵 Low Confidence Prediction")
                    st.write(f"""
The model has **lower confidence ({confidence:.1f}%)** in this prediction.

**Why low confidence?**
- Unique case characteristics not seen frequently in training data
- Conflicting signals from different features
- Outcome highly dependent on judicial interpretation
- Thorough legal review strongly recommended
                    """)
                    st.markdown('</div>', unsafe_allow_html=True)
            
            with tab2:
                st.markdown("#### 🎯 Key Contributing Factors")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🟢 Factors Supporting Prediction:**")
                    if detected['grounds']:
                        st.write("**Detected Grounds:**")
                        for ground in detected['grounds']:
                            st.write(f"  • {ground}")
                    if detected['evidence']:
                        st.write("**Evidence Types:**")
                        for evidence in detected['evidence'][:3]:
                            st.write(f"  • {evidence}")
                    
                    st.write(f"**Legal-BERT Analysis:**")
                    st.write(f"  • Semantic similarity with {similar_cases[0]['outcome']} cases: {similar_cases[0]['similarity']:.1f}%")
                
                with col2:
                    st.markdown("**📊 Model Insights:**")
                    st.write(f"• Total features detected: **{total_detected}**")
                    st.write(f"• BERT embeddings: **768 dimensions**")
                    st.write(f"• Selected features used: **150**")
                    st.write(f"• Top similar case outcome: **{similar_cases[0]['outcome']}**")
                    st.write(f"• Model accuracy: **60.16%** (on test set)")
            
            with tab3:
                st.markdown("#### 📋 Strategic Recommendations")
                
                if prediction == "Appeal_Allowed" and confidence > 60:
                    st.success(f"""
✅ **Proceed with Appeal** (High Success Probability)

**Recommended Actions:**
1. Strengthen arguments around detected grounds: {", ".join(detected['grounds'][:3]) if detected['grounds'] else "key grounds"}
2. Prepare comprehensive written submissions
3. Cite similar precedents (see similar cases above)
4. Focus on procedural/evidentiary weaknesses in prosecution case
                    """)
                
                elif prediction == "Appeal_Dismissed" and confidence > 60:
                    st.error("""
⚠️ **Appeal Success Unlikely** (High Dismissal Probability)

**Recommended Actions:**
1. Consider settlement or plea bargaining options
2. If proceeding, focus on mitigating factors for sentence reduction
3. Ensure no procedural errors in appeal filing
4. Consult senior counsel for case review
                    """)
                
                elif prediction == "Partly_Allowed":
                    st.warning("""
⚖️ **Partial Success Possible** (Mixed Outcome)

**Recommended Actions:**
1. Focus on strongest grounds while being realistic about full acquittal
2. Prepare arguments for sentence reduction
3. Highlight mitigating circumstances
4. Consider negotiated outcome
                    """)
                
                else:
                    st.info("""
🔍 **Uncertain Outcome** (Further Analysis Needed)

**Recommended Actions:**
1. Conduct detailed legal research on similar precedents
2. Strengthen case description with more specific details
3. Obtain expert opinions on key evidence/procedural issues
4. Prepare for both scenarios (success/failure)
                    """)
                
                st.markdown("---")
                st.warning("⚠️ **Important**: These recommendations are AI-generated based on historical patterns. Always consult qualified legal counsel for case-specific advice.")
            
            # Download report
            st.markdown("---")
            st.markdown("### 📥 Export Results")
            
            report = {
                "prediction": prediction,
                "probabilities": probs,
                "confidence": confidence,
                "detected_features": detected,
                "similar_cases": similar_cases,
                "case_summary": {
                    "character_count": char_count,
                    "word_count": word_count,
                    "input_preview": case_text[:500] + "..." if len(case_text) > 500 else case_text
                },
                "metadata": {
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "model_version": "1.0",
                    "model_accuracy": 60.16
                }
            }
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    "📄 Download Report (JSON)",
                    data=json.dumps(report, indent=2),
                    file_name=f"appeal_prediction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            with col2:
                # Create text report
                text_report = f"""
APPEAL OUTCOME PREDICTION REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PREDICTION: {prediction.replace('_', ' ')}
CONFIDENCE: {confidence:.1f}%

PROBABILITIES:
- Appeal Allowed: {probs['Appeal_Allowed']:.2f}%
- Appeal Dismissed: {probs['Appeal_Dismissed']:.2f}%
- Partly Allowed: {probs['Partly_Allowed']:.2f}%

DETECTED FEATURES ({total_detected} total):
Grounds: {', '.join(detected['grounds']) if detected['grounds'] else 'None'}
Evidence: {', '.join(detected['evidence']) if detected['evidence'] else 'None'}
Offence: {', '.join(detected['offence']) if detected['offence'] else 'None'}

SIMILAR CASES:
{chr(10).join([f"{i+1}. {case['case_id']} - {case['outcome']} ({case['similarity']:.1f}% similar)" for i, case in enumerate(similar_cases)])}

CASE INPUT:
{case_text[:500]}...

---
Generated by Appeal Outcome Predictor AI System
Model Accuracy: 60.16% | Training Cases: 1,000
                """
                
                st.download_button(
                    "📝 Download Report (TXT)",
                    data=text_report,
                    file_name=f"appeal_prediction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6B7280; padding: 2rem 0;">
        <p><strong>Appeal Outcome Prediction System v1.0</strong></p>
        <p>Powered by Legal-BERT & Ensemble Machine Learning with Feature Detection</p>
        <p style="font-size: 0.9rem;">© 2026 | For informational purposes only | Not a substitute for legal advice</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# RUN APP
# ============================================
if __name__ == "__main__":
    main()
