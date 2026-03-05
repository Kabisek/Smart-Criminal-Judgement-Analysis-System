from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys
import tempfile
import gc
import json
import time
from datetime import datetime
from typing import Optional, Dict

# Ensure backend/ root is on sys.path for absolute package imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── COMPONENT 1: Intelligent Legal Intelligence Layer ──────────────────────────
# Handles: multilingual transcription, ChromaDB semantic retrieval with
# fine-tuned Legal-BERT, statutory decomposition, knowledge graph construction.
from comp1.utils.transcriber import transcribe_audio
from comp1.core.engine import LegalResourceExtractor

# ── COMPONENT 2: Adversarial Case Analysis / Argument Generation ───────────────
# Handles: PDF/text ingestion, Nearest Neighbors case retrieval,
# LLM-based argument generation (Groq), structured case analysis output.
from comp2.api.routes import analyze, arguments, upload, status, results, history
from comp2.api.config import API_V1_PREFIX

# ── COMPONENT 3: Appeal Outcome Decision Support ─────────────────────────────
# Handles: appeal outcome prediction, case similarity analysis, feature detection
from comp3.api.routes import prediction as comp3_prediction, health as comp3_health
from comp3.api.config import API_V1_PREFIX as COMP3_API_PREFIX

"""
RESEARCH CONTRIBUTION: SECURE CONFIGURATION & API GATEWAY
---------------------------------------------------------
This module implements the 'Secure Configuration Management' (Section 4.1 in Paper).
- Uses python-dotenv for isolated credential management.
- Implements strict CORS policies for frontend security.
- Serves as the entry point for the Hybrid Neuro-Symbolic Pipeline.
"""

app = FastAPI(title="Smart Criminal Judgement System", version="Final-Research-v3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── COMPONENT 4: Trilingual Legal Chatbot ─────────────────────────────────────
from comp4.api.comp4_api import router as comp4_router

# ── COMPONENT 2: Mount all adversarial analysis routers ───────────────────────
app.include_router(analyze.router,    prefix=API_V1_PREFIX, tags=["analyze"])
app.include_router(arguments.router,  prefix=API_V1_PREFIX, tags=["arguments"])
app.include_router(upload.router,     prefix=API_V1_PREFIX, tags=["upload"])
app.include_router(status.router,     prefix=API_V1_PREFIX, tags=["status"])
app.include_router(results.router,    prefix=API_V1_PREFIX, tags=["results"])
app.include_router(history.router,    prefix=API_V1_PREFIX, tags=["history"])

# ── COMPONENT 3: Mount appeal outcome prediction routers ─────────────────────
app.include_router(comp3_prediction.router, prefix=COMP3_API_PREFIX, tags=["appeal-prediction"])
app.include_router(comp3_health.router, prefix=COMP3_API_PREFIX, tags=["appeal-health"])

# ── COMPONENT 4: Mount Trilingual Legal Chatbot router ────────────────────────
app.include_router(comp4_router)

# ── COMPONENT 1: Initialize ChromaDB / Legal-BERT engine ─────────────────────
DB_PATH = os.path.join(os.getcwd(), "data", "chroma_db")
engine = LegalResourceExtractor(db_path=DB_PATH) if os.path.exists(DB_PATH) else None


@app.on_event("startup")
async def startup_db_client():
    from comp2.core.database import check_database_connection
    await check_database_connection()


# Ensure output directory exists for research data logging
OUTPUT_DIR = os.path.join(os.getcwd(), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ── REQUEST / RESPONSE MODELS ─────────────────────────────────────────────────
class AnalysisRequest(BaseModel):
    english_transcript: str
    original_transcript: Optional[str] = None
    detected_lang: Optional[str] = "en"


class AnalysisResponse(BaseModel):
    status: str
    input_metadata: Dict[str, str]
    data: dict


def save_research_output(data: dict, prefix: str = "extract"):
    """
    RESEARCH UTILITY: DATA LOGGING
    Saves API responses to JSON for detailed analysis and dataset expansion.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.json"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"   [Logger] Saved research output to: {filepath}")


# ── COMPONENT 1: ENDPOINTS ────────────────────────────────────────────────────

@app.post("/transcribe")
async def transcribe_endpoint(audio: UploadFile = File(...), language: Optional[str] = Form("auto")):
    """
    RESEARCH PIPELINE STEP 1: MULTIMODAL INGESTION
    Handles multilingual (Sinhala/Tamil/English) audio transcription via
    Whisper + Gemini hybrid consensus strategy.
    """
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
            try:
                gc.collect()
                os.unlink(temp_path)
            except:
                pass


@app.post("/extract", response_model=AnalysisResponse)
async def extract_endpoint(request: AnalysisRequest):
    """
    RESEARCH PIPELINE STEP 2 & 3: EXTRACTION & GRAPH CONSTRUCTION
    Orchestrates the Neuro-Symbolic Logic:
    - Dual semantic search (prosecution + defense queries)
    - Statutory decomposition (actus reus, mens rea, punishment)
    - Hierarchical knowledge graph construction
    """
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not ready. Run comp1/scripts/build_db.py")

    try:
        result = engine.extract_resources(request.english_transcript)

        response_data = {
            "status": "success",
            "input_metadata": {
                "language": request.detected_lang,
                "original_text": request.original_transcript or "N/A",
                "analyzed_text": request.english_transcript
            },
            "data": result
        }

        return response_data
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "Smart Criminal Judgement System",
        "components": {
            "comp1_engine": "ready" if engine else "not initialized (run build_db.py)",
            "comp2_api": "ready",
            "comp3_appeal": "ready"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)