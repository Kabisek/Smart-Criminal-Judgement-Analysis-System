# 📋 Application Usage Guide

## 🌐 Web Application (Recommended)

### Getting Started
```bash
cd extract
pip install -r requirements.txt
streamlit run app.py
```

Opens at: **http://localhost:8501**

### Step-by-Step Guide

#### Step 1: Configuration (Right Sidebar)
1. Select API: **Gemini** (recommended) or **Deepseek**
2. Set Output CSV folder (default: `./output`)
3. Set CSV filename (default: `judgment_extractions`)

#### Step 2: Upload PDF
1. Click "📤 Upload PDF" section
2. Select a criminal judgment PDF file
3. File is validated and temporarily saved

#### Step 3: Extract Information
1. Click **"🔍 Extract Information"** button
2. Processing indicator shows progress
3. Results appear below

#### Step 4: Review Results
- Formatted display of all extracted fields
- Metadata about the PDF (pages, size, name)
- Organized layout with column-based presentation

#### Step 5: Save to CSV
1. Click **"💾 Save to CSV"** button
2. Data is appended to your CSV file
3. Success message confirms saving

#### Step 6: Download & Continue
- Use **sidebar** to view and download CSV files
- Click **"🔄 Extract Another"** to process more PDFs

### CSV Management (Sidebar)
- 📊 View list of all CSV files
- 📈 See record count and file size
- 📥 Download any CSV file
- 🔄 Switch between different CSV files

---

## 💻 Command-Line Interface (Batch Processing)

### Basic Commands

#### Single PDF Extraction
```bash
python cli.py -p "path\to\judgment.pdf" -o "results.csv"
```

#### Batch Process Entire Folder
```bash
python cli.py -b "Data_judgment_PDF_files\2021\AppealCourt" -o "2021_results.csv"
```

#### Specify API Type
```bash
# Use Gemini
python cli.py -p "judgment.pdf" -o "results.csv" -a gemini

# Use Deepseek
python cli.py -p "judgment.pdf" -o "results.csv" -a deepseek
```

#### Custom File Pattern
```bash
# Process only April files
python cli.py -b "Data_judgment_PDF_files" --pattern "April_*.pdf" -o "april.csv"

# Process all 2021 appeal court files
python cli.py -b "Data_judgment_PDF_files\2021\AppealCourt" -o "2021_all.csv"
```

### Get Help
```bash
python cli.py --help
```

### Example Workflows

**Process Single File:**
```bash
python cli.py -p "April_criminal_judgment_1123.pdf" -o "single_result.csv"
```

**Batch Process by Year:**
```bash
# 2021 cases
python cli.py -b "Data_judgment_PDF_files\2021\AppealCourt" -o "cases_2021.csv"

# 2022 cases
python cli.py -b "Data_judgment_PDF_files\2022\AppealCourt" -o "cases_2022.csv"

# 2023 cases
python cli.py -b "Data_judgment_PDF_files\2023\AppealCourt" -o "cases_2023.csv"
```

**Batch Process by Month:**
```bash
python cli.py -b "Data_judgment_PDF_files" --pattern "April_*.pdf" -o "april_all_years.csv"
```

---

## 🐍 Python API

### Basic Usage

```python
from src.pdf_processor import PDFProcessor
from src.ai_extractor import ExtractorFactory
from src.csv_storage import CSVStorage
from src.config import Config

# 1. Extract text from PDF
processor = PDFProcessor()
success, message, text = processor.extract_text('judgment.pdf')

if success:
    # 2. Process with AI
    extractor = ExtractorFactory.create_extractor('gemini', Config.GEMINI_API_KEY)
    extracted_data = extractor.extract_judgment_info(text)
    
    # 3. Save to CSV
    storage = CSVStorage('./output')
    storage.create_csv_file('my_judgments')
    success, msg = storage.save_data('./output/my_judgments.csv', extracted_data, 'judgment.pdf')
    print(msg)
```

### Advanced: Batch Processing

```python
import os
from pathlib import Path
from src.pdf_processor import PDFProcessor
from src.ai_extractor import ExtractorFactory
from src.csv_storage import CSVStorage
from src.config import Config

# Setup
pdf_folder = "Data_judgment_PDF_files/2021/AppealCourt"
output_csv = "./output/2021_judgments.csv"

processor = PDFProcessor()
storage = CSVStorage()
extractor = ExtractorFactory.create_extractor('gemini', Config.GEMINI_API_KEY)

# Create CSV file
storage.create_csv_file('2021_judgments')

# Process all PDFs
for filename in sorted(os.listdir(pdf_folder)):
    if filename.endswith('.pdf'):
        filepath = os.path.join(pdf_folder, filename)
        
        print(f"Processing: {filename}...", end=" ")
        
        # Extract text
        success, msg, text = processor.extract_text(filepath)
        
        if success and text:
            # Extract information
            data = extractor.extract_judgment_info(text)
            
            # Save to CSV
            success, msg = storage.save_data(output_csv, data, filename)
            print(f"✅")
        else:
            print(f"❌ {msg}")

print(f"\nCompleted! Results saved to: {output_csv}")
```

### Custom Extraction Prompt

```python
from src.ai_extractor import GeminiExtractor

class CustomExtractor(GeminiExtractor):
    def get_extraction_prompt(self):
        return """
        Extract ONLY these fields from the judgment:
        1. Case Number
        2. Verdict (Guilty/Not Guilty)
        3. Sentence
        
        Return as JSON: {"case_number": "", "verdict": "", "sentence": ""}
        """

# Use custom extractor
extractor = CustomExtractor(Config.GEMINI_API_KEY)
data = extractor.extract_judgment_info(text)
```

---

## 📊 Working with CSV Files

### View Generated CSV
```bash
# Using pandas
import pandas as pd

df = pd.read_csv('./output/judgment_extractions.csv')
print(df.head())
print(df.info())
print(df.describe())
```

### Filter Results
```python
import pandas as pd

df = pd.read_csv('./output/judgment_extractions.csv')

# Filter by verdict
guilty_cases = df[df['verdict'].str.contains('Guilty', case=False)]

# Filter by year
df['year'] = pd.to_datetime(df['judgment_date']).dt.year
cases_2021 = df[df['year'] == 2021]

# Export filtered results
filtered.to_csv('./output/filtered_results.csv', index=False)
```

### Analysis Examples
```python
import pandas as pd

df = pd.read_csv('./output/judgment_extractions.csv')

# Count verdicts
print(df['verdict'].value_counts())

# Average sentence length
print(df['sentence'].value_counts().head(10))

# Cases by court
print(df['court_name'].value_counts())

# Cases by crime type
print(df['crime_type'].value_counts())
```

---

## ⚙️ Configuration Options

### .env File Settings

```env
# PRIMARY_API: Which AI service to use
# Options: 'gemini' or 'deepseek'
PRIMARY_API=gemini

# Google Gemini API Key
GEMINI_API_KEY=your_key_from_ai.google.dev

# Deepseek API Key
DEEPSEEK_API_KEY=your_key_from_platform.deepseek.com

# Where to save CSV files
OUTPUT_FOLDER=./output

# Maximum allowed PDF file size in MB
MAX_FILE_SIZE_MB=25
```

### Change Configuration at Runtime

**Web App:**
- Use sidebar settings to override defaults

**CLI:**
```bash
# Use specific API
python cli.py -p "file.pdf" -o "results.csv" -a deepseek
```

**Python API:**
```python
from src.config import Config
from src.csv_storage import CSVStorage

# Override output folder
storage = CSVStorage('./custom_output_folder')

# Get current API
print(Config.PRIMARY_API)
print(Config.GEMINI_API_KEY)
```

---

## 🔍 Troubleshooting

### Web App Issues

**Port already in use:**
```bash
streamlit run app.py --server.port 8502
```

**Slow loading:**
```bash
streamlit run app.py --logger.level=error
```

**Clear cache:**
```bash
rm -r ~/.streamlit/cache
```

### CLI Issues

**File not found:**
```bash
# Use absolute paths
python cli.py -p "C:\Users\...\judgment.pdf" -o "results.csv"
```

**Permission denied:**
```bash
# Run with admin rights or check folder permissions
```

**Out of memory:**
```bash
# Process smaller batches
python cli.py -b "Data_judgment_PDF_files\2021" -o "2021.csv"
python cli.py -b "Data_judgment_PDF_files\2022" -o "2022.csv"
```

---

## 📈 Performance Tips

1. **Start small** - Test with 1-2 PDFs first
2. **Batch by year** - Process year-wise instead of all at once
3. **Monitor API usage** - Check API quotas regularly
4. **Use CLI for batching** - Faster than web app for multiple files
5. **Cache results** - Don't re-process same PDFs

---

## 🎯 Common Use Cases

### Use Case 1: Annual Report Generation
```bash
for year in 2021 2022 2023 2024
do
    python cli.py -b "Data_judgment_PDF_files\$year\AppealCourt" -o "${year}_report.csv"
done
```

### Use Case 2: Monthly Analysis
```bash
python cli.py -b "." --pattern "*April_*.pdf" -o "april_analysis.csv"
python cli.py -b "." --pattern "*August_*.pdf" -o "august_analysis.csv"
```

### Use Case 3: Verdict Analysis
```python
import pandas as pd

df = pd.read_csv('judgment_extractions.csv')

# Analyze conviction rate
guilty = len(df[df['verdict'].str.contains('Guilty')])
total = len(df)
conviction_rate = (guilty / total) * 100

print(f"Conviction Rate: {conviction_rate:.2f}%")
```

---

## 📚 Additional Resources

- **README.md** - Complete feature documentation
- **QUICKSTART.md** - 5-minute setup
- **ARCHITECTURE.md** - Technical design
- **requirements.txt** - All dependencies

## 🎓 Learning Path

1. ✅ Read QUICKSTART.md (5 min)
2. ✅ Setup .env file (2 min)
3. ✅ Run web app once (5 min)
4. ✅ Extract first PDF (1 min)
5. ✅ Download CSV and inspect
6. ✅ Try CLI for batch processing
7. ✅ Write custom Python scripts
8. ✅ Analyze results with pandas

---

**Ready to begin? Start with:** `streamlit run app.py`
