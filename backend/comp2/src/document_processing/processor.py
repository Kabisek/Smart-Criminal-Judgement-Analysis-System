import fitz  # PyMuPDF
from pathlib import Path
import logging
import json

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

logger = logging.getLogger(__name__)

class MultiFormatProcessor:
    def extract_text(self, file_path: str) -> dict:
        path = Path(file_path)
        ext = path.suffix.lower()
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if ext == '.pdf':
            return self._from_pdf(str(path))
        elif ext in ['.docx', '.doc']:
            return self._from_docx(str(path))
        elif ext == '.txt':
            return self._from_txt(str(path))
        elif ext == '.json':
            return self._from_json(str(path))
        else:
            raise ValueError(f"Unsupported format: {ext}")

    def extract_text_with_positions(self, file_path: str) -> dict:
        """Extract text along with character-offset page/block info for bounding-box highlighting."""
        path = Path(file_path)
        ext = path.suffix.lower()

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if ext == '.pdf':
            return self._from_pdf_with_positions(str(path))
        elif ext in ['.docx', '.doc']:
            return self._add_page_wrapper(self._from_docx(str(path)))
        elif ext == '.txt':
            return self._add_page_wrapper(self._from_txt(str(path)))
        elif ext == '.json':
            return self._add_page_wrapper(self._from_json(str(path)))
        else:
            raise ValueError(f"Unsupported format: {ext}")

    def _from_pdf_with_positions(self, path: str) -> dict:
        """PDF extraction that also returns per-page text and block-level bounding boxes."""
        doc = fitz.open(path)
        pages = []
        full_parts = []
        char_cursor = 0

        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            page_dict = page.get_text("dict")

            blocks = []
            for blk in page_dict.get("blocks", []):
                if blk.get("type") != 0:
                    continue
                block_text_parts = []
                for line in blk.get("lines", []):
                    for span in line.get("spans", []):
                        block_text_parts.append(span.get("text", ""))
                block_text = " ".join(block_text_parts)
                if not block_text.strip():
                    continue
                bbox = blk.get("bbox", [0, 0, 0, 0])
                idx = page_text.find(block_text[:40])
                blk_offset = char_cursor + idx if idx >= 0 else char_cursor
                blocks.append({
                    "text": block_text,
                    "bbox": list(bbox),
                    "char_offset": blk_offset,
                })

            pages.append({
                "page_num": page_num,
                "text": page_text,
                "char_offset": char_cursor,
                "blocks": blocks,
            })
            full_parts.append(page_text)
            char_cursor += len(page_text)

        doc.close()
        return {
            "full_text": "".join(full_parts),
            "source": Path(path).name,
            "pages": pages,
        }

    @staticmethod
    def _add_page_wrapper(base: dict) -> dict:
        """Wrap a simple extraction result in the pages structure expected by the highlight pipeline."""
        text = base.get("full_text", "")
        base["pages"] = [{
            "page_num": 0,
            "text": text,
            "char_offset": 0,
            "blocks": [],
        }]
        return base

    def _from_pdf(self, path):
        doc = fitz.open(path)
        text = "".join([page.get_text() for page in doc])
        return {"full_text": text, "source": Path(path).name}

    def _from_docx(self, path):
        if not DOCX_AVAILABLE: raise ImportError("Install python-docx")
        doc = DocxDocument(path)
        text = "\n".join([p.text for p in doc.paragraphs])
        return {"full_text": text, "source": Path(path).name}

    def _from_txt(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return {"full_text": f.read(), "source": Path(path).name}
    
    def _from_json(self, path):
        """
        Extract text from JSON file.
        Supports multiple JSON structures:
        1. Standard case JSON with input_metadata.analyzed_text or input_metadata.original_text
        2. Simple JSON with 'text' or 'content' field
        3. JSON array/object that can be stringified
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            text_parts = []
            
            # Try to extract from structured case JSON format
            if isinstance(data, dict):
                # Check for input_metadata.analyzed_text (preferred - English)
                if 'input_metadata' in data:
                    metadata = data['input_metadata']
                    if 'analyzed_text' in metadata and metadata['analyzed_text']:
                        text_parts.append(metadata['analyzed_text'])
                    elif 'original_text' in metadata and metadata['original_text']:
                        text_parts.append(metadata['original_text'])
                
                # Check for direct text fields
                if 'text' in data and data['text']:
                    text_parts.append(str(data['text']))
                if 'content' in data and data['content']:
                    text_parts.append(str(data['content']))
                if 'full_text' in data and data['full_text']:
                    text_parts.append(str(data['full_text']))
                
                # If data has legal_analysis, include it
                if 'data' in data and isinstance(data['data'], dict):
                    if 'legal_analysis' in data['data']:
                        legal = data['data']['legal_analysis']
                        if isinstance(legal, dict):
                            if 'prosecution_argument' in legal:
                                text_parts.append(f"Prosecution Argument: {legal['prosecution_argument']}")
                            if 'defense_argument' in legal:
                                text_parts.append(f"Defense Argument: {legal['defense_argument']}")
                
                # If no specific text fields found, try to stringify the whole structure
                if not text_parts:
                    # Convert entire JSON to readable text format
                    text_parts.append(json.dumps(data, indent=2, ensure_ascii=False))
            
            # If it's a list, stringify it
            elif isinstance(data, list):
                text_parts.append(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Join all text parts
            full_text = "\n\n".join(text_parts) if text_parts else json.dumps(data, indent=2, ensure_ascii=False)
            
            return {
                "full_text": full_text,
                "source": Path(path).name,
                "json_data": data  # Also include original JSON data for further processing
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON file {path}: {e}")
            raise ValueError(f"Invalid JSON file: {e}")
        except Exception as e:
            logger.error(f"Error reading JSON file {path}: {e}")
            raise