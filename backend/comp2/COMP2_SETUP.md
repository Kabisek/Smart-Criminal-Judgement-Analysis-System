# Component 2 Setup (ChromaDB-only)

Component 2 uses **ChromaDB** as the sole retrieval store. No `feature_vectors.pkl`, `merged_v2.csv`, or NN model at runtime.

## Prerequisites

1. Run **backend2** notebooks 01, 02, 03 to produce:
   - `backend2/data/chroma_db/` (with enriched metadata: case_id, judge_names, judge_statement, year)

## Deploy to Main Pipeline

Copy the ChromaDB output to the main backend:

```
backend2/data/chroma_db/  →  Smart-Criminal-Judgement-Analysis-System/backend/data/chroma_db_comp2/
```

Component 1 uses `backend/data/chroma_db` (collection: legal_knowledge_base).  
Component 2 uses `backend/data/chroma_db_comp2` (collection: legal_cases). They do not conflict.

## Verify

Start the backend and hit `/api/v1/analyze` or `/api/v1/arguments` with a case file.
