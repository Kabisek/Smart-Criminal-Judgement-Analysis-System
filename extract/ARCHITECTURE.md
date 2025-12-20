# System Architecture & Component Overview

## Project Summary

A complete PDF extraction system for criminal judgment documents that:
- Accepts PDF uploads
- Extracts text and structured information
- Uses AI (Deepseek or Gemini) to intelligently parse judgment data
- Saves results to CSV files for analysis

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│              USER INTERFACE LAYER                        │
├─────────────────────────────────────────────────────────┤
│  Streamlit Web App (app.py) │ CLI Tool (cli.py)         │
└────────────────┬────────────────────────────────────────┘
                 │
┌─────────────────▼────────────────────────────────────────┐
│         APPLICATION LOGIC LAYER                          │
├─────────────────────────────────────────────────────────┤
│ ┌──────────────────┐ ┌──────────────────┐               │
│ │ PDF Processor    │ │  AI Extractor    │               │
│ │ (pdf_processor)  │ │ (ai_extractor)   │               │
│ └──────────────────┘ └──────────────────┘               │
│ ┌──────────────────┐ ┌──────────────────┐               │
│ │ CSV Storage      │ │  Configuration   │               │
│ │ (csv_storage)    │ │  (config)        │               │
│ └──────────────────┘ └──────────────────┘               │
└─────────────────┬────────────────────────────────────────┘
                 │
┌─────────────────▼────────────────────────────────────────┐
│           EXTERNAL SERVICES                              │
├─────────────────────────────────────────────────────────┤
│  Google Gemini API  │  Deepseek API  │  File System     │
└─────────────────────────────────────────────────────────┘
```

## Module Breakdown

### 1. **pdf_processor.py** - PDF Text Extraction
```
Responsibilities:
- File validation (format, size)
- Text extraction from PDF pages
- Metadata extraction (page count, file info)
- Error handling for corrupted files

Key Classes:
- PDFProcessor: Main class for PDF operations
```

### 2. **ai_extractor.py** - AI-Powered Information Extraction
```
Responsibilities:
- Abstract interface for AI extractors
- Deepseek API integration
- Google Gemini API integration
- Response parsing and JSON handling
- Prompt engineering for judgment extraction

Key Classes:
- AIExtractor (abstract)
- DeepseekExtractor
- GeminiExtractor
- ExtractorFactory (factory pattern)

Extracted Fields:
- Case Number, Judge Names, Accused Names
- Victim Names, Crime Type, Judgment Date
- Verdict, Sentence, Key Facts
- Court Name, Case Registration Date
- Hearing Dates
```

### 3. **csv_storage.py** - Data Persistence
```
Responsibilities:
- CSV file creation with headers
- Single and batch data saving
- CSV statistics and listing
- Data formatting and normalization

Key Classes:
- CSVStorage: Handles all CSV operations

Features:
- Auto-creates folders
- Appends data to existing files
- Timestamps all entries
```

### 4. **config.py** - Configuration Management
```
Responsibilities:
- Environment variable loading
- API key management
- Configuration validation
- Settings exposure

Key Classes:
- Config: Centralized configuration

Configuration Sources:
- .env file
- Environment variables
- Default values
```

### 5. **app.py** - Streamlit Web Application
```
Responsibilities:
- User interface
- File upload handling
- Results display
- CSV management

Features:
- Drag-and-drop PDF upload
- Real-time extraction progress
- Data preview
- CSV download
- File listing
```

### 6. **cli.py** - Command-Line Interface
```
Responsibilities:
- CLI argument parsing
- Batch processing
- Progress reporting
- Exit codes

Features:
- Single file processing
- Batch folder processing
- Custom file patterns
- Progress summary
```

## Data Flow

```
1. USER UPLOADS PDF
        ↓
2. FILE VALIDATION
   (format, size check)
        ↓
3. TEXT EXTRACTION
   (from PDF pages)
        ↓
4. METADATA COLLECTION
   (pages, file size, etc)
        ↓
5. AI PROCESSING
   (send to Gemini/Deepseek)
        ↓
6. RESPONSE PARSING
   (extract JSON data)
        ↓
7. DATA FORMATTING
   (normalize fields)
        ↓
8. CSV STORAGE
   (append to CSV file)
        ↓
9. USER RECEIVES RESULTS
   (download or view)
```

## Configuration

**File:** `config/.env`

```env
# API Selection
PRIMARY_API=gemini  # or 'deepseek'

# API Keys
GEMINI_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here

# Output Settings
OUTPUT_FOLDER=./output
MAX_FILE_SIZE_MB=25
```

## File Structure

```
extract/
├── app.py                          # 🌐 Web application (Streamlit)
├── cli.py                          # 💻 Command-line tool
├── requirements.txt                # 📦 Dependencies
├── README.md                       # 📖 Full documentation
├── QUICKSTART.md                   # ⚡ Quick start guide
├── config/
│   └── .env.example               # ⚙️  Config template
├── src/
│   ├── pdf_processor.py           # 📄 PDF extraction
│   ├── ai_extractor.py            # 🤖 AI processing
│   ├── csv_storage.py             # 💾 CSV management
│   └── config.py                  # ⚙️  Configuration
├── output/                         # 📊 Generated CSV files
└── temp/                           # 🗑️  Temporary files
```

## Features

✅ **Multi-Format Support** - Supports both Gemini and Deepseek APIs
✅ **Flexible Interfaces** - Web UI and CLI options
✅ **Batch Processing** - Process multiple PDFs at once
✅ **Data Validation** - File validation before processing
✅ **Error Handling** - Comprehensive error messages
✅ **CSV Export** - Standardized data format
✅ **Configuration** - Easy .env configuration
✅ **Logging** - Progress tracking and feedback

## Usage Examples

### Web Application
```bash
streamlit run app.py
# Opens at http://localhost:8501
# 1. Upload PDF
# 2. Click "Extract Information"
# 3. Review results
# 4. Click "Save to CSV"
# 5. Download from sidebar
```

### Single File Processing
```bash
python cli.py -p "judgment.pdf" -o "results.csv" -a gemini
```

### Batch Processing
```bash
python cli.py -b "PDF_folder" -o "results.csv" -a deepseek
```

### Python API
```python
from src.pdf_processor import PDFProcessor
from src.ai_extractor import ExtractorFactory
from src.csv_storage import CSVStorage
from src.config import Config

# Extract
processor = PDFProcessor()
success, msg, text = processor.extract_text('file.pdf')

# Process with AI
extractor = ExtractorFactory.create_extractor('gemini', Config.GEMINI_API_KEY)
data = extractor.extract_judgment_info(text)

# Save
storage = CSVStorage()
storage.save_data('./output/results.csv', data, 'file.pdf')
```

## API Integration

### Gemini API
- **Provider**: Google
- **Website**: https://ai.google.dev/
- **Model**: gemini-pro
- **Free Tier**: 60 requests/minute

### Deepseek API
- **Provider**: Deepseek
- **Website**: https://platform.deepseek.com/
- **Model**: deepseek-chat
- **Free Tier**: Check platform

## Error Handling

The system handles:
- Invalid file formats
- Corrupted PDF files
- Missing API keys
- API timeouts
- Network errors
- Invalid JSON responses
- Missing fields in extracted data

## Security

- API keys stored locally in .env
- Never committed to version control
- No data stored on external servers
- Temporary files auto-cleaned
- Input validation on all files

## Performance

- **File Size**: Supports up to 25 MB PDFs
- **API Response**: ~5-30 seconds per document
- **Batch Processing**: Sequential processing with progress
- **Memory**: Efficient streaming for large documents

## Dependencies

```
streamlit==1.28.1              # Web UI
python-dotenv==1.0.0          # Environment variables
google-generativeai==0.3.0     # Gemini API
openai==1.3.0                  # API utilities
pdfplumber==0.10.3             # PDF extraction
pandas==2.1.1                  # Data handling
requests==2.31.0               # HTTP requests
```

## Future Enhancements

- [ ] Database backend (SQLite/PostgreSQL)
- [ ] REST API endpoint
- [ ] Advanced text preprocessing
- [ ] Custom extraction templates
- [ ] Caching mechanism
- [ ] Scheduling service
- [ ] Data visualization
- [ ] Multi-language support

---

**Version**: 1.0  
**Created**: November 2025  
**Status**: Production Ready
