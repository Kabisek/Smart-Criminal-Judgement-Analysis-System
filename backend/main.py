from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# --- PATH SETUP ---
# Get the absolute path of the project root directory
# (Goes up one level from 'backend' folder)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add project root to python path so we can import 'core'
sys.path.append(BASE_DIR)

from core.engine import LegalReasoningEngine

# --- APP INITIALIZATION ---
app = FastAPI(
    title="Smart Criminal Judgement Analysis System",
    description="Advanced AI System for Legal Reasoning, Clustering, and Graph Generation",
    version="2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GLOBAL AI ENGINE ---
# Construct the absolute path to the database
DB_PATH = os.path.join(BASE_DIR, "data", "chroma_db")

print(f"⏳ Initializing Legal AI Engine...")
print(f"   -> Database Path: {DB_PATH}")

if not os.path.exists(DB_PATH):
    print("❌ CRITICAL ERROR: Database folder not found at path!")
    print("   Please run 'python scripts/build_db.py' first.")
    sys.exit(1)

try:
    engine = LegalReasoningEngine(db_path=DB_PATH)
    print("✅ System Online.")
except Exception as e:
    print(f"❌ Failed to load AI Engine: {e}")
    sys.exit(1)

# --- DATA MODELS ---
class AnalysisRequest(BaseModel):
    transcript: str

class AnalysisResponse(BaseModel):
    status: str
    data: dict

# --- ENDPOINTS ---

@app.get("/")
def health_check():
    return {"status": "active", "module": "Legal Reasoning Core"}

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_case(request: AnalysisRequest):
    try:
        if not request.transcript or len(request.transcript) < 5:
            raise HTTPException(status_code=400, detail="Transcript is too short.")

        print(f"🔍 Analyzing case: {request.transcript[:50]}...")
        result = engine.analyze_case(request.transcript)
        
        return {
            "status": "success",
            "data": result
        }
    
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)