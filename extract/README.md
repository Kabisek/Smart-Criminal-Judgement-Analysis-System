# Criminal Judgment PDF Extractor

A web application to extract structured information from criminal judgment PDF documents and store the data in CSV format using AI APIs (Deepseek or Google Gemini).

## Features

✅ **PDF Upload** - Upload criminal judgment PDF files  
✅ **AI-Powered Extraction** - Extract key information using Deepseek or Google Gemini  
✅ **CSV Storage** - Automatically save extracted data to CSV files  
✅ **User-Friendly Interface** - Built with Streamlit for easy interaction  
✅ **Batch Processing** - Support for processing multiple documents  
✅ **Flexible API** - Switch between Deepseek and Gemini APIs  

## Extracted Information

The application extracts the following fields from judgment documents:

- Case Number
- Judge Names
- Accused Names
- Victim Names
- Crime Type / Section
- Judgment Date
- Verdict (Guilty/Not Guilty/etc)
- Sentence/Punishment
- Key Facts
- Court Name
- Case Registration Date
- Hearing Dates
- Timestamp and Source Filename

## Project Structure

```
extract/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── config/
│   └── .env.example               # Environment variables template
├── src/
│   ├── config.py                  # Configuration management
│   ├── pdf_processor.py          # PDF text extraction
│   ├── ai_extractor.py           # AI extraction logic
│   └── csv_storage.py            # CSV file handling
├── output/                        # Generated CSV files
└── temp/                          # Temporary file storage
```

## Prerequisites

- Python 3.8 or higher
- API Key for either Google Gemini or Deepseek
- pip (Python package manager)

## Installation

### 1. Clone or Extract the Project

```bash
cd extract
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Keys

Create `.env` file in the `config` folder:

```bash
cp config/.env.example config/.env
```

Edit `config/.env` and add your API credentials:

```env
# For Google Gemini
GEMINI_API_KEY=your_api_key_here
PRIMARY_API=gemini

# OR for Deepseek
DEEPSEEK_API_KEY=your_api_key_here
PRIMARY_API=deepseek
```

### Get API Keys

**Google Gemini:**
1. Visit https://ai.google.dev/
2. Click "Get API Key" 
3. Create a new API key in Google Cloud Console
4. Copy the key to `.env`

**Deepseek:**
1. Visit https://platform.deepseek.com/
2. Sign up for an account
3. Generate an API key from the dashboard
4. Copy the key to `.env`

## Usage

### Run the Web Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

### Using the Application

1. **Upload PDF** - Click the file uploader and select a criminal judgment PDF
2. **Extract** - Click "Extract Information" button
3. **Review** - Check the extracted information
4. **Save** - Click "Save to CSV" to store the data
5. **Download** - Use the sidebar to download CSV files

### Using as a Python Module

```python
from src.pdf_processor import PDFProcessor
from src.ai_extractor import ExtractorFactory
from src.csv_storage import CSVStorage
from src.config import Config

# Extract text from PDF
pdf_processor = PDFProcessor()
success, message, text = pdf_processor.extract_text('path/to/pdf.pdf')

# Extract information using AI
extractor = ExtractorFactory.create_extractor(
    'gemini', 
    Config.GEMINI_API_KEY
)
extracted_info = extractor.extract_judgment_info(text)

# Save to CSV
csv_storage = CSVStorage()
csv_storage.create_csv_file('judgments')
csv_storage.save_data('./output/judgments.csv', extracted_info, 'pdf_name.pdf')
```

## Configuration

Edit `config/.env` to customize:

```env
# API Configuration
DEEPSEEK_API_KEY=your_key
GEMINI_API_KEY=your_key
PRIMARY_API=gemini  # or 'deepseek'

# Output folder for CSV files
OUTPUT_FOLDER=./output

# Maximum allowed PDF file size (in MB)
MAX_FILE_SIZE_MB=25
```

## Output Format

Generated CSV files contain the following columns:

| Column | Description |
|--------|-------------|
| timestamp | When the extraction was performed |
| filename | Original PDF filename |
| case_number | Court case reference number |
| judge_names | Names of judges |
| accused_names | Names of accused persons |
| victim_names | Names of victims |
| crime_type | Type of crime / Sections |
| judgment_date | Date of judgment |
| verdict | Judgment verdict |
| sentence | Punishment details |
| key_facts | Important facts from case |
| court_name | Name of the court |
| case_registration_date | When case was registered |
| hearing_dates | Dates of court hearings |

## Troubleshooting

### "API Key not configured"
- Ensure `.env` file exists in `config` folder
- Check that API key is correctly entered
- Verify PRIMARY_API is set to 'gemini' or 'deepseek'

### "Connection timeout"
- Check internet connection
- Verify API endpoint is accessible
- Try with smaller PDF files first

### "Text extraction failed"
- Ensure PDF contains searchable text (not scanned images)
- Check PDF file is not corrupted
- Try with a different PDF file

### Memory/Performance Issues
- Reduce MAX_FILE_SIZE_MB in `.env`
- Process PDFs in smaller batches
- Clear `temp` folder periodically

## Advanced Usage

### Batch Processing

```python
import os
from src.pdf_processor import PDFProcessor
from src.ai_extractor import ExtractorFactory
from src.csv_storage import CSVStorage
from src.config import Config

pdf_processor = PDFProcessor()
csv_storage = CSVStorage()
extractor = ExtractorFactory.create_extractor('gemini', Config.GEMINI_API_KEY)

# Create CSV file
csv_storage.create_csv_file('batch_extraction')

# Process multiple PDFs
pdf_folder = './Data_judgment_PDF_files/2021/AppealCourt'
for filename in os.listdir(pdf_folder):
    if filename.endswith('.pdf'):
        filepath = os.path.join(pdf_folder, filename)
        _, _, text = pdf_processor.extract_text(filepath)
        
        if text:
            extracted_info = extractor.extract_judgment_info(text)
            csv_storage.save_data(
                './output/batch_extraction.csv',
                extracted_info,
                filename
            )
```

## API Rate Limits

**Gemini API:**
- Free tier: 60 requests per minute
- Paid tier: Higher limits available

**Deepseek API:**
- Varies by subscription
- Check platform.deepseek.com for details

## Security Notes

- Never commit `.env` file to version control
- Keep API keys confidential
- Use environment variables in production
- Consider API rate limiting and caching

## License

This project is part of the Smart Criminal Judgement Analysis System.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review API documentation
3. Verify configuration files
4. Check internet connectivity

## Future Enhancements

- [ ] Multi-language support
- [ ] Custom extraction templates
- [ ] Database integration
- [ ] API rate limiting with queues
- [ ] Advanced text processing
- [ ] Data visualization dashboard
- [ ] Scheduled batch processing
- [ ] REST API interface
