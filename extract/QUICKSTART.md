# Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies
```bash
cd extract
pip install -r requirements.txt
```

### Step 2: Configure API Keys
```bash
# Copy the example config
copy config\.env.example config\.env

# Edit config\.env with your favorite editor
# Add your GEMINI_API_KEY or DEEPSEEK_API_KEY
```

### Step 3: Get Your API Key

**Option A: Google Gemini (Recommended for beginners)**
1. Go to https://ai.google.dev/
2. Click "Get API Key"
3. Create a new API key
4. Copy and paste into `config/.env`

**Option B: Deepseek**
1. Go to https://platform.deepseek.com/
2. Sign up and create API key
3. Copy and paste into `config/.env`

### Step 4: Run the Application

**Web Interface (Recommended):**
```bash
streamlit run app.py
```
Opens at http://localhost:8501

**Command Line (For batch processing):**
```bash
# Single PDF
python cli.py -p "path\to\file.pdf" -o "output.csv"

# Batch process folder
python cli.py -b "path\to\pdf\folder" -o "output.csv"
```

## That's it! 🎉

Your application is ready to extract criminal judgment data from PDFs!

---

## Common Commands

### Web App
```bash
streamlit run app.py
```

### CLI - Single File
```bash
python cli.py -p "documents\judgment_001.pdf" -o "results.csv" -a gemini
```

### CLI - Entire Folder
```bash
python cli.py -b "Data_judgment_PDF_files\2021\AppealCourt" -o "2021_extractions.csv"
```

### CLI - Custom Pattern
```bash
python cli.py -b "Data_judgment_PDF_files" -p "April_*.pdf" -o "april_cases.csv"
```

---

## File Locations

After setup, you'll have:

```
extract/
├── config/
│   └── .env              ← Your API keys go here
├── output/               ← Generated CSV files here
│   └── judgment_extractions.csv
├── temp/                 ← Temporary PDF files (auto-cleaned)
└── app.py               ← Web application
```

---

## Extracted Data

Each CSV will contain:

- **case_number** - Court case ID
- **judge_names** - Judge(s) involved
- **accused_names** - Accused person/persons
- **victim_names** - Victim(s)
- **crime_type** - Type of crime / IPC sections
- **judgment_date** - Date judgment was issued
- **verdict** - Verdict (Guilty/Not Guilty/etc)
- **sentence** - Punishment details
- **court_name** - Which court
- **key_facts** - Important case facts
- **case_registration_date** - When case was filed
- **hearing_dates** - Dates of hearings
- **timestamp** - When extracted
- **filename** - Original PDF name

---

## Troubleshooting

### "Module not found" error
```bash
# Make sure you're in the extract folder
cd extract

# Install dependencies
pip install -r requirements.txt
```

### "API key invalid" error
- Check `config/.env` exists and has your API key
- Verify the key is copied correctly (no spaces)
- Try generating a new key from the API provider

### "PDF extraction failed"
- Ensure the PDF has selectable text (not a scanned image)
- Try a different PDF file first
- Check the PDF is not corrupted

### "API timeout"
- Check your internet connection
- Try a smaller PDF first
- Check if the API service is online

---

## Next Steps

- ✅ Run the web app
- ✅ Upload your first PDF
- ✅ Check the extracted data
- ✅ Download the CSV file
- ✅ Process your entire document collection

See `README.md` for more detailed information and advanced usage.
