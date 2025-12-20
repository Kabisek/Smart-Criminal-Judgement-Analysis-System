# Setup & Installation Guide

## System Requirements

- **Python:** 3.8 or higher
- **OS:** Windows, macOS, or Linux
- **Browser:** Modern browser (Chrome, Firefox, Safari, Edge)
- **Disk Space:** At least 100 MB for application and dependencies

## Step-by-Step Installation

### 1. Verify Python Installation

```powershell
python --version
pip --version
```

You should see Python 3.8+ and pip versions.

### 2. Clone/Download the Application

The application folder is located at:
```
c:\Users\shant\OneDrive\Desktop\SmartCriminalJudgementAnalysisSystem\JSON_to_CSV
```

### 3. Navigate to Application Directory

```powershell
cd "c:\Users\shant\OneDrive\Desktop\SmartCriminalJudgementAnalysisSystem\JSON_to_CSV"
```

### 4. Create Virtual Environment (Optional but Recommended)

```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1
```

If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again.

### 5. Install Dependencies

```powershell
pip install -r requirements.txt
```

This installs:
- Flask 3.0.0 (web framework)
- Werkzeug 3.0.1 (WSGI utilities)
- openpyxl 3.11.0 (Excel support)

### 6. Run the Application

```powershell
python app.py
```

You should see:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

### 7. Access the Web Interface

Open your browser and go to:
```
http://localhost:5000
```

You should see the JSON to CSV Converter interface.

## Verification Checklist

- [ ] Python version is 3.8+
- [ ] All dependencies installed without errors
- [ ] Flask app starts without errors
- [ ] Web interface loads in browser
- [ ] Sample JSON button works
- [ ] Can convert sample JSON successfully

## Troubleshooting Installation

### Issue: "Python not found" or "pip not found"

**Solution:** Add Python to PATH or use full path to Python executable:
```powershell
C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python311\python.exe app.py
```

### Issue: "ModuleNotFoundError: No module named 'flask'"

**Solution:** Reinstall requirements:
```powershell
pip uninstall -r requirements.txt
pip install -r requirements.txt
```

### Issue: "Port 5000 already in use"

**Solution:** Change port in app.py (last line):
```python
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)  # Use 5001 instead
```

### Issue: "Address already in use" even after restart

**Solution:** Kill the process using port 5000:
```powershell
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Issue: "Execution Policy" error when activating venv

**Solution:** Run PowerShell as Administrator and:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Post-Installation Setup

### Create Data Directory (Auto-created but you can do manually)

```powershell
New-Item -ItemType Directory -Path "data" -Force
```

### Check Permissions

Ensure the application folder has write permissions for the `data` directory.

## Running Without Virtual Environment

If you prefer not to use a virtual environment:

```powershell
pip install --user -r requirements.txt
python app.py
```

Note: This installs packages for your user only.

## Stopping the Application

In the PowerShell terminal where the app is running:
```powershell
Ctrl+C
```

## Next Steps

1. Read the QUICKSTART.md for first usage
2. Check README.md for detailed features
3. Review CONFIG.md for customization options
4. Explore the API endpoints in README.md

## Production Deployment

For production use:

1. **Disable Debug Mode:**
   ```python
   app.run(debug=False, host='0.0.0.0', port=5000)
   ```

2. **Use a Production WSGI Server:**
   ```powershell
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

3. **Add HTTPS/SSL:**
   - Use Nginx as reverse proxy
   - Configure SSL certificates
   - Set up firewall rules

4. **Implement Authentication:**
   - Add user authentication
   - Encrypt stored data
   - Regular backups

5. **Monitor:**
   - Set up logging
   - Monitor disk space
   - Regular backups of data directory

## Getting Help

- Check the README.md for feature documentation
- Review CONFIG.md for configuration options
- Check API endpoints in README.md for integration help
- Examine app.py for source code and logic

---

**Installation complete!** Your JSON to CSV Converter is ready to use.
