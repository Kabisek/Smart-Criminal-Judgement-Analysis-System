"""
PDF Processing Module
Extracts text from PDF files and handles batch processing
"""

import fitz  # PyMuPDF
from pathlib import Path
import pandas as pd
from tqdm import tqdm
import logging
import sys
from pathlib import Path as PathLib

# Add src to path for judge extractor
sys.path.insert(0, str(PathLib(__file__).parent.parent))
from comp2.src.ml_utils.judge_extractor import JudgeExtractor

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Process PDF files and extract text content"""
    
    def __init__(self, data_dir="data/judgments", extract_judge_info=True):
        self.data_dir = Path(data_dir)
        self.extract_judge_info = extract_judge_info
        if extract_judge_info:
            self.judge_extractor = JudgeExtractor()
        
    def extract_text_from_pdf(self, pdf_path):
        """
        Extract text from a single PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            dict: Contains full_text, source, and metadata
        """
        try:
            doc = fitz.open(str(pdf_path))
            num_pages = len(doc)  # Get page count before closing
            text_parts = []
            
            for page_num, page in enumerate(doc):
                text = page.get_text()
                if text.strip():  # Only add non-empty pages
                    text_parts.append(text)
            
            full_text = "\n\n".join(text_parts)
            doc.close()  # Close document after extracting all data
            
            result = {
                "full_text": full_text,
                "source": pdf_path.name,
                "file_path": str(pdf_path),
                "num_pages": num_pages,
                "text_length": len(full_text),
                "success": True,
                "error": None
            }
            
            # Extract judge information if enabled
            if self.extract_judge_info and full_text:
                try:
                    judge_info = self.judge_extractor.extract_judge_info(full_text)
                    result["judge_names"] = ",".join(judge_info.get("judge_names", []))
                    result["judge_statements_count"] = len(judge_info.get("judge_statements", []))
                    result["judge_holdings_count"] = len(judge_info.get("judge_holdings", []))
                    result["has_judge_info"] = judge_info.get("has_judge_info", False)
                    # Store full judge info as JSON string for later use
                    import json
                    result["judge_info_json"] = json.dumps(judge_info)
                except Exception as e:
                    logger.warning(f"Error extracting judge info from {pdf_path}: {e}")
                    result["judge_names"] = ""
                    result["judge_statements_count"] = 0
                    result["judge_holdings_count"] = 0
                    result["has_judge_info"] = False
                    result["judge_info_json"] = "{}"
            
            return result
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")
            return {
                "full_text": "",
                "source": pdf_path.name,
                "file_path": str(pdf_path),
                "num_pages": 0,
                "text_length": 0,
                "success": False,
                "error": str(e)
            }
    
    def process_all_pdfs(self, output_file="data/processed/raw_extracted_texts.csv"):
        """
        Process all PDF files in the data directory and save to CSV
        
        Args:
            output_file: Path to save the extracted texts CSV
            
        Returns:
            pd.DataFrame: DataFrame with extracted texts and metadata
        """
        # Find all PDF files
        pdf_files = list(self.data_dir.rglob("*.pdf"))
        print(f"Found {len(pdf_files)} PDF files to process")
        
        results = []
        
        # Process each PDF with progress bar
        for pdf_path in tqdm(pdf_files, desc="Processing PDFs"):
            result = self.extract_text_from_pdf(pdf_path)
            results.append(result)
        
        # Create DataFrame
        df = pd.DataFrame(results)
        
        # Extract year and court from path
        df['year'] = df['file_path'].apply(self._extract_year)
        df['court'] = df['file_path'].apply(self._extract_court)
        
        # Create case_id
        df['case_id'] = df.apply(
            lambda row: f"{row['year']}_{row['court']}_{row['source'].replace('.pdf', '')}", 
            axis=1
        )
        
        # Save to CSV
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        print(f"\n✅ Processing complete!")
        print(f"   Total files: {len(df)}")
        print(f"   Successful: {df['success'].sum()}")
        print(f"   Failed: {(~df['success']).sum()}")
        print(f"   Saved to: {output_path}")
        
        return df
    
    def _extract_year(self, file_path):
        """Extract year from file path"""
        path_parts = Path(file_path).parts
        for part in path_parts:
            if part.isdigit() and len(part) == 4:
                return int(part)
        return None
    
    def _extract_court(self, file_path):
        """Extract court type from file path"""
        path_parts = Path(file_path).parts
        for part in path_parts:
            if 'court' in part.lower():
                return part
        return "Unknown"

