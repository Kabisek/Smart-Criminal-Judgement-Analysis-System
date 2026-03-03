import os
from pathlib import Path
from dotenv import load_dotenv
import motor.motor_asyncio
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

# Load .env explicitly before anything else
_env_path = Path(__file__).parent.parent.parent / ".env"  # comp2/core/database.py → backend/.env
load_dotenv(dotenv_path=_env_path, override=True)

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
print(f"[DB] Connecting using URI ending in: ...@{MONGODB_URI.split('@')[-1] if '@' in MONGODB_URI else MONGODB_URI}")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client.legal_system_db

# ── Separate collections per component ───────────────────────────────
history_comp1_collection = db.history_comp1
history_comp2_collection = db.history_comp2

async def check_database_connection():
    try:
        await db.command('ismaster')
        print("✅ MongoDB connected successfully to 'legal_system_db'")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False

# ── Shared summary model ──────────────────────────────────────────────

class HistorySummary(BaseModel):
    case_id: str
    case_name: str
    timestamp: datetime
    subject: str
    accused: str

# ── Component 1 — Legal Resource Extractor ───────────────────────────

class Comp1HistoryRecord(BaseModel):
    case_id: str
    case_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: dict          # Full analyzed_case + data + input_metadata
    subject: str = "N/A"
    accused: str = "N/A"

async def save_comp1_record(record: Comp1HistoryRecord) -> str:
    record_dict = record.model_dump()
    await history_comp1_collection.update_one(
        {"case_id": record.case_id},
        {"$set": record_dict},
        upsert=True
    )
    return record.case_id

async def get_comp1_list() -> List[HistorySummary]:
    cursor = history_comp1_collection.find(
        {}, {"case_id": 1, "case_name": 1, "timestamp": 1, "subject": 1, "accused": 1}
    ).sort("timestamp", -1)
    summaries = []
    async for doc in cursor:
        summaries.append(HistorySummary(
            case_id=doc["case_id"],
            case_name=doc["case_name"],
            timestamp=doc["timestamp"],
            subject=doc.get("subject", "N/A"),
            accused=doc.get("accused", "N/A"),
        ))
    return summaries

async def get_comp1_record(case_id: str) -> Optional[dict]:
    return await history_comp1_collection.find_one({"case_id": case_id}, {"_id": 0})

# ── Component 2 — Argument Synthesis Engine ──────────────────────────

class Comp2HistoryRecord(BaseModel):
    case_id: str
    case_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: dict          # Full arguments_report
    subject: str = "N/A"
    accused: str = "N/A"

async def save_comp2_record(record: Comp2HistoryRecord) -> str:
    record_dict = record.model_dump()
    await history_comp2_collection.update_one(
        {"case_id": record.case_id},
        {"$set": record_dict},
        upsert=True
    )
    return record.case_id

async def get_comp2_list() -> List[HistorySummary]:
    cursor = history_comp2_collection.find(
        {}, {"case_id": 1, "case_name": 1, "timestamp": 1, "subject": 1, "accused": 1}
    ).sort("timestamp", -1)
    summaries = []
    async for doc in cursor:
        summaries.append(HistorySummary(
            case_id=doc["case_id"],
            case_name=doc["case_name"],
            timestamp=doc["timestamp"],
            subject=doc.get("subject", "N/A"),
            accused=doc.get("accused", "N/A"),
        ))
    return summaries

async def get_comp2_record(case_id: str) -> Optional[dict]:
    return await history_comp2_collection.find_one({"case_id": case_id}, {"_id": 0})

# ── Legacy shared history (kept for backward compat with frontend) ────

history_shared_collection = db.history_shared

class HistoryMetadata(BaseModel):
    accused: Optional[str] = "N/A"
    subject: Optional[str] = "N/A"
    file_hash: Optional[str] = None

class HistoryRecord(BaseModel):
    case_id: str
    case_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    component1_data: dict
    component2_data: dict
    metadata: HistoryMetadata = Field(default_factory=HistoryMetadata)

async def save_history_record(record: HistoryRecord) -> str:
    record_dict = record.model_dump()
    await history_shared_collection.update_one(
        {"case_id": record.case_id},
        {"$set": record_dict},
        upsert=True
    )
    return record.case_id

async def get_history_list() -> List[HistorySummary]:
    cursor = history_shared_collection.find(
        {}, {"case_id": 1, "case_name": 1, "timestamp": 1}
    ).sort("timestamp", -1)
    summaries = []
    async for doc in cursor:
        meta = doc.get("metadata", {})
        summaries.append(HistorySummary(
            case_id=doc["case_id"],
            case_name=doc["case_name"],
            timestamp=doc["timestamp"],
            subject=meta.get("subject", "N/A"),
            accused=meta.get("accused", "N/A"),
        ))
    return summaries

async def get_history_record(case_id: str) -> Optional[dict]:
    return await history_shared_collection.find_one({"case_id": case_id}, {"_id": 0})
