# Hugging Face Spaces (Docker) — FastAPI backend only.
# Spaces route public traffic to port 7860.
FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/

WORKDIR /app/backend

ENV PYTHONUNBUFFERED=1
# HF Spaces default; override in Space settings if needed
ENV PORT=7860

EXPOSE 7860

# No .env in image — set secrets in Space → Settings → Variables and secrets
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-7860}"]
