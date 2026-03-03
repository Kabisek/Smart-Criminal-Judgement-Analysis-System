from fastapi import APIRouter, HTTPException
from typing import List
from comp2.core.database import (
    # Comp1
    Comp1HistoryRecord, save_comp1_record, get_comp1_list, get_comp1_record,
    # Comp2
    Comp2HistoryRecord, save_comp2_record, get_comp2_list, get_comp2_record,
    # Legacy shared
    HistoryRecord, save_history_record, get_history_list, get_history_record,
    # Shared Summary
    HistorySummary,
)

router = APIRouter(prefix="/history", tags=["history"])

# ── Legacy shared history endpoints (used by frontend saveToHistory / fetchHistoryList / fetchHistoryDetail)

@router.post("/save")
async def save_history(record: HistoryRecord):
    try:
        case_id = await save_history_record(record)
        return {"status": "success", "case_id": case_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list", response_model=List[HistorySummary])
async def list_history():
    try:
        return await get_history_list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{case_id}")
async def fetch_history(case_id: str):
    # Must be last — catches anything not matched by comp1/* or comp2/* routes
    try:
        record = await get_history_record(case_id)
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        return record
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Component 1 Routes ─────────────────────────────────────────────────

@router.post("/comp1/save")
async def save_comp1_history(record: Comp1HistoryRecord):
    try:
        case_id = await save_comp1_record(record)
        return {"status": "success", "case_id": case_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comp1/list", response_model=List[HistorySummary])
async def list_comp1_history():
    try:
        return await get_comp1_list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comp1/{case_id}")
async def fetch_comp1_history(case_id: str):
    try:
        record = await get_comp1_record(case_id)
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        return record
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Component 2 Routes ─────────────────────────────────────────────────

@router.post("/comp2/save")
async def save_comp2_history(record: Comp2HistoryRecord):
    try:
        case_id = await save_comp2_record(record)
        return {"status": "success", "case_id": case_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comp2/list", response_model=List[HistorySummary])
async def list_comp2_history():
    try:
        return await get_comp2_list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comp2/{case_id}")
async def fetch_comp2_history(case_id: str):
    try:
        record = await get_comp2_record(case_id)
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        return record
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
