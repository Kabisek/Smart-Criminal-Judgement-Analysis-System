import os
import json
import fitz
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# --- CONFIGURATION ---
RAW_DIR = "data/raw/Landmark cases"
OUTPUT_DIR = "data/structured"
MODEL_NAME = "gemini-2.5-flash" 

def extract_text_from_pdf(pdf_path):
    print(f"   Reading PDF: {os.path.basename(pdf_path)}...")
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

import time
import random

def convert_to_structured_json(raw_text):
    prompt = f"""
    Role: Professional Legal Data Scientist.
    Task: Convert the following Sri Lankan Landmark Case raw text into a highly structured JSON object.
    
    JSON Schema:
    {{
      "case_metadata": {{
        "case_name": "...",
        "case_number": "...",
        "court": "...",
        "citation": "...",
        "dates": {{ "hearing": [], "decision": "..." }},
        "judges": ["Name 1", "Name 2"],
        "counsel": {{ "appellants": [], "respondents": [] }},
        "keywords": [],
        "legislation_referred": []
      }},
      "headnotes": [
        {{ "point_number": 1, "summary": "..." }}
      ],
      "cases_referred": [],
      "judgment_text": [
        {{ "section_title": "...", "content": "..." }}
      ]
    }}

    Rules:
    1. Extract ALL headnotes points (usually found at the start).
    2. Split judgment text into logical sections (Facts, Legal Issues, Ratio Decidendi, Conclusion).
    3. Ensure judicial names are correctly captured.
    4. Return ONLY valid JSON. No markdown.

    RAW TEXT:
    {raw_text[:30000]} # Limit to 30k chars for stability
    """
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel(model_name=MODEL_NAME)
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            return json.loads(response.text)
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                wait = (attempt + 1) * 60 + random.uniform(5, 15)
                print(f"   ⚠️  Quota hit. Waiting {wait:.1f}s before retry...")
                time.sleep(wait)
            else:
                raise e

def main():
    pdfs = [
        "001-SLLR-SLLR-1999-V-1-B.-SIRISENA-COORAY-v.-TISSA-DIAS-BANDARANAYAKE-AND-TWO-OTHERS.pdf",
        "013-NLR-NLR-V-37-THE-KING-v.-ATTYGALLE-et-al.pdf",
        "019-SLLR-SLLR-1989-V-2-THILAKARATNE-v.-ATTORNEY-GENERAL.pdf",
        "032-SLLR-SLLR-1999-V-2-UPUL-DE-SILVA-v.-ATTORNEY-GENERAL.pdf",
        "048-NLR-NLR-V-63-K.-G.-SOMAPALA-Appellant-and-THE-ATTORNEY-GENERAL-Respondent.pdf",
        "069-NLR-NLR-V-55-THE-QUEEN-v.-M.-SATHASIVAM.pdf",
        "117-NLR-NLR-V-41-FERNANDO-v.-THEMIS-APPUHAMY.pdf"
    ]
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    for pdf_name in pdfs:
        pdf_path = os.path.join(RAW_DIR, pdf_name)
        if not os.path.exists(pdf_path):
            print(f"⚠️  Missing: {pdf_path}")
            continue

        try:
            raw_text = extract_text_from_pdf(pdf_path)
            structured_json = convert_to_structured_json(raw_text)
            
            output_name = pdf_name.replace(".pdf", ".json").lower()
            output_path = os.path.join(OUTPUT_DIR, output_name)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(structured_json, f, indent=2)
            
            print(f"✅ Converted: {output_name}")
            # Intelligent delay between files to avoid project-level quota hits
            time.sleep(15) 
        except Exception as e:
            print(f"❌ Failed {pdf_name}: {e}")

if __name__ == "__main__":
    main()
