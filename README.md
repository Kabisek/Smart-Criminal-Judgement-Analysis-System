---
title: Smart Criminal Judgement Analysis API
emoji: ⚖️
colorFrom: blue
colorTo: gray
sdk: docker
pinned: false
app_port: 7860
license: mit
---

# Smart-Criminal-Judgement-Analysis-System

Final year research project: legal intelligence, case analysis, appeal prediction, and trilingual legal assistant.

## Backend on Hugging Face Spaces

Deploy the FastAPI API with Docker using the root **`Dockerfile`**. Step-by-step instructions: **[HF_SPACES_DEPLOY.md](./HF_SPACES_DEPLOY.md)**.

Public URL shape: `https://<HF_USERNAME>-<SPACE_NAME>.hf.space` — use that as the API base for the Expo frontend (HTTPS).

## Local development

- Backend: `cd backend` → `pip install -r requirements.txt` → `python main.py` or `uvicorn main:app --host 0.0.0.0 --port 8000`
- Frontend: see `frontend/README-REACT-NATIVE.md`

Large models and Chroma stores can be pulled at runtime via `runtime_artifacts.py` and Google Drive URLs in `.env` (see `backend/.env.example`).
