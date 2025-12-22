# Smart-Criminal-Judgement-Analysis-System
Final year research project

## Project Overview
This project consists of three main components designed to extract, process, and analyze criminal judgment data from PDF documents and convert them into structured formats.

---

## 📁 Folder Structure

### 1. **Data_judgment_PDF_files/**
This folder contains the raw judgment PDF documents organized by year and court type.

**Structure:**
- **2021-2025 subdirectories**: Each year folder contains judicial documents
  - **AppealCourt/**: Contains judgment PDF files from the Appeal Court for that specific year

**Purpose:** 
- Serves as the primary data source for the extraction system
- Stores raw, unprocessed judgment documents from various years
- Organized chronologically for easy access and archival management

**Content:**
- PDF documents containing criminal judgments and appeal court decisions
- Year-based organization allows for temporal analysis of judgments

---

### 2. **extract/**
This folder contains the PDF data extraction application that reads judgment PDFs and extracts relevant information.

**Key Components:**
- **app.py**: Main Flask/Streamlit web application entry point
- **cli.py**: Command-line interface for batch processing PDFs
- **src/**: Source code directory containing:
  - `ai_extractor.py`: AI-powered extraction logic for parsing judgment content
  - `pdf_processor.py`: PDF reading and text extraction functionality
  - `csv_storage.py`: CSV file handling and storage
  - `config.py`: Configuration settings
- **config/**: Configuration files for the extraction system
- **output/**: Stores extracted data:
  - `judgment_extractions.csv`: Extracted judgment data in CSV format
  - `extracted_json/`: JSON-formatted extracted data
- **logs/**: Application logs for debugging and monitoring
- **requirements.txt**: Python package dependencies

**Purpose:**
- Extracts structured information from unstructured PDF judgment documents
- Converts PDF content into machine-readable formats (CSV and JSON)
- Provides both web UI (app.py) and command-line (cli.py) interfaces

---

### 3. **JSON_to_CSV/**
This folder contains the JSON to CSV conversion application with a web-based interface.

**Key Components:**
- **app.py**: Web application for JSON-CSV conversion
- **data/**: Data directory containing:
  - `raw_inputs.json`: Input JSON files for conversion
  - `conversions.csv`: Output CSV files after conversion
- **templates/**: HTML templates:
  - `index.html`: Web interface for the conversion tool
- **requirements.txt**: Python package dependencies
- **Documentation files**:
  - `START_HERE.md`: Quick start guide
  - `QUICKSTART.md`: Usage instructions
  - `USAGE_GUIDE.md`: Detailed usage documentation
  - `CONFIG.md`: Configuration reference
  - `DEVELOPER_NOTES.md`: Development guidelines

**Purpose:**
- Converts JSON-formatted data into CSV format for analysis
- Provides a web-based user interface for easy conversion
- Bridges the output from the extraction module to analysis-ready CSV files
- Handles data transformation and validation

---

## 🔄 Data Flow
```
Data_judgment_PDF_files/ 
        ↓
    extract/ (PDF → JSON/CSV extraction)
        ↓
JSON_to_CSV/ (JSON → CSV conversion)
        ↓
    Analysis Ready Data
```

---

## Getting Started
Refer to the individual folder READMEs and documentation files for specific setup and usage instructions for each component.
