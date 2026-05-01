# Component 2 – Complete Workflow

Adversarial Case Analysis: case analysis (Output File 1) and strategic arguments (Output File 2).

---

## 1. Prerequisites

| Requirement | Purpose |
|-------------|---------|
| Python 3.11+ | Runtime |
| `backend/requirements.txt` | Dependencies |
| `GROQ_API_KEY` in `backend/.env` | LLM (Groq) for case analysis & arguments |
| `MONGODB_URI` in `backend/.env` | History storage (optional) |

---

## 2. ChromaDB Setup (One-Time)

### 2.1 Run backend2 Notebooks

```bash
cd backend2/notebooks
```

Execute in order:

| Notebook | Purpose |
|----------|---------|
| **01_Dataset_Preparation** | Extract text from PDF judgments |
| **02_Data_Preprocessing** | Clean text, produce `merged_v2.csv` |
| **03_Feature_Engineering** | Legal-BERT embeddings → ChromaDB |

```bash
jupyter nbconvert --to notebook --execute 01_Dataset_Preparation.ipynb --output 01_executed.ipynb
jupyter nbconvert --to notebook --execute 02_Data_Preprocessing.ipynb --output 02_executed.ipynb
jupyter nbconvert --to notebook --execute 03_Feature_Engineering.ipynb --output 03_executed.ipynb --ExecutePreprocessor.timeout=1800
```

### 2.2 Deploy ChromaDB to Main Backend

```bash
# Delete old/corrupted chroma_db_comp2 if present
rm -rf Smart-Criminal-Judgement-Analysis-System/backend/data/chroma_db_comp2

# Copy ChromaDB output
cp -r backend2/data/chroma_db Smart-Criminal-Judgement-Analysis-System/backend/data/chroma_db_comp2
```

**Windows PowerShell:**
```powershell
Remove-Item -Recurse -Force "Smart-Criminal-Judgement-Analysis-System\backend\data\chroma_db_comp2" -ErrorAction SilentlyContinue
Copy-Item -Path "backend2\data\chroma_db\*" -Destination "Smart-Criminal-Judgement-Analysis-System\backend\data\chroma_db_comp2" -Recurse -Force
```

### 2.3 Optional: Copy Trained Models

For K-Means cluster prediction and KNN retrieval:

```
backend2/data/models/kmeans_model.pkl           → backend/data/models/
backend2/data/models/final_nearest_neighbors_model.pkl → backend/data/models/
```

---

## 3. Verify ChromaDB

```bash
cd Smart-Criminal-Judgement-Analysis-System/backend
python scripts/check_chromadb.py
```

Expected: `[OK] ChromaDB connected. Collection has N vectors.`

---

## 4. Run Tests (Comp2 Only)

```bash
cd Smart-Criminal-Judgement-Analysis-System/backend
python tests/test_smoke_unit.py
```

Expected: `PASSED: 12 | FAILED: 0`

---

## 5. Start Backend

```bash
cd Smart-Criminal-Judgement-Analysis-System/backend
python main.py
# or: uvicorn main:app --host 0.0.0.0 --port 8000
```

Backend: `http://localhost:8000`

---

## 6. API Endpoints (Comp2)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/analyze` | Case analysis (Output File 1) |
| POST | `/api/v1/arguments` | Strategic arguments (Output File 2) |
| POST | `/api/v1/upload` | Upload file, start analysis |
| GET | `/api/v1/status/{job_id}` | Job status |
| GET | `/api/v1/results/{job_id}` | Get results |
| GET | `/api/v1/history/list` | List saved cases |

---

## 7. Output Formats

### Output File 1 – Case Analysis (`/api/v1/analyze`)

```json
{
  "status": "success",
  "analyzed_case_file": {
    "case_header": { "file_number", "date_of_analysis", "subject" },
    "incident_timeline": { "what_happened", "where_it_happened", "key_dates" },
    "parties_and_roles": { "accused", "complainant", "doubters_witnesses" },
    "argument_synthesis": { "prosecution_logic", "defense_logic", "reasonable_doubt_factors" },
    "final_judicial_opinion": "..."
  },
  "document_text": [...],
  "source_spans": [...]
}
```

### Output File 2 – Arguments Report (`/api/v1/arguments`)

```json
{
  "similar_cases": [...],
  "cluster_id": 0,
  "prosecution_arguments": [...],
  "defense_arguments": [...],
  "adversarial_simulation": {...}
}
```

---

## 8. Pipeline Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Upload Case    │────▶│  Extract Text    │────▶│  Clean Text     │
│  (PDF/TXT/DOCX) │     │  (Processor)     │     │  (TextCleaner)   │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                           │
                    ┌──────────────────────────────────────┼──────────────────────────────────────┐
                    │                                      │                                      │
                    ▼                                      ▼                                      ▼
         ┌──────────────────┐                  ┌──────────────────┐                  ┌──────────────────┐
         │  Case Analysis   │                  │  Legal-BERT     │                  │  ChromaDB        │
         │  (LLM only)      │                  │  Embeddings     │                  │  Similar Cases   │
         │  Output File 1   │                  │  (FeatureExt)   │                  │  (Arguments)     │
         └──────────────────┘                  └────────┬───────┘                  └────────┬────────┘
                                                          │                                      │
                                                          ▼                                      ▼
                                               ┌──────────────────┐                  ┌──────────────────┐
                                               │  K-Means Cluster │                  │  Arguments       │
                                               │  Prediction      │                  │  Report          │
                                               │  (optional)      │                  │  Output File 2   │
                                               └──────────────────┘                  └──────────────────┘
```

---

## 9. Troubleshooting

| Issue | Action |
|-------|--------|
| ChromaDB `range start index` / `PanicException` | Delete `chroma_db_comp2`, re-run notebooks 01–03, copy again |
| `Missing key: case_summary` | Use comp2 keys: `case_header`, `incident_timeline`, etc. |
| LLM 429 Rate limit | Wait or upgrade Groq tier |
| `GROQ_API_KEY` missing | Add to `backend/.env` |
| ChromaDB empty | Run backend2 Notebook 03, then copy to `chroma_db_comp2` |

---

## 10. File Layout

```
Smart-Criminal-Judgement-Analysis-System/
├── backend/
│   ├── .env                    # GROQ_API_KEY, MONGODB_URI
│   ├── main.py                 # FastAPI app
│   ├── data/
│   │   ├── chroma_db_comp2/    # ChromaDB (from backend2)
│   │   ├── models/             # kmeans_model.pkl, final_nearest_neighbors_model.pkl
│   │   └── evaluation/sample_cases/
│   ├── comp2/
│   │   ├── api/routes/         # analyze, arguments, upload, status, results, history
│   │   ├── src/reasoning/      # enhanced_agent.py
│   │   └── src/retrieval/      # chroma_store.py
│   ├── scripts/check_chromadb.py
│   └── tests/test_smoke_unit.py
├── uploads/                    # case1.txt, case2.txt (sample cases)
└── backend2/
    ├── notebooks/              # 01, 02, 03
    └── data/
        ├── chroma_db/           # Output of Notebook 03
        └── processed/merged_v2.csv
```
