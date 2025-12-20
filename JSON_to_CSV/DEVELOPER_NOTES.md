# Developer Notes & Architecture

## 🏗️ Application Architecture

### MVC Pattern
```
Model Layer
├── CSV Storage (data/conversions.csv)
├── JSON Storage (data/raw_inputs.json)
└── In-memory processing

View Layer
├── HTML Template (templates/index.html)
├── CSS Styling
└── JavaScript Interactivity

Controller Layer
├── Flask Routes (app.py)
├── Request handlers
└── Response formatting
```

---

## 📂 Code Organization

### Backend (app.py)

**Main Components:**

1. **Configuration**
   - CSV_HEADERS (82 columns)
   - DATA_DIR paths
   - File locations

2. **Data Functions**
   - `load_json_storage()` - Read JSON file
   - `save_json_storage()` - Write JSON file
   - `append_to_csv()` - Add CSV row
   - `validate_json()` - Validate input
   - `process_json_row()` - Convert format

3. **Routes**
   - `/` - Serve index.html
   - `/api/convert` - Convert endpoint
   - `/api/data` - Get all data
   - `/api/download/*` - Download endpoints
   - `/api/delete/*` - Delete endpoint
   - `/api/stats` - Statistics endpoint

### Frontend (templates/index.html)

**Structure:**

```html
<html>
  <head>
    <style>/* 800+ lines of responsive CSS */</style>
  </head>
  <body>
    <header><!-- Title and description --></header>
    <div class="container">
      <div class="main-content">
        <div class="card"><!-- Input section --></div>
        <div class="card"><!-- Preview section --></div>
        <div class="card data-section"><!-- Management --></div>
      </div>
    </div>
    <div id="detailsModal"><!-- Modal dialog --></div>
    <script>/* 600+ lines of JavaScript --></script>
  </body>
</html>
```

**Key JavaScript Functions:**

- `formatJSON()` - Clean JSON
- `loadSampleJSON()` - Load example
- `convertJSON()` - Send to backend
- `loadAllData()` - Fetch from server
- `renderDataTable()` - Display data
- `downloadCSV/JSON/Excel()` - Export
- `deleteEntry()` - Remove data
- `viewDetails()` - Show modal
- `showAlert()` - Display messages

---

## 🔄 Data Flow

### Conversion Flow
```
User Input (JSON)
    ↓
Validation (validate_json)
    ↓
Processing (process_json_row)
    ↓
CSV Append (append_to_csv)
    ↓
JSON Save (save_json_storage)
    ↓
Response to Frontend
    ↓
Update UI (table, preview, stats)
```

### Download Flow
```
User Click Download
    ↓
Load Data (CSV/JSON)
    ↓
Format Data (add timestamps)
    ↓
Create Stream (BytesIO)
    ↓
Send File Response
    ↓
Browser Download
```

### Delete Flow
```
User Confirm Delete
    ↓
Load JSON Storage
    ↓
Filter Out Entry
    ↓
Save JSON
    ↓
Recreate CSV
    ↓
Response + Refresh
```

---

## 🔧 Technical Decisions

### Why Flask?
- Lightweight and simple
- Perfect for small-to-medium apps
- Easy to extend
- Good documentation
- Python ecosystem

### Why CSV + JSON Storage?
- **CSV:** Compatible with Excel, databases, BI tools
- **JSON:** Preserves original data, better for backup
- **Both:** Redundancy and flexibility

### Why Vanilla JavaScript?
- No dependencies to install
- Fast and responsive
- Easier to modify
- Smaller file size

### Why SQLite Not Used?
- CSV is simpler for this use case
- Better for ad-hoc analysis
- Easier to backup and migrate
- Lower complexity

---

## 📊 Data Field Mapping

### JSON Input → CSV Output

**Simple fields:** Direct copy
```python
json_obj["source_file_name"] → csv_row["source_file_name"]
```

**List fields:** Pipe-separated conversion
```python
["Judge A", "Judge B"] → "Judge A | Judge B"
```

**Null fields:** Empty string
```python
null → ""
```

**Added fields:** Automatic
```python
timestamp → "2024-11-25T10:30:45.123456"
conversion_id → "CONV_20241125_103045"
```

---

## 🔐 Error Handling

### Frontend Errors
- Invalid JSON → Alert user
- Network errors → Catch and display
- File not found → Show empty state

### Backend Errors
- JSON decode error → 400 status
- File I/O error → 500 status
- Missing parameter → 400 status

### Validation
- JSON syntax check
- Type validation
- Required fields check (optional)

---

## 🚀 Performance Optimizations

### Frontend
- Vanilla JS (no framework overhead)
- Debounced stats refresh (10s)
- Minimal DOM manipulation
- CSS animations (GPU accelerated)
- Responsive images (emojis)

### Backend
- Efficient file I/O
- CSV append (not rewrite)
- JSON loaded once per request
- No database overhead
- Stream downloads

### Storage
- UTF-8 encoding (compact)
- Only necessary data stored
- Periodic cleanup recommended
- Separate CSV/JSON (choose format)

---

## 🔌 Extension Points

### Add New Fields
1. Update `CSV_HEADERS` in app.py
2. Fields automatically handled by `process_json_row()`
3. Restart application

### Change Download Format
Add new route in app.py:
```python
@app.route('/api/download/parquet', methods=['GET'])
def download_parquet():
    # Custom format export
    pass
```

### Add Database Support
Replace file I/O in:
- `load_json_storage()`
- `save_json_storage()`
- `append_to_csv()`

### Add Authentication
Wrap routes with decorator:
```python
@app.route('/api/convert', methods=['POST'])
@require_auth
def convert_json():
    pass
```

### Add WebSocket Support
For real-time updates:
- Install flask-socketio
- Update frontend to use WebSocket
- Broadcast stats changes

---

## 🧪 Testing Scenarios

### Manual Test Cases

**1. Basic Conversion**
```json
{"source_file_name": "test.pdf", "court_of_appeal_case_no": "HCC 0001/23"}
```

**2. With Arrays**
```json
{"judges": ["Judge A", "Judge B"], "offence_sections": ["Section 1", "Section 2"]}
```

**3. With Nulls**
```json
{"judgment_date_hc": null, "date_of_offence": null}
```

**4. Large Data**
```json
{"brief_facts_summary": "Very long text..."}
```

**5. Special Characters**
```json
{"name": "Text with \"quotes\"", "text": "Unicode: 你好"}
```

---

## 📈 Monitoring & Logging

### Current State
- Console logs in browser (F12)
- Terminal output in PowerShell

### Future Enhancements
- Log file generation
- Error tracking (Sentry)
- Analytics (Google Analytics)
- Performance monitoring

---

## 🔄 Deployment Scenarios

### Local Development
```powershell
python app.py
# Debug mode enabled
# Watch for changes
```

### Production (Gunicorn)
```powershell
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Production (Docker)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### Production (Apache/Nginx)
```nginx
server {
    listen 80;
    server_name example.com;
    
    location / {
        proxy_pass http://localhost:5000;
    }
}
```

---

## 🛡️ Security Hardening

### Current Implementation
✅ Input validation
✅ Safe file paths
✅ UTF-8 encoding
✅ No external calls

### Recommendations
- [ ] Add HTTPS/SSL
- [ ] Implement authentication
- [ ] Add rate limiting
- [ ] Encrypt stored data
- [ ] Log all operations
- [ ] Regular backups
- [ ] Access control lists
- [ ] Input sanitization (extra layer)

---

## 📚 Code Comments

The code includes:
- Docstrings for functions
- Inline comments for logic
- Section headers
- Type hints (where applicable)

---

## 🎯 Future Enhancements

### Phase 2
- Database backend (SQLAlchemy)
- User authentication (Flask-Login)
- Multi-user support
- Data encryption

### Phase 3
- Real-time collaboration
- WebSocket updates
- Webhook notifications
- Advanced analytics

### Phase 4
- Machine learning integration
- Data validation rules engine
- Custom field mapping
- Template management

---

## 📞 Code Review Checklist

Before deploying to production:

- [ ] Test with sample data
- [ ] Check error handling
- [ ] Verify file permissions
- [ ] Test all download formats
- [ ] Check CSV encoding
- [ ] Verify timestamps
- [ ] Test delete functionality
- [ ] Check UI responsiveness
- [ ] Review security settings
- [ ] Backup/restore tested

---

## 🧑‍💻 Developer Setup

### Create Development Environment
```powershell
# Clone/download repo
cd JSON_to_CSV

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
python app.py
```

### Code Style
- PEP 8 for Python
- HTML5 semantics
- Modern CSS (Grid, Flexbox)
- ES6+ JavaScript

---

## 📖 References

### Flask Documentation
- https://flask.palletsprojects.com/
- Routing, request/response
- File handling

### CSV Module
- https://docs.python.org/3/library/csv.html
- DictReader/DictWriter

### Werkzeug
- https://werkzeug.palletsprojects.com/
- File uploads, security

---

## ✨ Special Thanks

Built with:
- Python 3.11
- Flask 3.0.0
- Modern web standards
- Love and attention to detail

---

**Happy coding!** 🚀
