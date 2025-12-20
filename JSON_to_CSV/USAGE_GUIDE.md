# Usage Guide

Complete guide for using the JSON to CSV Converter application.

## Getting Started

### 1. Start the Application

```powershell
python app.py
```

Open `http://localhost:5000` in your browser.

## Main Interface Overview

The application is divided into three main sections:

### Left Panel: Input JSON Data
- **Text Area:** Paste your JSON data here
- **Format JSON Button:** Auto-formats and validates JSON
- **Convert to CSV Button:** Converts and saves the data
- **Load Sample JSON Button:** Loads example data for testing

### Right Panel: Preview & Info
- Shows the last converted entry
- Displays field values from the conversion
- Helps verify correct data conversion

### Bottom Panel: Data Management
- **Statistics:** Total entries, file sizes, latest update
- **Download Buttons:** Export data in multiple formats
- **Data Table:** View all stored conversions
- **Refresh Button:** Reload data from storage

## Step-by-Step Usage

### Converting Your First JSON

#### Step 1: Prepare Your JSON
Your JSON must be a valid object with fields matching the CSV schema.

Example minimal JSON:
```json
{
  "source_file_name": "case_001.pdf",
  "court_of_appeal_case_no": "HCC 0001/2023",
  "high_court_case_no": "HC/001/23",
  "high_court_location": "Colombo",
  "judgment_date_coa": "2023-12-15",
  "offence_category": "Theft"
}
```

#### Step 2: Paste JSON
1. Click in the JSON input area
2. Paste your JSON data
3. If formatting is messy, click **"Format JSON"**

#### Step 3: Convert
Click the **"Convert to CSV"** button or press `Ctrl+Enter`

You'll see:
- ✅ Success message at the top
- 📊 Preview of converted data
- 🔄 Statistics updated automatically

### Working with Stored Data

#### View an Entry
1. Locate the entry in the data table
2. Click the **"View"** button
3. A modal opens showing all fields in JSON format
4. Click **"Download Entry as JSON"** to save it

#### Delete an Entry
1. Find the entry in the table
2. Click the **"Delete"** button
3. Confirm deletion
4. Entry is removed from both CSV and JSON storage

#### Refresh Data
Click the **"Refresh Data"** button to reload from disk.

## Downloading Data

### Download as CSV
```powershell
# Click the "Download CSV" button
# Saves as: conversions_YYYYMMDD_HHMMSS.csv
```

**Use for:**
- Import into Excel, Google Sheets
- Data analysis tools
- Database imports
- Sharing structured data

### Download as JSON
```powershell
# Click the "Download JSON" button
# Saves as: raw_inputs_YYYYMMDD_HHMMSS.json
```

**Use for:**
- Backup original inputs
- API integrations
- Data migration
- System backup

### Download as Excel
```powershell
# Click the "Download Excel" button
# Saves as: conversions_YYYYMMDD_HHMMSS.xlsx
```

**Use for:**
- Excel-specific features
- Pivot tables
- Advanced formatting
- Business reporting

## Data Fields

### Essential Fields
```json
{
  "source_file_name": "filename",           // Source document
  "court_of_appeal_case_no": "HCC 0001/23", // Appeal case number
  "high_court_case_no": "HC/001/23",       // High court number
  "high_court_location": "Colombo",        // Court location
  "judgment_date_coa": "2023-12-15"        // Date format: YYYY-MM-DD
}
```

### Case Information
```json
{
  "judges": ["Judge A", "Judge B"],        // Array of judges
  "offence_sections": "Section 2(1)(d)",   // Criminal statutes
  "offence_category": "Theft",             // Crime type
  "brief_facts_summary": "..."             // Case summary
}
```

### Arrays and Lists
Fields like `judges` and `grounds_of_appeal_structured_notes` accept arrays:

```json
{
  "judges": [
    "R. Gurusinghe J.",
    "Mayadunne Corea J."
  ]
}
```

In CSV, arrays are converted to pipe-separated values:
```
R. Gurusinghe J. | Mayadunne Corea J.
```

### Null and Empty Values
```json
{
  "judgment_date_hc": null,           // Becomes empty string in CSV
  "date_of_offence": null,            // Becomes empty string in CSV
  "field": ""                          // Empty string stays empty
}
```

## Common Tasks

### Batch Convert Multiple JSONs
1. Load first JSON
2. Click "Convert to CSV"
3. Load next JSON
4. Repeat
5. All data accumulates in storage

### Verify Data Was Saved
1. Look at statistics box
2. "Total Entries" should increase
3. "Latest Entry" should update
4. Data table should show new row

### Find a Specific Entry
1. Use browser's Find function: `Ctrl+F`
2. Search for case number or file name
3. Click view to inspect details

### Back Up Your Data
1. Click "Download CSV" to backup structured data
2. Click "Download JSON" to backup raw inputs
3. Store both files in a safe location

### Restore from Backup
Currently, to restore:
1. Delete entries one by one, or
2. Stop app and replace `data/conversions.csv` or `data/raw_inputs.json` manually
3. Restart app

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Enter` | Convert JSON |
| `Ctrl+F` | Find in page |
| `Tab` | Navigate form fields |
| `Escape` | Close modal dialog |

## Tips & Tricks

### 1. Format Complex JSON
```powershell
# Paste messy JSON, click "Format JSON"
{"a":"b","c":"d"} 
# Becomes:
{
  "a": "b",
  "c": "d"
}
```

### 2. Load Sample First
Click "Load Sample JSON" to see the correct structure before entering your own data.

### 3. Check Statistics
Monitor the stats box to verify:
- All data is being saved
- File sizes are reasonable
- Recent entries are being added

### 4. Use Date Format YYYY-MM-DD
```json
{
  "judgment_date_coa": "2023-12-15",  // ✓ Correct
  "judgment_date_coa": "15/12/2023"   // ✗ Will be stored as string
}
```

### 5. Handle Special Characters
```json
{
  "name": "Text with \"quotes\"",    // Escape quotes with \"
  "name": "Text with 'apostrophe'"   // Single quotes don't need escaping
}
```

## Data Storage Locations

Files are created automatically in the `data/` directory:

```
data/
├── conversions.csv        # CSV export of all entries
└── raw_inputs.json        # Original JSON objects
```

### CSV File Structure
- **Header Row:** All 82 CSV columns
- **Data Rows:** One row per converted JSON
- **Encoding:** UTF-8
- **Line Endings:** CRLF (Windows standard)

### JSON File Structure
Array of objects:
```json
[
  {
    "source_file_name": "...",
    "court_of_appeal_case_no": "...",
    "timestamp": "2024-11-25T10:30:45.123456",
    "conversion_id": "CONV_20241125_103045",
    ...
  },
  ...
]
```

## API Usage (Advanced)

If you want to integrate with other systems:

### Convert Data
```bash
curl -X POST http://localhost:5000/api/convert \
  -H "Content-Type: application/json" \
  -d '{"json_input": "{\"court_of_appeal_case_no\":\"HCC 0001/23\"}"}'
```

### Get All Data
```bash
curl http://localhost:5000/api/data
```

### Delete Entry
```bash
curl -X DELETE http://localhost:5000/api/delete/CONV_20241125_103045
```

### Get Statistics
```bash
curl http://localhost:5000/api/stats
```

## Troubleshooting

### "Invalid JSON" Error
- Check JSON syntax using online JSON validator
- Ensure all quotes are properly escaped
- Look for missing commas between fields

### "Port already in use" Error
- Another app is using port 5000
- Wait a minute and try again, or
- Change port in app.py and restart

### Data not appearing in table
- Click "Refresh Data" button
- Check if conversion was successful (green message)
- Verify file permissions in data/ folder

### Download buttons not working
- Check browser console for errors (F12)
- Ensure data/ folder exists
- Try refreshing the page

### Excel export fails
- Install openpyxl: `pip install openpyxl`
- Restart the application

## Best Practices

1. **Regular Backups**
   - Download JSON weekly
   - Store backups in separate location
   - Version your backups

2. **Data Quality**
   - Validate JSON before converting
   - Use consistent date formats
   - Test with sample data first

3. **Performance**
   - CSV files grow over time
   - Archive old data periodically
   - Download and delete old entries if needed

4. **Security**
   - Don't expose to public internet without HTTPS
   - Backup sensitive data
   - Clear data when no longer needed

## Reporting Issues

If something doesn't work:
1. Check browser console: Press F12 → Console tab
2. Check application logs in terminal
3. Try restarting the application
4. Verify JSON format is valid

---

**Happy converting!** 🎉

For more information, check:
- README.md - Full feature documentation
- QUICKSTART.md - 2-minute setup
- CONFIG.md - Configuration options
