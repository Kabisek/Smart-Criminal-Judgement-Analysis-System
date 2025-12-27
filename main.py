# from fastapi import FastAPI, UploadFile, File, Form, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# import os
# import sys
# import tempfile
# import gc
# from datetime import datetime
# from typing import Optional

# # Import modules
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# from utils.transcriber import transcribe_audio
# from core.engine import LegalReasoningEngine

# app = FastAPI(title="Smart Criminal Judgement System", version="Final-Research")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Initialize Engine
# DB_PATH = os.path.join(os.getcwd(), "data", "chroma_db")
# engine = LegalReasoningEngine(db_path=DB_PATH) if os.path.exists(DB_PATH) else None

# class AnalysisRequest(BaseModel):
#     transcript: str

# @app.post("/transcribe")
# async def transcribe_endpoint(audio: UploadFile = File(...), language: Optional[str] = Form("auto")):
#     temp_path = None
#     try:
#         suffix = f".{audio.filename.split('.')[-1]}"
#         with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
#             tmp.write(await audio.read())
#             temp_path = tmp.name
        
#         result = transcribe_audio(temp_path, language)
#         return {**result, "timestamp": datetime.now().isoformat()}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#     finally:
#         if temp_path and os.path.exists(temp_path):
#             try: gc.collect(); os.unlink(temp_path)
#             except: pass

# @app.post("/analyze")
# async def analyze_endpoint(request: AnalysisRequest):
#     if not engine: raise HTTPException(status_code=503, detail="Engine not ready. Run build_db.py")
#     try:
#         return {"status": "success", "data": engine.analyze_case(request.transcript)}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys
import tempfile
import gc
from datetime import datetime
from typing import Optional, Dict

# Import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.transcriber import transcribe_audio
from core.engine import LegalReasoningEngine

app = FastAPI(title="Smart Criminal Judgement System", version="Final-Research-v2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Engine
DB_PATH = os.path.join(os.getcwd(), "data", "chroma_db")
engine = LegalReasoningEngine(db_path=DB_PATH) if os.path.exists(DB_PATH) else None

# --- UPDATED DATA MODELS ---
class AnalysisRequest(BaseModel):
    english_transcript: str
    original_transcript: Optional[str] = None
    detected_lang: Optional[str] = "en"

class AnalysisResponse(BaseModel):
    status: str
    input_metadata: Dict[str, str] # <--- New Field to show input details
    data: dict

@app.post("/transcribe")
async def transcribe_endpoint(audio: UploadFile = File(...), language: Optional[str] = Form("auto")):
    temp_path = None
    try:
        suffix = f".{audio.filename.split('.')[-1]}"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await audio.read())
            temp_path = tmp.name
        
        result = transcribe_audio(temp_path, language)
        return {**result, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and os.path.exists(temp_path):
            try: gc.collect(); os.unlink(temp_path)
            except: pass

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_endpoint(request: AnalysisRequest):
    if not engine: raise HTTPException(status_code=503, detail="Engine not ready. Run build_db.py")
    
    try:
        # Run the analysis
        analysis_result = engine.analyze_case(request.english_transcript)
        
        # Return combined result
        return {
            "status": "success",
            "input_metadata": {
                "language": request.detected_lang,
                "original_text": request.original_transcript or "N/A",
                "analyzed_text": request.english_transcript
            },
            "data": analysis_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)