# Application Configuration

## Server Settings

HOST = '0.0.0.0'
PORT = 5000
DEBUG = True

## File Storage

DATA_DIR = 'data'
CSV_FILE = 'conversions.csv'
JSON_STORAGE = 'raw_inputs.json'

## CSV Configuration

# Headers must match the JSON structure
# Lists are converted to pipe-separated strings
# None values become empty strings
# All fields are preserved

## Security Notes

- Never expose this server to the public internet without HTTPS
- Implement authentication for production use
- Regular backups recommended for data directory
- Clear sensitive data when necessary

## Performance

- CSV file size grows with each entry (~5-10 KB per judgment entry)
- JSON storage preserves original input exactly
- Consider archiving old data for long-running instances

## Customization

To modify CSV columns:
1. Edit CSV_HEADERS in app.py
2. Restart the application
3. New columns will be created in new exports

To change port:
1. Modify PORT = 5000 to your desired port
2. Or pass port parameter: app.run(port=8000)
