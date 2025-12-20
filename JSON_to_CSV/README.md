# JSON to CSV Converter Application

A modern web application that converts JSON data to CSV format with data storage and download capabilities.

## Features

✨ **Core Functionality:**
- Convert JSON objects to CSV format
- Automatic data validation and formatting
- Support for complex data types (lists, arrays)
- Beautiful, responsive user interface

💾 **Data Management:**
- All inputs automatically saved to local storage
- View stored conversions with timestamps
- Delete individual entries
- Real-time statistics and analytics

📥 **Download Options:**
- Export as CSV
- Export as JSON (raw inputs)
- Export as Excel (XLSX)
- Download individual entries

🎨 **User Experience:**
- Dark mode-friendly gradient interface
- Real-time JSON formatting
- Sample data for quick testing
- Modal view for detailed entry inspection
- Responsive design for all screen sizes

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup Steps

1. **Navigate to the application directory:**
```powershell
cd "c:\Users\shant\OneDrive\Desktop\SmartCriminalJudgementAnalysisSystem\JSON_to_CSV"
```

2. **Install dependencies:**
```powershell
pip install -r requirements.txt
```

3. **Run the application:**
```powershell
python app.py
```

4. **Open your browser:**
Navigate to `http://localhost:5000`

## Usage

### Converting JSON to CSV

1. **Paste your JSON data** into the input area on the left
   - Use the "Format JSON" button to auto-format messy JSON
   - Click "Load Sample JSON" to see the expected format

2. **Click "Convert to CSV"** (or press Ctrl+Enter)
   - The data is validated and converted
   - Success message appears at the top

3. **View the conversion result** in the preview panel

### Managing Data

- **View Details:** Click the "View" button to inspect full entry
- **Delete Entry:** Click the "Delete" button to remove an entry
- **Download Data:** Use the download buttons to export in various formats

### Statistics

Real-time statistics show:
- Total number of entries converted
- CSV file size
- JSON storage size
- Date of latest entry

## File Structure

```
JSON_to_CSV/
├── app.py                 # Flask backend application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── QUICKSTART.md         # Quick start guide
├── templates/
│   └── index.html        # Web interface
├── data/                 # Auto-created data directory
│   ├── conversions.csv   # Stored CSV data
│   └── raw_inputs.json   # Stored JSON inputs
└── config/
    └── (optional configurations)
```

## API Endpoints

### POST /api/convert
Convert JSON to CSV and save
- **Request:** `{ "json_input": "{...}" }`
- **Response:** `{ "success": true, "conversion_id": "...", "csv_row": {...} }`

### GET /api/data
Get all stored conversions
- **Response:** `{ "success": true, "data": [...], "total_entries": 0 }`

### GET /api/download/csv
Download CSV file

### GET /api/download/json
Download JSON file

### GET /api/download/excel
Download Excel file

### DELETE /api/delete/<conversion_id>
Delete specific entry

### GET /api/stats
Get application statistics

## Column Support

The application supports the following CSV columns from criminal judgment data:

### Basic Information
- source_file_name
- court_of_appeal_case_no
- high_court_case_no
- high_court_location
- judgment_date_coa
- judgment_date_hc
- date_of_offence

### Case Details
- judges
- offence_sections
- offence_category
- location_of_offence
- language_of_criminal

### Evidence & Facts
- brief_facts_summary
- evidence_type_primary
- evidence_type_secondary
- witness_evidence_analysis_summary

### High Court Information
- hc_offence_of_conviction_sections
- hc_sentence_type
- hc_fine_amount
- hc_compensation_amount
- hc_judgment_summary

### Appeal Grounds
- grounds_of_appeal_raw_text_summary
- grounds_of_appeal_structured_notes
- gnd_contradictions
- gnd_chain_of_custody
- gnd_illegal_search_or_raid
- (and 10+ more ground-specific fields)

### Evidence Analysis
- eyewitness_present
- child_witness_present
- expert_evidence_present
- forensic_evidence_present
- medical_evidence_strength
- chain_of_custody_quality
- dying_declaration_present
- confession_present
- circumstantial_case

### Court of Appeal Information
- coa_final_outcome_class
- coa_conviction_status
- coa_sentence_type
- coa_fine_amount
- coa_compensation_amount
- court_of_appeal_analysis_summary

### Metadata
- prosecution_counsel
- defence_counsel
- plea_of_accused
- appeal_type
- trial_method
- precedents_cited_list
- standard_of_review_applied

## Keyboard Shortcuts

- **Ctrl+Enter** or **Cmd+Enter**: Convert JSON

## Troubleshooting

### Port 5000 Already in Use
If port 5000 is in use, modify `app.py` line at the bottom:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change 5000 to 5001
```

### Missing Dependencies
Reinstall requirements:
```powershell
pip install --upgrade -r requirements.txt
```

### Excel Export Not Working
Install openpyxl:
```powershell
pip install openpyxl
```

### JSON Validation Errors
Ensure your JSON is valid. Use the "Format JSON" button to automatically format and validate.

## Data Storage

- **CSV Storage:** `data/conversions.csv`
- **JSON Storage:** `data/raw_inputs.json`

Both files are auto-created and updated as you add conversions.

## Performance Notes

- Handles large JSON objects efficiently
- CSV export optimized for Excel compatibility
- JSON storage preserves all data without truncation
- Real-time statistics with 10-second refresh interval

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

This application is part of the Smart Criminal Judgement Analysis System.

## Support

For issues or feature requests, contact the development team.
