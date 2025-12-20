#!/usr/bin/env python3
"""
Command-line interface for PDF extraction
Alternative to the web application for batch processing
"""

import os
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pdf_processor import PDFProcessor
from ai_extractor import ExtractorFactory
from csv_storage import CSVStorage
from config import Config


def process_single_pdf(pdf_path, output_csv, api_type=None):
    """
    Process a single PDF file
    
    Args:
        pdf_path: Path to PDF file
        output_csv: Output CSV file path
        api_type: API to use ('gemini' or 'deepseek')
    """
    print(f"\n📄 Processing: {pdf_path}")
    
    # Use configured API if not specified
    if api_type is None:
        api_type = Config.PRIMARY_API
    
    # Initialize components
    pdf_processor = PDFProcessor()
    csv_storage = CSVStorage()
    
    # Extract text from PDF
    print("  ├─ Extracting text from PDF...")
    success, message, extracted_text = pdf_processor.extract_text(pdf_path)
    
    if not success:
        print(f"  ├─ ❌ Error: {message}")
        return False
    
    print(f"  ├─ ✅ Text extracted successfully")
    
    # Get metadata
    metadata = pdf_processor.extract_metadata(pdf_path)
    print(f"  ├─ Pages: {metadata.get('total_pages', 'N/A')}")
    print(f"  ├─ Size: {metadata.get('file_size_mb', 'N/A')} MB")
    
    # Extract with AI
    print(f"  ├─ Extracting information with {api_type.upper()}...")
    try:
        api_key = Config.DEEPSEEK_API_KEY if api_type == 'deepseek' else Config.GEMINI_API_KEY
        
        if not api_key:
            print(f"  ├─ ❌ Error: {api_type.upper()}_API_KEY not configured")
            return False
        
        extractor = ExtractorFactory.create_extractor(api_type, api_key)
        extracted_info = extractor.extract_judgment_info(extracted_text)
        
        if 'error' in extracted_info:
            print(f"  ├─ ❌ Error: {extracted_info['error']}")
            return False
        
        print(f"  ├─ ✅ Information extracted successfully")
    
    except Exception as e:
        print(f"  ├─ ❌ Error: {str(e)}")
        return False
    
    # Save to CSV
    print(f"  ├─ Saving to CSV...")
    
    # Create CSV if doesn't exist
    csv_dir = os.path.dirname(output_csv)
    os.makedirs(csv_dir, exist_ok=True)
    
    if not os.path.exists(output_csv):
        csv_storage.create_csv_file(
            os.path.splitext(os.path.basename(output_csv))[0],
            csv_dir
        )
    
    success, message = csv_storage.save_data(
        output_csv,
        extracted_info,
        filename=os.path.basename(pdf_path)
    )
    
    if success:
        print(f"  └─ ✅ {message}")
        return True
    else:
        print(f"  └─ ❌ {message}")
        return False


def process_batch(pdf_folder, output_csv, api_type=None, file_pattern='*.pdf'):
    """
    Process multiple PDF files from a folder
    
    Args:
        pdf_folder: Folder containing PDF files
        output_csv: Output CSV file path
        api_type: API to use
        file_pattern: Glob pattern for PDF files
    """
    if not os.path.isdir(pdf_folder):
        print(f"❌ Error: Folder not found: {pdf_folder}")
        return
    
    print(f"🔍 Scanning folder: {pdf_folder}")
    
    # Find all PDF files
    pdf_files = list(Path(pdf_folder).glob(file_pattern))
    
    if not pdf_files:
        print(f"❌ No PDF files found matching pattern: {file_pattern}")
        return
    
    print(f"📊 Found {len(pdf_files)} PDF file(s)")
    
    # Process files
    successful = 0
    failed = 0
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}]", end="")
        
        if process_single_pdf(str(pdf_path), output_csv, api_type):
            successful += 1
        else:
            failed += 1
    
    # Summary
    print("\n" + "="*50)
    print("📊 BATCH PROCESSING SUMMARY")
    print("="*50)
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📁 Output: {output_csv}")
    print("="*50)


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description='Criminal Judgment PDF Extractor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Process single PDF with Gemini
  python cli.py -p "path/to/judgment.pdf" -o "output.csv" -a gemini
  
  # Batch process all PDFs in folder
  python cli.py -b "path/to/folder" -o "output.csv"
  
  # Process with custom pattern
  python cli.py -b "path/to/folder" -p "*.pdf" -o "output.csv" -a deepseek
        '''
    )
    
    parser.add_argument('-p', '--pdf', type=str, help='Path to single PDF file')
    parser.add_argument('-b', '--batch', type=str, help='Path to folder containing PDFs')
    parser.add_argument('-o', '--output', type=str, required=True, help='Output CSV file path')
    parser.add_argument('-a', '--api', type=str, choices=['gemini', 'deepseek'],
                        help='API to use (defaults to PRIMARY_API from config)')
    parser.add_argument('--pattern', type=str, default='*.pdf', help='File pattern for batch (default: *.pdf)')
    
    args = parser.parse_args()
    
    # Validate configuration
    is_valid, config_msg = Config.validate_api_config()
    if not is_valid:
        print(f"❌ Configuration Error: {config_msg}")
        print("\nPlease set up your API key in config/.env")
        return 1
    
    # Process based on arguments
    if args.pdf:
        print("🚀 Single PDF Processing Mode")
        if not os.path.isfile(args.pdf):
            print(f"❌ Error: PDF file not found: {args.pdf}")
            return 1
        
        success = process_single_pdf(args.pdf, args.output, args.api)
        return 0 if success else 1
    
    elif args.batch:
        print("🚀 Batch Processing Mode")
        process_batch(args.batch, args.output, args.api, args.pattern)
        return 0
    
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
