"""
Streamlit Web Application for Criminal Judgment PDF Extraction
Main application file for the PDF extraction and CSV storage system
"""

import streamlit as st
import os
import sys
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pdf_processor import PDFProcessor
from ai_extractor import ExtractorFactory
from csv_storage import CSVStorage
from config import Config


# Page configuration
st.set_page_config(
    page_title="Criminal Judgment PDF Extractor",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if 'extracted_data' not in st.session_state:
        st.session_state.extracted_data = None
    if 'pdf_uploaded' not in st.session_state:
        st.session_state.pdf_uploaded = False
    if 'extraction_in_progress' not in st.session_state:
        st.session_state.extraction_in_progress = False


def validate_configuration():
    """Validate API configuration"""
    is_valid, message = Config.validate_api_config()
    return is_valid, message


def extract_from_pdf(pdf_file_path: str, api_type: str) -> dict:
    """
    Extract information from PDF file
    
    Args:
        pdf_file_path: Path to the PDF file
        api_type: Type of API to use
        
    Returns:
        Dictionary with extracted information
    """
    # Initialize PDF processor
    pdf_processor = PDFProcessor()
    
    # Extract text from PDF
    success, message, extracted_text = pdf_processor.extract_text(pdf_file_path)
    
    if not success:
        return {"error": message}
    
    # Get metadata
    metadata = pdf_processor.extract_metadata(pdf_file_path)
    
    # Use AI to extract information
    try:
        api_key = Config.DEEPSEEK_API_KEY if api_type == 'deepseek' else Config.GEMINI_API_KEY
        extractor = ExtractorFactory.create_extractor(api_type, api_key)
        
        st.info("🔄 Processing with AI... This may take 30-60 seconds...")
        extracted_info = extractor.extract_judgment_info(extracted_text)
        
        # Add full text to extracted info if not already present
        if 'full_text_judgment' not in extracted_info or not extracted_info['full_text_judgment']:
            extracted_info['full_text_judgment'] = extracted_text[:50000]  # Limit to 50k chars for CSV
        
        # Combine metadata with extracted info
        result = {
            'metadata': metadata,
            'extracted_info': extracted_info
        }
        
        return result
    
    except Exception as e:
        return {"error": f"AI Extraction Error: {str(e)}"}


def display_extracted_data(data: dict):
    """Display extracted information in CSV-ready format with preview"""
    if 'error' in data:
        st.error(f"❌ Error: {data['error']}")
        return
    
    # Display metadata
    metadata = data.get('metadata', {})
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📄 Total Pages", metadata.get('total_pages', 'N/A'))
    with col2:
        st.metric("💾 File Size", f"{metadata.get('file_size_mb', 'N/A')} MB")
    with col3:
        st.metric("📁 File Name", metadata.get('file_name', 'N/A')[:20] + "...")
    
    st.divider()
    
    # Display extracted information
    extracted_info = data.get('extracted_info', {})
    
    # Create tabs for organized viewing
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Case Overview", 
        "⚖️ Court Decisions", 
        "🔍 Evidence & Defence",
        "📊 CSV Preview"
    ])
    
    with tab1:
        st.subheader("🏛️ Case Identification")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Court of Appeal Case No:**")
            st.info(extracted_info.get('court_of_appeal_case_no', 'Not Found'))
            
            st.markdown("**High Court Case No:**")
            st.info(extracted_info.get('high_court_case_no', 'Not Found'))
            
            st.markdown("**High Court Location:**")
            st.info(extracted_info.get('high_court_location', 'Not Found'))
        
        with col2:
            st.markdown("**Judges:**")
            st.info(extracted_info.get('judges', 'Not Found'))
            
            st.markdown("**Offence Sections:**")
            st.info(extracted_info.get('offence_sections', 'Not Found'))
            
            st.markdown("**Offence Category:**")
            st.info(extracted_info.get('offence_category', 'Not Found'))
        
        st.divider()
        
        st.subheader("📅 Important Dates")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Date of Offence:**")
            st.success(extracted_info.get('date_of_offence', 'Not Found'))
        with col2:
            st.markdown("**HC Judgment Date:**")
            st.success(extracted_info.get('judgment_date_hc', 'Not Found'))
        with col3:
            st.markdown("**CoA Judgment Date:**")
            st.success(extracted_info.get('judgment_date_coa', 'Not Found'))
        
        st.divider()
        
        st.subheader("📝 Brief Facts Summary")
        st.text_area("Facts", extracted_info.get('brief_facts_summary', 'Not Found'), height=150, disabled=True)
    
    with tab2:
        st.subheader("⚖️ High Court Decision")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Conviction Sections:**")
            st.info(extracted_info.get('hc_offence_of_conviction_sections', 'Not Found'))
            
            st.markdown("**Sentence Type:**")
            st.warning(extracted_info.get('hc_sentence_type', 'Not Found'))
        
        with col2:
            st.markdown("**Fine Amount:**")
            st.info(f"Rs. {extracted_info.get('hc_fine_amount', 'Not Found')}")
            
            st.markdown("**Compensation Amount:**")
            st.info(f"Rs. {extracted_info.get('hc_compensation_amount', 'Not Found')}")
        
        st.markdown("**HC Judgment Summary:**")
        st.text_area("HC Summary", extracted_info.get('hc_judgment_summary', 'Not Found'), height=100, disabled=True)
        
        st.divider()
        
        st.subheader("📢 Grounds of Appeal")
        
        # Display grounds in a grid
        grounds_data = [
            ('Contradictions', 'gnd_contradictions'),
            ('Chain of Custody', 'gnd_chain_of_custody'),
            ('Illegal Search/Raid', 'gnd_illegal_search_or_raid'),
            ('Wrong Identification', 'gnd_wrong_identification'),
            ('Dying Declaration Validity', 'gnd_dying_declaration_validity'),
            ('Circumstantial Insufficient', 'gnd_circumstantial_insufficient'),
            ('Medical Inconsistency', 'gnd_medical_inconsistency'),
            ('Misdirection on Law', 'gnd_misdirection_on_law'),
            ('Procedural Error', 'gnd_procedural_error'),
            ('New Evidence', 'gnd_new_evidence'),
            ('Excessive Sentence', 'gnd_sentence_excessive_or_inadequate'),
            ('Delay Prejudice', 'gnd_delay_prejudice'),
            ('Judicial Bias', 'gnd_judicial_bias_or_unfair_trial'),
            ('Other', 'gnd_other')
        ]
        
        # Create 4 columns for grounds
        grounds_cols = st.columns(4)
        for i, (label, key) in enumerate(grounds_data):
            with grounds_cols[i % 4]:
                value = extracted_info.get(key, 'No')
                if value.lower() == 'yes':
                    st.success(f"✅ {label}")
                else:
                    st.error(f"❌ {label}")
        
        if extracted_info.get('gnd_other', '').lower() == 'yes':
            st.markdown("**Other Ground Description:**")
            st.info(extracted_info.get('gnd_other_description', 'Not specified'))
        
        st.markdown("**Grounds Summary:**")
        st.text_area("Grounds", extracted_info.get('grounds_of_appeal_raw_text_summary', 'Not Found'), height=100, disabled=True)
        
        st.divider()
        
        st.subheader("👨‍⚖️ Court of Appeal Analysis")
        st.text_area("CoA Analysis", extracted_info.get('court_of_appeal_analysis_summary', 'Not Found'), height=150, disabled=True)
        
        st.subheader("📊 Final Outcome")
        col1, col2, col3 = st.columns(3)
        with col1:
            outcome = extracted_info.get('coa_final_outcome_class', 'Not Found')
            if 'allow' in outcome.lower():
                st.success(f"**Decision:** {outcome}")
            else:
                st.error(f"**Decision:** {outcome}")
        with col2:
            st.info(f"**Conviction Status:** {extracted_info.get('coa_conviction_status', 'Not Found')}")
        with col3:
            st.warning(f"**Sentence Type:** {extracted_info.get('coa_sentence_type', 'Not Found')}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("CoA Fine Amount", f"Rs. {extracted_info.get('coa_fine_amount', 'Not Found')}")
        with col2:
            st.metric("CoA Compensation", f"Rs. {extracted_info.get('coa_compensation_amount', 'Not Found')}")
    
    with tab3:
        st.subheader("👥 Witnesses")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Prosecution Witnesses", extracted_info.get('num_prosecution_witnesses', 0))
        with col2:
            st.metric("Defence Witnesses", extracted_info.get('num_defence_witnesses', 0))
        with col3:
            eyewitness = extracted_info.get('eyewitness_present', 'No')
            st.metric("Eyewitness", "✅ Yes" if eyewitness.lower() == 'yes' else "❌ No")
        with col4:
            child = extracted_info.get('child_witness_present', 'No')
            st.metric("Child Witness", "✅ Yes" if child.lower() == 'yes' else "❌ No")
        
        st.divider()
        
        st.subheader("🔬 Evidence Quality Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Medical Evidence Strength:**")
            strength = extracted_info.get('medical_evidence_strength', 'None')
            if strength.lower() == 'strong':
                st.success(strength)
            elif strength.lower() == 'moderate':
                st.warning(strength)
            else:
                st.error(strength)
            
            st.markdown("**Chain of Custody Quality:**")
            custody = extracted_info.get('chain_of_custody_quality', 'none')
            st.info(custody.capitalize())
            
            st.markdown("**Forensic Evidence Present:**")
            forensic = extracted_info.get('forensic_evidence_present', 'No')
            st.info(forensic)
            
            st.markdown("**Expert Evidence Present:**")
            expert = extracted_info.get('expert_evidence_present', 'No')
            st.info(expert)
        
        with col2:
            st.markdown("**Dying Declaration Present:**")
            dd = extracted_info.get('dying_declaration_present', 'No')
            st.info(dd)
            
            if dd.lower() == 'yes':
                st.markdown("**Dying Declaration Reliability:**")
                reliability = extracted_info.get('dying_declaration_reliability', 'N/A')
                if reliability.lower() == 'reliable':
                    st.success(reliability)
                elif reliability.lower() == 'doubtful':
                    st.warning(reliability)
                else:
                    st.error(reliability)
            
            st.markdown("**Confession Present:**")
            confession = extracted_info.get('confession_present', 'No')
            st.info(confession)
            
            st.markdown("**Circumstantial Case:**")
            circumstantial = extracted_info.get('circumstantial_case', 'No')
            st.info(circumstantial)
        
        st.markdown("**Witness & Evidence Analysis Summary:**")
        st.text_area("Evidence Summary", extracted_info.get('witness_evidence_analysis_summary', 'Not Found'), height=100, disabled=True)
        
        st.divider()
        
        st.subheader("🛡️ Defence")
        st.text_area("Defence Version", extracted_info.get('defence_version_summary', 'Not Found'), height=120, disabled=True)
        
        st.divider()
        
        st.subheader("⚖️ Legal Analysis")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Legal Errors Identified:**")
            legal_errors = extracted_info.get('legal_errors_identified', 'No')
            if legal_errors.lower() == 'yes':
                st.error(legal_errors)
                st.markdown("**Description:**")
                st.info(extracted_info.get('legal_errors_description', 'Not Found'))
            else:
                st.success(legal_errors)
        
        with col2:
            st.markdown("**Procedural Defects Present:**")
            procedural = extracted_info.get('procedural_defects_present', 'No')
            if procedural.lower() == 'yes':
                st.error(procedural)
                st.markdown("**Description:**")
                st.info(extracted_info.get('procedural_defects_description', 'Not Found'))
            else:
                st.success(procedural)
        
        st.markdown("**Burden of Proof Directions Correct:**")
        burden = extracted_info.get('directions_on_burden_of_proof_correct', 'Not Found')
        if burden.lower() == 'yes':
            st.success(burden)
        else:
            st.error(burden)
    
    with tab4:
        st.subheader("📊 CSV Preview - All Extracted Fields")
        st.info("This shows how your data will appear in the CSV file")
        
        # Create a preview dataframe
        preview_data = {
            'Field Name': [],
            'Extracted Value': []
        }
        
        # Add all fields in order
        for key in CSVStorage.DEFAULT_COLUMNS:
            if key not in ['timestamp', 'filename']:
                preview_data['Field Name'].append(key.replace('_', ' ').title())
                value = str(extracted_info.get(key, 'Not Found'))
                # Truncate long values for preview
                if len(value) > 100:
                    value = value[:100] + "..."
                preview_data['Extracted Value'].append(value)
        
        # Display as dataframe
        df_preview = pd.DataFrame(preview_data)
        st.dataframe(df_preview, use_container_width=True, height=400)
        
        st.divider()
        
        st.info(f"📝 Total Fields to be saved: {len(preview_data['Field Name'])} + timestamp + filename")


def main():
    """Main application function"""
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.title("⚖️ Criminal Judgment PDF Extractor")
    st.markdown("**Extract structured information from Court of Appeal judgment PDFs and save to CSV**")
    
    # Validate configuration
    is_valid, config_message = validate_configuration()
    
    if not is_valid:
        st.error(f"❌ Configuration Error: {config_message}")
        st.warning("Please configure your API keys in `config/.env` file")
        st.info("""
        **Setup Instructions:**
        1. Copy `config/.env.example` to `config/.env`
        2. Add your API keys:
           - For Gemini: Get from https://ai.google.dev/
           - For Deepseek: Get from https://platform.deepseek.com/
        3. Set PRIMARY_API to 'gemini' or 'deepseek'
        4. Restart the application
        """)
        return
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        api_type = st.radio(
            "Select AI API",
            ["gemini", "deepseek"],
            index=0 if Config.PRIMARY_API == 'gemini' else 1,
            help="Choose which AI service to use for extraction"
        )
        
        st.divider()
        
        output_folder = st.text_input(
            "Output CSV Folder",
            value=Config.OUTPUT_FOLDER,
            help="Folder where CSV files will be saved"
        )
        
        csv_filename = st.text_input(
            "CSV Filename (without .csv)",
            value="judgment_extractions",
            help="Name of the CSV file to create/append to"
        )
        
        st.divider()
        
        st.subheader("📊 Existing CSV Files")
        csv_storage = CSVStorage(output_folder)
        csv_files = csv_storage.get_csv_list()
        
        if csv_files:
            selected_csv = st.selectbox("View CSV file:", csv_files)
            if selected_csv:
                csv_path = os.path.join(output_folder, selected_csv)
                stats = csv_storage.get_csv_stats(csv_path)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📝 Records", stats.get('row_count', 0))
                with col2:
                    st.metric("💾 Size", f"{stats.get('file_size_kb', 0)} KB")
                
                # Download button
                if st.button("📥 Download CSV", use_container_width=True):
                    try:
                        with open(csv_path, 'rb') as f:
                            st.download_button(
                                label="⬇️ Click to Download",
                                data=f.read(),
                                file_name=selected_csv,
                                mime="text/csv",
                                use_container_width=True
                            )
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                
                # Preview button
                if st.button("👁️ Preview CSV", use_container_width=True):
                    try:
                        df = pd.read_csv(csv_path)
                        st.dataframe(df.tail(5), use_container_width=True)
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        else:
            st.info("No CSV files yet. Extract your first PDF to create one!")
        
        st.divider()
        
        st.markdown("### 📋 Fields Extracted")
        st.caption(f"Total: {len(CSVStorage.DEFAULT_COLUMNS)} columns")
        with st.expander("View all fields"):
            for col in CSVStorage.DEFAULT_COLUMNS:
                st.text(f"• {col}")
    
    # Main content
    st.subheader("📤 Upload Criminal Judgment PDF")
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file containing a Court of Appeal criminal judgment",
        type=['pdf'],
        help="Upload a PDF file (max 50MB). The file should contain a complete judgment with case details."
    )
    
    if uploaded_file is not None:
        # Save temporary file
        temp_dir = './temp'
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, uploaded_file.name)
        
        with open(temp_file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"✅ File uploaded: **{uploaded_file.name}**")
        
        # Show file info
        file_size_mb = len(uploaded_file.getbuffer()) / (1024 * 1024)
        st.info(f"📄 File size: {file_size_mb:.2f} MB")
        
        st.session_state.pdf_uploaded = True
        
        st.divider()
        
        # Extraction button
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            if st.button("🔍 Extract Information", use_container_width=True, type="primary"):
                st.session_state.extraction_in_progress = True
                st.session_state.extracted_data = None  # Clear previous data
        
        with col3:
            if st.button("🔄 Reset & Upload New", use_container_width=True):
                st.session_state.extracted_data = None
                st.session_state.pdf_uploaded = False
                st.session_state.extraction_in_progress = False
                # Clean up temp file
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                st.rerun()
        
        # Process extraction
        if st.session_state.extraction_in_progress:
            with st.spinner("🔄 Extracting and analyzing judgment... Please wait (30-60 seconds)"):
                extracted_data = extract_from_pdf(temp_file_path, api_type)
                st.session_state.extracted_data = extracted_data
                st.session_state.extraction_in_progress = False
        
        # Display results
        if st.session_state.extracted_data:
            st.divider()
            
            # Check for errors
            if 'error' in st.session_state.extracted_data:
                st.error(f"❌ Extraction Failed: {st.session_state.extracted_data['error']}")
                st.warning("Please check your PDF file and try again. Ensure the PDF contains readable text.")
            else:
                st.success("✅ Extraction Complete!")
                
                display_extracted_data(st.session_state.extracted_data)
                
                # Save to CSV section
                st.divider()
                st.subheader("💾 Save Extracted Data")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("💾 Save to CSV File", use_container_width=True, type="primary"):
                        csv_storage = CSVStorage(output_folder)
                        csv_path = os.path.join(output_folder, f"{csv_filename}.csv")
                        
                        # Ensure file exists with headers
                        if not os.path.exists(csv_path):
                            success, msg = csv_storage.create_csv_file(csv_filename)
                            if not success:
                                st.error(f"❌ Failed to create CSV: {msg}")
                                return
                        
                        # Save data
                        success, message = csv_storage.save_data(
                            csv_path,
                            st.session_state.extracted_data['extracted_info'],
                            filename=uploaded_file.name
                        )
                        
                        if success:
                            st.success(f"✅ {message}")
                            st.info(f"📁 Saved to: `{csv_path}`")
                            
                            # Show stats
                            stats = csv_storage.get_csv_stats(csv_path)
                            st.metric("Total Records in CSV", stats.get('row_count', 0))
                        else:
                            st.error(f"❌ Save Failed: {message}")
                
                with col2:
                    if st.button("📄 Extract Another PDF", use_container_width=True):
                        st.session_state.extracted_data = None
                        st.session_state.pdf_uploaded = False
                        st.session_state.extraction_in_progress = False
                        # Clean up temp file
                        if os.path.exists(temp_file_path):
                            os.remove(temp_file_path)
                        st.rerun()
        
        # Cleanup temp file if extraction is done
        if st.session_state.extracted_data and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass
    
    else:
        # Show instructions when no file is uploaded
        st.info("""
        **How to use:**
        1. 📤 Upload a Court of Appeal criminal judgment PDF
        2. 🔍 Click "Extract Information" to analyze the document
        3. 👀 Review the extracted data in organized tabs
        4. 💾 Save the structured data to CSV file
        5. 📥 Download CSV from sidebar for further analysis
        
        **Extracted Fields Include:**
        - Case identification (Case numbers, court locations)
        - Dates (Offence, HC judgment, CoA judgment)
        - Parties (Judges, names)
        - Offence details (Sections, categories)
        - Evidence analysis (Witnesses, forensic, medical)
        - Grounds of appeal (14 categories)
        - Court decisions (HC and CoA)
        - Legal analysis (Errors, procedural defects)
        - Final outcomes (Conviction status, sentences, fines)
        - Full judgment text
        """)


if __name__ == "__main__":
    main()