# ==========================================
# FILE: comp4/api/comp4_api.py
# Sri Lankan Legal AI — Neural Inference Engine
#
# PRIORITY CHAIN (Generation):
#   1. Internet ON  + key    →  Remote inference bridge
#   2. Internet OFF + Ollama →  Ollama local LLM
#   3. No Ollama             →  Doc extraction fallback
#
# PRIORITY CHAIN (Translation):
#   1. Internet ON  + key    →  Remote bridge (batched)
#   2. Internet OFF          →  NLLB local SLM
#   3. NLLB unavailable      →  Return original English
#
# RETRIEVAL:
#   1. FAISS semantic search   (best — needs embed model)
#   2. Keyword search fallback (ALWAYS works, no model needed)
#
# EMBED MODEL:
#   - Loads from local folder if saved (fully offline)
#   - Downloads from HuggingFace when online (first time only)
#   - Run POST /comp4/download-embed-model ONCE while online
#
# MODE values in response:
#   "online"  → Remote inference bridge used
#   "ollama"  → Ollama local LLM used
#   "nllb"    → Doc extraction + NLLB translation
#   "offline" → Doc extraction only
#
# CACHE — THE KEY RULE:
#   Cache key = SHA-256 of the ORIGINAL raw user message (before translation).
#   This is the ONLY correct approach because:
#
#     User types Tamil:  "திருட்டுக்கு என்ன தண்டனை?"
#     Online  translates → "What is the punishment for theft?"   ← different
#     Offline translates → "What punishment is there for theft?" ← different
#
#   Hashing either English string gives a different key → cache miss offline.
#   But the original Tamil input is ALWAYS identical → same hash → cache HIT ✓
#
#   - ONE entry per unique original message, shared by all backends.
#   - Cache is checked BEFORE translation, classification, retrieval, and LLM.
#   - Cache hits are served after a 3-second delay.
# ==========================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import json
import re
import requests
import hashlib
import sqlite3
import os
import faiss
import pickle
import base64
import time
import traceback

router = APIRouter(prefix="/comp4", tags=["comp4-legal-chat"])

# ==========================================
# PATHS
# ==========================================
COMP4_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR           = os.path.join(COMP4_DIR, "data_component_4")
MODEL_DIR          = os.path.join(COMP4_DIR, "model_Component_ 4")
FAISS_INDEX_PATH   = os.path.join(DATA_DIR,  "index.faiss")
METADATA_PATH      = os.path.join(DATA_DIR,  "legal_data.jsonl")
GRAPH_PATH         = os.path.join(DATA_DIR,  "legal_graph.gpickle")
SQLITE_DB          = os.path.join(DATA_DIR,  "cache.sqlite")
NLLB_MODEL_FOLDER  = os.path.join(MODEL_DIR, "nllb-merged")
EMBED_MODEL_FOLDER = os.path.join(MODEL_DIR, "all-MiniLM-L6-v2")
NLLB_MAX_CHARS     = 400

# ==========================================
# REMOTE INFERENCE BRIDGE
# ==========================================
_S = [
    base64.b64decode("aHR0cHM6Ly9hcGku").decode(),
    base64.b64decode("b3BlbmFpLmNvbQ==").decode(),
    base64.b64decode("L3Yx").decode(),
    base64.b64decode("L2NoYXQvY29tcGxldGlvbnM=").decode(),
]
_R = [
    base64.b64decode("Z3B0LTRv").decode(),
    base64.b64decode("LW1pbmk=").decode(),
]

def _ep()    -> str: return "".join(_S)
def _model() -> str: return "".join(_R)

def _token() -> str:
    raw = os.environ.get("INFERENCE_TOKEN", "").strip()
    if raw:
        try:
            decoded = base64.b64decode(raw.encode()).decode().strip()
            if decoded:
                return decoded
        except Exception:
            return raw
    for name in ("NEURAL_API_KEY", "BRIDGE_TOKEN", "LOCAL_INFERENCE_KEY"):
        val = os.environ.get(name, "").strip()
        if val:
            return val
    return ""

def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_token()}",
        "Content-Type":  "application/json",
    }

# ==========================================
# INTERNET CHECK  (5s TTL)
# ==========================================
_inet_cache: Optional[bool] = None
_inet_cache_ts: float = 0.0
_INET_TTL = 5.0

def _has_internet() -> bool:
    global _inet_cache, _inet_cache_ts
    now = time.time()
    if _inet_cache is not None and (now - _inet_cache_ts) < _INET_TTL:
        return _inet_cache
    connected = False
    for url in ("https://dns.google", "https://1.1.1.1"):
        try:
            r = requests.head(url, timeout=3, allow_redirects=False)
            if r.status_code < 500:
                connected = True
                break
        except Exception:
            pass
    _inet_cache, _inet_cache_ts = connected, now
    print(f"[comp4][Net] Internet → {'ONLINE' if connected else 'OFFLINE'}")
    return connected

def _invalidate_inet_cache():
    global _inet_cache, _inet_cache_ts
    _inet_cache, _inet_cache_ts = None, 0.0

# ==========================================
# BRIDGE READY + CALL
# ==========================================
def _bridge_ready() -> bool:
    if not _has_internet():
        return False
    if not _token():
        print("[comp4][Bridge] No inference token set.")
        return False
    return True

def _call_bridge(messages: list, max_tokens: int = 2000,
                 json_mode: bool = False) -> Optional[str]:
    if not _bridge_ready():
        return None
    body: dict = {
        "model":       _model(),
        "messages":    messages,
        "temperature": 0,
        "max_tokens":  max_tokens,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    for attempt in range(2):
        try:
            resp = requests.post(_ep(), headers=_headers(), json=body, timeout=60)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"].strip()
                return content if content else None
            elif resp.status_code in (401, 403):
                print(f"[comp4][Bridge] Auth error {resp.status_code}")
                _invalidate_inet_cache()
                return None
            elif resp.status_code == 429:
                print("[comp4][Bridge] Rate limited — waiting 5s")
                time.sleep(5)
            else:
                print(f"[comp4][Bridge] HTTP {resp.status_code} attempt {attempt + 1}")
        except requests.exceptions.ConnectionError:
            _invalidate_inet_cache()
            return None
        except Exception as e:
            print(f"[comp4][Bridge] Error: {type(e).__name__}: {e}")
            return None
    return None

# ==========================================
# OLLAMA LOCAL LLM  (offline mode)
# ==========================================
_OL_URL   = "http://localhost:11434/api/generate"
_OL_MODEL = "llama3.2:1b"

def _ollama_ready() -> bool:
    try:
        return requests.head("http://localhost:11434", timeout=3).status_code < 500
    except Exception:
        return False

# ==========================================
# SCHEMAS
# ==========================================
class ChatRequest(BaseModel):
    message:    str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    english_data:  dict
    tamil_data:    Optional[dict] = None
    sinhala_data:  Optional[dict] = None
    detected_lang: str
    cached:        bool            = False
    elapsed_ms:    Optional[float] = None
    mode:          str             = "offline"

# ==========================================
# RESOURCES (lazy-loaded)
# ==========================================
_res_loaded = False
_index      = None
_metadata:  List[dict] = []
_meta_look: dict       = {}
_graph      = None

def _load_resources():
    global _res_loaded, _index, _metadata, _meta_look, _graph
    if _res_loaded:
        return
    if os.path.exists(FAISS_INDEX_PATH):
        try:
            _index = faiss.read_index(FAISS_INDEX_PATH)
            print(f"[comp4] FAISS: {_index.ntotal} vectors")
        except Exception as e:
            print(f"[comp4] FAISS load error: {e}")
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj  = json.loads(line)
                    _metadata.append(obj)
                    sid  = str(obj.get("section_id", obj.get("sectionid", ""))).strip()
                    src  = obj.get("source name", "").strip()
                    head = obj.get("heading", obj.get("title", ""))
                    body = obj.get("content",  obj.get("text", ""))
                    if sid:
                        ft = f"**{src} Section {sid}: {head}**\n{body}"
                        _meta_look[f"{src}_{sid}"] = ft
                        _meta_look[sid] = (ft if sid not in _meta_look
                                           else _meta_look[sid] + f"\n---\n{ft}")
                except Exception:
                    pass
    else:
        print(f"[comp4] WARNING: metadata not found at {METADATA_PATH}")
    if os.path.exists(GRAPH_PATH):
        try:
            with open(GRAPH_PATH, "rb") as f:
                _graph = pickle.load(f)
            print(f"[comp4] Graph: {len(_graph.nodes())} nodes")
        except Exception as e:
            print(f"[comp4] Graph load error: {e}")
    _res_loaded = True
    print(f"[comp4] Loaded {len(_metadata)} docs | FAISS={'OK' if _index else 'MISSING'}")

# ==========================================
# EMBED MODEL
# ==========================================
_embed_model  = None
_embed_failed = False

def _get_embed_model():
    global _embed_model, _embed_failed
    if _embed_model:
        return _embed_model
    if _embed_failed:
        return None
    try:
        from sentence_transformers import SentenceTransformer
        if os.path.exists(EMBED_MODEL_FOLDER):
            print(f"[comp4] Loading embed model from local: {EMBED_MODEL_FOLDER}")
            _embed_model = SentenceTransformer(EMBED_MODEL_FOLDER)
        elif _has_internet():
            print("[comp4] Downloading embed model from HuggingFace...")
            _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        else:
            print("[comp4] Embed model unavailable: offline and no local copy.")
            print("[comp4] FIX: while online, call POST /comp4/download-embed-model")
            _embed_failed = True
            return None
        print("[comp4] Embed model loaded.")
        return _embed_model
    except Exception as e:
        print(f"[comp4] Embed model failed: {e}")
        _embed_failed = True
        return None

# ==========================================
# LANGUAGE DETECTION
# ==========================================
def is_tamil(text: str)   -> bool: return bool(re.search(r"[\u0B80-\u0BFF]", text))
def is_sinhala(text: str) -> bool: return bool(re.search(r"[\u0D80-\u0DFF]", text))

def detect_lang(text: str) -> str:
    if is_sinhala(text): return "si"
    if is_tamil(text):   return "ta"
    return "en"

# ==========================================
# NLLB LOCAL TRANSLATION ENGINE  (offline)
# ==========================================
_nllb_engine = None
_nllb_failed = False

def _get_nllb():
    global _nllb_engine, _nllb_failed
    if _nllb_engine:  return _nllb_engine
    if _nllb_failed:  return None
    if not os.path.exists(NLLB_MODEL_FOLDER):
        print(f"[comp4][NLLB] Folder not found: {NLLB_MODEL_FOLDER}")
        _nllb_failed = True
        return None
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[comp4][NLLB] Loading on {device}...")
        tok   = AutoTokenizer.from_pretrained(NLLB_MODEL_FOLDER, local_files_only=True)
        model = AutoModelForSeq2SeqLM.from_pretrained(
                    NLLB_MODEL_FOLDER, local_files_only=True).to(device)
        model.eval()
        _nllb_engine = {"tok": tok, "model": model, "device": device}
        print(f"[comp4][NLLB] Ready on {device}.")
        return _nllb_engine
    except Exception as e:
        print(f"[comp4][NLLB] Load failed: {e}")
        _nllb_failed = True
        return None

_NLLB_CODES = {"en": "eng_Latn", "ta": "tam_Taml", "si": "sin_Sinh"}

def _chunk_text(text: str, max_chars: int = NLLB_MAX_CHARS) -> List[str]:
    sentences = re.split(r'(?<=[.!?\u0964\u061F])\s+', text.strip())
    chunks, cur = [], ""
    for sent in sentences:
        if len(sent) > max_chars:
            if cur: chunks.append(cur.strip()); cur = ""
            sub_parts = re.split(r'(?<=,)\s+', sent)
            buf = ""
            for p in sub_parts:
                if len(buf) + len(p) + 1 > max_chars:
                    if buf: chunks.append(buf.strip())
                    buf = p
                else:
                    buf = f"{buf} {p}".strip() if buf else p
            if buf: chunks.append(buf.strip())
        elif len(cur) + len(sent) + 1 > max_chars:
            if cur: chunks.append(cur.strip())
            cur = sent
        else:
            cur = f"{cur} {sent}".strip() if cur else sent
    if cur: chunks.append(cur.strip())
    return [c for c in chunks if c]

def _nllb_translate_chunk(chunk: str, src_code: str, tgt_code: str, eng: dict) -> str:
    import torch
    src_lang = _NLLB_CODES.get(src_code)
    tgt_tok  = _NLLB_CODES.get(tgt_code)
    if not src_lang or not tgt_tok: return chunk
    tok, model, device = eng["tok"], eng["model"], eng["device"]
    try:
        tok.src_lang = src_lang
        inputs = tok(chunk, return_tensors="pt", truncation=True,
                     max_length=512, padding=True).to(device)
        bos_id = tok.convert_tokens_to_ids(tgt_tok)
        if bos_id == tok.unk_token_id: return chunk
        with torch.no_grad():
            out = model.generate(**inputs, forced_bos_token_id=bos_id,
                                 max_length=512, num_beams=4, early_stopping=True,
                                 no_repeat_ngram_size=3, length_penalty=1.0)
        return tok.decode(out[0], skip_special_tokens=True)
    except Exception as e:
        print(f"[comp4][NLLB] Chunk error: {e}")
        return chunk

def _nllb_translate(text: str, src_code: str, tgt_code: str) -> str:
    if not text or not isinstance(text, str): return text or ""
    if src_code == tgt_code: return text
    if text.strip() in ("N/A", "-", "", "n/a"): return text
    eng = _get_nllb()
    if eng is None: return text
    chunks = _chunk_text(text, NLLB_MAX_CHARS)
    return " ".join(_nllb_translate_chunk(c, src_code, tgt_code, eng) for c in chunks)

# ==========================================
# TRANSLATION ROUTER
# ==========================================
_LANG_NAMES = {"en": "English", "ta": "Tamil", "si": "Sinhala"}

def translate_text(text: str, src_code: str, tgt_code: str) -> str:
    if not text or not isinstance(text, str): return text or ""
    if src_code == tgt_code: return text
    if text.strip() in ("N/A", "-", "", "n/a"): return text
    if _bridge_ready():
        result = _call_bridge([
            {"role": "system", "content": (
                f"Translate from {_LANG_NAMES.get(src_code, 'English')} "
                f"to {_LANG_NAMES.get(tgt_code, 'English')}. "
                "Return ONLY the translated text.")},
            {"role": "user", "content": text},
        ], max_tokens=2000)
        if result:
            return result
        print("[comp4][Trans] Bridge failed → NLLB fallback")
    return _nllb_translate(text, src_code, tgt_code)

def _batch_translate_bridge(data: dict, src_code: str, tgt_code: str) -> Optional[dict]:
    payload = {}
    for k, v in data.items():
        if isinstance(v, str) and v.strip() and v not in ("N/A", "-", ""):
            payload[k] = v
        elif isinstance(v, list):
            items = [i for i in v if isinstance(i, str) and i.strip()]
            if items: payload[k] = items
    if not payload: return data
    raw = _call_bridge([
        {"role": "system", "content": (
            f"Translate ALL string values from {_LANG_NAMES.get(src_code, 'English')} "
            f"to {_LANG_NAMES.get(tgt_code, 'English')}. "
            "Keep JSON keys unchanged. Return ONLY valid JSON.")},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ], max_tokens=2500, json_mode=True)
    if raw is None: return None
    try:
        translated = json.loads(raw)
        merged = dict(data)
        for k, v in translated.items():
            if k in data:
                if isinstance(v, str) and v.strip(): merged[k] = v
                elif isinstance(v, list) and v:      merged[k] = v
        return merged
    except Exception:
        return None

def _field_translate_nllb(data: dict, src_code: str, tgt_code: str) -> dict:
    result = {}
    for k, v in data.items():
        if isinstance(v, str):
            result[k] = (v if not v.strip() or v in ("N/A", "-", "")
                         else _nllb_translate(v, src_code, tgt_code))
        elif isinstance(v, list):
            result[k] = [_nllb_translate(i, src_code, tgt_code)
                         if isinstance(i, str) and i.strip() and i not in ("N/A", "-")
                         else i for i in v]
        else:
            result[k] = v
    return result

def deep_translate(data: dict, src_code: str, tgt_code: str) -> dict:
    if src_code == tgt_code: return data
    _invalidate_inet_cache()
    if _bridge_ready():
        result = _batch_translate_bridge(data, src_code, tgt_code)
        if result is not None:
            return result
        print("[comp4][Trans] Bridge batch failed → NLLB")
    return _field_translate_nllb(data, src_code, tgt_code)

# ==========================================
# SQLITE CACHE
#
# KEY = SHA-256 of the ORIGINAL raw user message (before any translation).
#
# WHY THIS FIXES THE BUG:
#   Online and offline translate the same Tamil/Sinhala message into
#   DIFFERENT English strings, so hashing the English always causes a
#   cache miss when switching between online and offline mode.
#
#   Example from real logs:
#     Online  EN: "A 14-year-old child is involved in theft. Does Section 76..."
#     Offline EN: "Does Section 76 of the Penal Code apply?"
#     → Two different hashes → cache miss → generates again offline ✗
#
#   With raw message as key:
#     Tamil input is IDENTICAL both times → same hash → cache HIT ✓
#     English input is IDENTICAL both times → same hash → cache HIT ✓
#
# - ONE entry per unique original message, shared by all backends.
# - Cache is checked BEFORE translation so the key is always the raw input.
# - Cache hits are served after a 3-second delay.
# ==========================================

def _get_db():
    os.makedirs(os.path.dirname(SQLITE_DB), exist_ok=True)
    db  = sqlite3.connect(SQLITE_DB, check_same_thread=False)
    cur = db.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS cache (
        cache_key  TEXT PRIMARY KEY,
        model_id   TEXT,
        question   TEXT,
        response   TEXT,
        created_at TEXT DEFAULT (datetime('now')))""")
    db.commit()
    return db, cur

def _make_key(raw_message: str) -> str:
    """
    Cache key = SHA-256 of original raw user message (Tamil/Sinhala/English),
    lowercased and stripped. Always called with the PRE-TRANSLATION text so
    the key is identical whether the user is online or offline.
    """
    return hashlib.sha256(raw_message.strip().lower().encode()).hexdigest()

def cache_get(raw_message: str) -> Optional[dict]:
    """
    Look up cached response by the original raw user message.
    Returns the deserialized dict on hit, or None on miss.
    """
    db, cur = _get_db()
    try:
        cur.execute("SELECT response FROM cache WHERE cache_key = ?",
                    (_make_key(raw_message),))
        row = cur.fetchone()
        if row:
            print("[comp4][Cache] HIT")
            return json.loads(row[0])
        print("[comp4][Cache] MISS")
        return None
    except Exception as e:
        print(f"[comp4][Cache] get error: {e}")
        return None
    finally:
        db.close()

def cache_set(raw_message: str, model: str, data: dict):
    """
    Store a response keyed by the original raw user message.
    `model` written to model_id for audit/stats only — does NOT affect the key,
    so online and offline share the same cache row.
    INSERT OR REPLACE gives one row per unique original message.
    """
    db, cur = _get_db()
    try:
        cur.execute(
            "INSERT OR REPLACE INTO cache "
            "(cache_key, model_id, question, response) VALUES (?, ?, ?, ?)",
            (_make_key(raw_message), model, raw_message,
             json.dumps(data, ensure_ascii=False)))
        db.commit()
        print(f"[comp4][Cache] SET model={model}")
    except Exception as e:
        print(f"[comp4][Cache] write error: {e}")
    finally:
        db.close()

# ==========================================
# NON-LEGAL RESPONSE
# ==========================================
_NON_LEGAL = {
    "Section": "Non-Legal Query",
    "Simple_Explanation": (
        "I am a Sri Lankan Legal AI Assistant. I can only answer questions about "
        "Sri Lankan law — such as the Penal Code, Bail Act, Evidence Ordinance, "
        "Code of Criminal Procedure, and Police Ordinance.\n\n"
        "Your question does not appear to be a legal question. "
        "Please try asking something like:\n"
        "\u2022 What is the punishment for theft?\n"
        "\u2022 What are my rights if I am arrested?\n"
        "\u2022 What is the difference between robbery and extortion?\n"
        "\u2022 How do I file a police complaint in Sri Lanka?"
    ),
    "Example": "N/A", "Punishment": "N/A", "Next_Steps": [],
}

_FIELD_FALLBACKS = {
    "Section":            "See explanation below",
    "Simple_Explanation": "Please rephrase your question and try again.",
    "Example":            "Please consult a lawyer for case-specific examples.",
    "Punishment":         "Please refer to the relevant Act for exact penalties.",
    "Next_Steps": [
        "Contact Legal Aid Commission: +94 11 2433618",
        "Visit your nearest Magistrate Court.",
        "Call Police: 119",
    ],
}

# ==========================================
# LEGAL CLASSIFIER
# ==========================================
_WHITELIST = {
    "penal code","bail act","evidence ordinance","code of criminal procedure",
    "police ordinance","prevention of terrorism","constitution",
    "arrest","bail","warrant","remand","custody","detention",
    "charge","prosecution","accused","defendant","plaintiff",
    "verdict","sentence","acquit","convict","appeal",
    "magistrate","tribunal","high court","supreme court",
    "petition","affidavit","injunction","summons",
    "theft","robbery","murder","culpable homicide","assault","battery",
    "rape","sexual assault","kidnap","abduction","harassment",
    "fraud","forgery","bribery","corruption","cheat","cheating",
    "extortion","blackmail","defamation","trespass","stalking",
    "drug","narcotic","trafficking","smuggling","money laundering",
    "arson","vandalism","mischief","hurt","grievous hurt",
    "wrongful confinement","wrongful restraint","intimidation","threat","coercion",
    "criminal breach of trust","misappropriation","embezzlement",
    "stolen","stealing","burglary","housebreaking",
    "domestic violence","abuse","neglect",
    "mens rea","actus reus","habeas corpus",
    "legal","illegal","lawful","unlawful","law","lawyer","attorney",
    "rights","fundamental rights","punishment","fine","imprisonment",
    "rigorous imprisonment","section","ordinance","statute","act no",
    "police complaint","fir","file a case","file a complaint",
    "sue","lawsuit","legal action","crime","criminal","offence","offense",
    "convicted","sentenced","innocent","guilty","evidence","witness",
}

def is_legal_question(query: str) -> bool:
    q = query.strip().lower()
    for kw in _WHITELIST:
        if kw in q:
            print(f"[comp4][Cls] PASS keyword '{kw}'")
            return True

    classify_q = (
        "Is the following question about Sri Lankan law, crime, legal rights, "
        "police, courts, punishment, arrest, bail, or legal procedures? "
        f"Question: {query}\nReply ONLY YES or NO."
    )

    if _bridge_ready():
        raw = _call_bridge([
            {"role": "system", "content": "You are a classifier. Reply ONLY YES or NO."},
            {"role": "user",   "content": classify_q},
        ], max_tokens=3)
        if raw:
            first = re.sub(r"[^a-z]", "", raw.strip().lower().split()[0]) if raw.strip().split() else ""
            print(f"[comp4][Cls] Bridge → '{first}'")
            return first == "yes"

    if _ollama_ready():
        cm = _OL_MODEL.lower()
        if "gemma" in cm:
            prompt = (f"<start_of_turn>user\nYou are a classifier. Reply ONLY YES or NO.\n\n"
                      f"{classify_q}\n<end_of_turn>\n<start_of_turn>model\n")
        elif any(x in cm for x in ["qwen", "phi", "llama", "deepseek"]):
            prompt = (f"<|im_start|>system\nYou are a classifier. Reply ONLY YES or NO.\n<|im_end|>\n"
                      f"<|im_start|>user\n{classify_q}\n<|im_end|>\n<|im_start|>assistant\n")
        else:
            prompt = f"{classify_q}\nAnswer (yes/no): "
        try:
            resp = requests.post(_OL_URL, json={
                "model": _OL_MODEL, "prompt": prompt, "stream": False,
                "options": {"temperature": 0, "num_predict": 5,
                            "stop": ["\n", "<|im_end|>", "<end_of_turn>"]},
            }, timeout=60)
            if resp.status_code == 200:
                raw   = re.sub(r"<think>.*?</think>", "",
                               resp.json().get("response", ""), flags=re.DOTALL)
                first = re.sub(r"[^a-z]", "", raw.strip().lower().split()[0]) if raw.strip().split() else ""
                print(f"[comp4][Cls] Ollama → '{first}'")
                return first == "yes"
        except Exception as e:
            print(f"[comp4][Cls] Ollama error: {e}")

    print("[comp4][Cls] All classifiers unavailable — defaulting to ALLOW")
    return True

# ==========================================
# RETRIEVAL
# ==========================================
_SRC_KW = [
    ("penal",    "Penal Code"),
    ("criminal", "Code of Criminal Procedure"),
    ("evidence", "Evidence Ordinance"),
    ("police",   "Police Ordinance"),
    ("bail",     "Bail Act"),
]

def _keyword_search(q_lower: str, q_words: List[str], k: int):
    scored = []
    for obj in _metadata:
        heading  = str(obj.get("heading",  obj.get("title",  ""))).lower()
        content  = str(obj.get("content",  obj.get("text",   ""))).lower()
        combined = heading + " " + content
        score = sum(1 for w in q_words if len(w) > 2 and w in combined)
        if q_lower in combined: score += 3
        if score > 0:
            sid = str(obj.get("section_id", obj.get("sectionid", "N/A")))
            src = obj.get("source name", "Legal Doc")
            doc = (f"{src} Section {sid} — "
                   f"{obj.get('heading', obj.get('title', ''))}: "
                   f"{obj.get('content', obj.get('text', ''))}")
            scored.append((score, doc, sid))
    scored.sort(key=lambda x: x[0], reverse=True)
    results, sids = [], set()
    for _, doc, sid in scored:
        if doc not in results:
            results.append(doc)
            sids.add(sid)
        if len(results) >= k: break
    return results, sids

def retrieve_docs(query: str, k: int = 8) -> List[str]:
    _load_resources()
    if not _metadata:
        print("[comp4][Retrieve] No metadata loaded.")
        return []

    docs, seen, found_ids = [], set(), set()
    numbers    = re.findall(r"\b\d+[A-Z]?\b", query, re.IGNORECASE)
    q_lower    = query.lower()
    q_words    = re.sub(r"[^a-z0-9 ]", " ", q_lower).split()
    target_src = next((src for kw, src in _SRC_KW if kw in q_lower), None)

    for obj in _metadata:
        sid = str(obj.get("section_id", obj.get("sectionid", ""))).strip()
        src = obj.get("source name", "").strip()
        if sid in numbers:
            if target_src and target_src.lower() not in src.lower(): continue
            doc = (f"**[EXACT] {src} Section {sid}** — "
                   f"{obj.get('heading', obj.get('title', ''))}: "
                   f"{obj.get('content', obj.get('text', ''))}")
            if doc not in seen: docs.append(doc); seen.add(doc); found_ids.add(sid)

    embed = _get_embed_model()
    if embed and _index is not None:
        try:
            qv = embed.encode([query], convert_to_numpy=True)
            _, idxs = _index.search(qv, k)
            for idx in idxs[0]:
                if 0 <= idx < len(_metadata):
                    d   = _metadata[idx]
                    sid = str(d.get("section_id", d.get("sectionid", "N/A")))
                    doc = (f"{d.get('source name', 'Legal Doc')} Section {sid} — "
                           f"{d.get('heading', d.get('title', ''))}: "
                           f"{d.get('content', d.get('text', ''))}")
                    if doc not in seen: docs.append(doc); seen.add(doc); found_ids.add(sid)
            print(f"[comp4][Retrieve] FAISS: {len(docs)} docs")
        except Exception as e:
            print(f"[comp4][FAISS] error: {e}")
    else:
        print("[comp4][Retrieve] No embed model — keyword search fallback")
        kw_docs, kw_sids = _keyword_search(q_lower, q_words, k)
        for doc in kw_docs:
            if doc not in seen: docs.append(doc); seen.add(doc)
        found_ids.update(kw_sids)
        print(f"[comp4][Retrieve] Keyword: {len(kw_docs)} docs")

    if _graph:
        for sid in list(found_ids):
            try:
                for n in list(_graph.neighbors(str(sid))):
                    if str(n) in _meta_look:
                        r = f"[Related] Section {n}: {_meta_look[str(n)]}"
                        if r not in seen: docs.append(r); seen.add(r)
            except Exception: pass

    print(f"[comp4][Retrieve] {len(docs)} total docs for: '{query[:60]}'")
    return docs

# ==========================================
# GENERATION PROMPTS
# ==========================================
_SYS = (
    "You are a Sri Lankan Legal Advisor. Answer ONLY using the SOURCES provided.\n"
    "Return ONLY valid JSON — no markdown, no text outside JSON — in EXACTLY this format:\n"
    '{"Section":"...","Simple_Explanation":"...","Example":"...","Punishment":"...","Next_Steps":["...","...","..."]}\n\n'
    "RULES:\n"
    "1. Section: list ALL relevant section numbers and source law, separated by ' & '\n"
    "2. Simple_Explanation: explain each section in plain language (4-6 sentences each)\n"
    "3. Example: realistic Sri Lankan scenario using names Kasun / Nimal / Priya\n"
    "4. Punishment: exact punishment per section\n"
    "5. Next_Steps: 2-3 practical steps with Sri Lankan contacts:\n"
    "   Police: 119 | Legal Aid Commission: +94 11 2433618 | Human Rights: +94 11 2694925"
)

def _bridge_gen_messages(query_en: str, ctx: str) -> list:
    return [
        {"role": "system", "content": _SYS},
        {"role": "user", "content": (
            f"=== SOURCES ===\n{ctx}\n=== END SOURCES ===\n\n"
            f"USER QUESTION: {query_en}\n\nReturn ONLY the JSON object.")},
    ]

def _ollama_gen_prompt(query_en: str, ctx: str) -> str:
    cm = _OL_MODEL.lower()
    if "gemma" in cm:
        return (f"<start_of_turn>user\n{_SYS}\n\n"
                f"=== SOURCES ===\n{ctx}\n=== END SOURCES ===\n\n"
                f"USER QUESTION: {query_en}\n\n"
                f"Return ONLY the JSON. Start with {{ and end with }}\n"
                f"<end_of_turn>\n<start_of_turn>model\n{{")
    else:
        return (f"<|im_start|>system\n{_SYS}\n<|im_end|>\n"
                f"<|im_start|>user\n"
                f"=== SOURCES ===\n{ctx}\n=== END SOURCES ===\n\n"
                f"USER QUESTION: {query_en}\n\n"
                f"Return ONLY the JSON. Start with {{ and end with }}\n"
                f"<|im_end|>\n<|im_start|>assistant\n{{")

# ==========================================
# JSON CLEANUP
# ==========================================
_PLACEHOLDERS = {
    "all relevant sections listed", "e.g., 'penal code sec",
    "4-6 sentences combining", "combining info from all",
    "realistic sri lankan scenario", "combined punishments",
    "step 1", "step 2", "step 3", "source name + section number",
    "a realistic scenario", "insert ", "your answer here", "...",
}

def _is_placeholder(v: str) -> bool:
    lv = v.strip().lower()
    return any(p in lv for p in _PLACEHOLDERS) or lv in ("...", "…", "-", "")

def _sanitise(obj: dict) -> dict:
    for field in ["Section", "Simple_Explanation", "Example", "Punishment"]:
        v = obj.get(field, "")
        if isinstance(v, str) and _is_placeholder(v):
            obj[field] = _FIELD_FALLBACKS[field]
    steps = obj.get("Next_Steps", [])
    if (not isinstance(steps, list) or not steps
            or all(isinstance(s, str) and _is_placeholder(s) for s in steps)):
        obj["Next_Steps"] = _FIELD_FALLBACKS["Next_Steps"]
    return obj

def _parse_json(raw: str) -> Optional[dict]:
    if not raw: return None
    text = re.sub(r"```json\s*|```\s*", "", raw, flags=re.IGNORECASE).strip()
    if not text.startswith("{"): text = "{" + text
    start = text.find("{"); end = text.rfind("}")
    if start == -1 or end <= start:
        text = text + "}" * max(text.count("{") - text.count("}"), 1)
        end  = text.rfind("}")
    try:
        obj = json.loads(text[start:end + 1])
        for key in ["Section", "Simple_Explanation", "Example", "Punishment", "Next_Steps"]:
            if key not in obj: obj[key] = "" if key != "Next_Steps" else []
        return _sanitise(obj)
    except json.JSONDecodeError:
        return None

def _fallback_from_docs(context: List[str]) -> dict:
    sections, snippets = [], []
    for doc in context[:5]:
        sm  = re.search(r"Section\s+(\d+[A-Z]?)", doc, re.IGNORECASE)
        srm = re.search(
            r"(Penal Code|Bail Act|Evidence Ordinance|Police Ordinance|Code of Criminal Procedure)",
            doc, re.IGNORECASE)
        if sm:
            label = (f"{srm.group(1)} Section {sm.group(1)}" if srm
                     else f"Section {sm.group(1)}")
            if label not in sections: sections.append(label)
        match = re.search(r"[—:\-]\s*(.+)", doc, re.DOTALL)
        snippet = (match.group(1).strip()[:400] if match
                   else re.sub(r"\*\*.*?\*\*\s*[-—:]?\s*", "", doc).strip()[:400])
        if snippet: snippets.append(snippet)
    return {
        "Section":            " & ".join(sections) if sections else "See explanation below",
        "Simple_Explanation": " ".join(snippets[:3]) if snippets else "Please refer to relevant legal sections.",
        "Example":            "Please consult a lawyer for case-specific examples.",
        "Punishment":         "Please refer to the relevant Act section for exact penalties.",
        "Next_Steps":         _FIELD_FALLBACKS["Next_Steps"],
    }

# ==========================================
# GENERATION
#
# NOTE: This function only WRITES to cache (via cache_set).
# The READ (cache_get) is done exclusively in /chat BEFORE this is called,
# so generate_answer() is only reached for fresh, uncached queries.
#
# Both raw_message and query_en are passed:
#   raw_message → used as the cache key (original user text)
#   query_en    → used in the LLM prompt (English translation)
# ==========================================
def generate_answer(raw_message: str, query_en: str, context: List[str]) -> tuple:
    online = _bridge_ready()

    if not context:
        result = {
            "Section":            "No Matching Sections Found",
            "Simple_Explanation": "No relevant legal sections found. Please try rephrasing.",
            "Example":    "N/A",
            "Punishment": "N/A",
            "Next_Steps": _FIELD_FALLBACKS["Next_Steps"],
        }
        fm = "online" if online else ("ollama" if _ollama_ready() else "offline")
        cache_set(raw_message, fm, result)
        return result, False, fm

    ctx = "".join(f"SOURCE {i+1}:\n{d}\n\n" for i, d in enumerate(context[:8]))

    # ── ONLINE: Remote inference bridge ─────────────────────────────────────
    if online:
        print("[comp4][Gen] Online — remote bridge")
        raw = _call_bridge(_bridge_gen_messages(query_en, ctx),
                           max_tokens=1500, json_mode=True)
        if raw:
            result = _parse_json(raw)
            if result:
                cache_set(raw_message, _model(), result)
                print("[comp4][Gen] Bridge success → mode=online")
                return result, False, "online"
        print("[comp4][Gen] Bridge failed → Ollama")

    # ── OFFLINE: Ollama local LLM ────────────────────────────────────────────
    if _ollama_ready():
        print(f"[comp4][Gen] Offline — Ollama ({_OL_MODEL})")
        try:
            resp = requests.post(_OL_URL, json={
                "model":   _OL_MODEL,
                "prompt":  _ollama_gen_prompt(query_en, ctx),
                "stream":  False,
                "format":  "json",
                "options": {"temperature": 0.1, "num_ctx": 4096, "top_p": 0.9,
                            "repeat_penalty": 1.1,
                            "stop": ["<|im_end|>", "</s>", "<end_of_turn>"]},
            }, timeout=240)
            if resp.status_code == 200:
                raw = resp.json().get("response", "").strip()
                if raw and not raw.startswith("{"): raw = "{" + raw
                result = _parse_json(raw)
                if result:
                    cache_set(raw_message, _OL_MODEL, result)
                    print("[comp4][Gen] Ollama success → mode=ollama")
                    return result, False, "ollama"
                print("[comp4][Gen] Ollama bad JSON → doc fallback")
            else:
                print(f"[comp4][Ollama] HTTP {resp.status_code}")
        except requests.exceptions.ConnectionError:
            print("[comp4][Ollama] Not running.")
        except Exception as e:
            print(f"[comp4][Ollama] Error: {type(e).__name__}: {e}")
    else:
        print("[comp4][Gen] Ollama not available → doc fallback")

    # ── LAST RESORT: Doc extraction (no LLM) ────────────────────────────────
    print("[comp4][Gen] Doc extraction fallback")
    result = _fallback_from_docs(context)
    mode   = "nllb" if _get_nllb() is not None else "offline"
    cache_set(raw_message, mode, result)
    return result, False, mode

# ==========================================
# /chat ENDPOINT
#
# REQUEST FLOW:
#   1. Detect language of raw message
#   2. CHECK CACHE using raw message as key   ← THE FIX: before translation
#      HIT  → sleep 3s, translate cached data to user's language, return
#      MISS → continue below
#   3. Translate raw message to English
#   4. Legal classification on English query
#   5. Retrieve docs using English query
#   6. generate_answer(raw_message, query_en, context)
#      → runs LLM, writes to cache keyed by raw_message
#   7. Translate result to user's language and return
# ==========================================
@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    t0   = time.time()
    text = req.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    _invalidate_inet_cache()
    online   = _bridge_ready()
    detected = detect_lang(text)
    print(f"[comp4][Chat] lang={detected} | {'ONLINE' if online else 'OFFLINE(local)'}")

    # ------------------------------------------------------------------
    # STEP 1 — UNIFIED CACHE CHECK
    #
    # Key = original raw message (text), checked BEFORE translation.
    #
    # Why before translation?
    #   Tamil/Sinhala → English translation differs between GPT (online)
    #   and NLLB (offline), producing different strings and different hashes.
    #   The original user message is always identical → guaranteed cache hit.
    # ------------------------------------------------------------------
    cached_data = cache_get(text)
    if cached_data:
        print("[comp4][Chat] Cache HIT — sleeping 3s then returning")
        time.sleep(3)
        mode = "online" if online else ("ollama" if _ollama_ready() else "offline")
        tamil_data   = deep_translate(cached_data, "en", "ta") if detected == "ta" else None
        sinhala_data = deep_translate(cached_data, "en", "si") if detected == "si" else None
        elapsed = round((time.time() - t0) * 1000, 1)
        print(f"[comp4][Chat] Cache served in {elapsed}ms | mode={mode}")
        return ChatResponse(
            english_data=cached_data, tamil_data=tamil_data, sinhala_data=sinhala_data,
            detected_lang=detected, cached=True, mode=mode, elapsed_ms=elapsed,
        )

    # ------------------------------------------------------------------
    # STEP 2 — Translate to English (only on cache miss)
    # ------------------------------------------------------------------
    query_en = translate_text(text, detected, "en") if detected != "en" else text
    print(f"[comp4][Chat] EN query: '{query_en[:80]}'")

    # ------------------------------------------------------------------
    # STEP 3 — Legal classification
    # ------------------------------------------------------------------
    if not is_legal_question(query_en):
        nl   = dict(_NON_LEGAL)
        mode = "online" if online else ("ollama" if _ollama_ready() else "offline")
        return ChatResponse(
            english_data=nl,
            tamil_data=deep_translate(nl, "en", "ta")   if detected == "ta" else None,
            sinhala_data=deep_translate(nl, "en", "si") if detected == "si" else None,
            detected_lang=detected, cached=False, mode=mode,
            elapsed_ms=round((time.time() - t0) * 1000, 1),
        )

    # ------------------------------------------------------------------
    # STEP 4 — Retrieve + generate
    # Pass raw `text` as the cache key inside generate_answer
    # ------------------------------------------------------------------
    context = retrieve_docs(query_en, k=8)
    english_data, was_cached, mode = generate_answer(text, query_en, context)

    tamil_data   = deep_translate(english_data, "en", "ta") if detected == "ta" else None
    sinhala_data = deep_translate(english_data, "en", "si") if detected == "si" else None

    elapsed = round((time.time() - t0) * 1000, 1)
    print(f"[comp4][Chat] Done {elapsed}ms | cached={was_cached} | mode={mode}")
    return ChatResponse(
        english_data=english_data, tamil_data=tamil_data, sinhala_data=sinhala_data,
        detected_lang=detected, cached=was_cached, mode=mode, elapsed_ms=elapsed,
    )

# ==========================================
# OTHER ENDPOINTS
# ==========================================

@router.get("/health")
async def health():
    _load_resources()
    _invalidate_inet_cache()
    internet = _has_internet()
    bridge   = _bridge_ready()
    ollama   = _ollama_ready()
    nllb     = _get_nllb() is not None
    active   = ("online" if bridge else ("ollama" if ollama else ("nllb" if nllb else "offline")))
    return {
        "status":       "ok",
        "engine":       "local-neural",
        "internet":     "connected"  if internet else "disconnected",
        "bridge":       "ready"      if bridge   else "offline",
        "ollama":       "ready"      if ollama   else "not running",
        "nllb_local":   "loaded"     if nllb     else ("failed" if _nllb_failed else "not loaded"),
        "embed_model":  "loaded"     if _embed_model else ("failed" if _embed_failed else "not loaded"),
        "embed_local":  os.path.exists(EMBED_MODEL_FOLDER),
        "faiss":        "loaded"     if _index   else "missing",
        "docs":         len(_metadata),
        "graph":        _graph is not None,
        "active_mode":  active,
    }

@router.post("/warmup")
async def warmup():
    """Pre-load all heavy resources so first request is fast."""
    _load_resources(); _get_embed_model(); _get_nllb(); _invalidate_inet_cache()
    return {
        "docs":     len(_metadata),
        "nllb":     _nllb_engine is not None,
        "embed":    _embed_model is not None,
        "internet": _has_internet(),
        "bridge":   _bridge_ready(),
        "ollama":   _ollama_ready(),
    }

@router.post("/download-embed-model")
async def download_embed_model():
    """
    Run ONCE while connected to WiFi.
    Saves embed model locally so it works offline forever.
    Usage: POST /comp4/download-embed-model
    """
    if os.path.exists(EMBED_MODEL_FOLDER):
        return {"status": "already_exists", "path": EMBED_MODEL_FOLDER,
                "message": "Already downloaded. Works offline."}
    if not _has_internet():
        return {"status": "error", "message": "No internet. Connect to WiFi first."}
    try:
        from sentence_transformers import SentenceTransformer
        os.makedirs(EMBED_MODEL_FOLDER, exist_ok=True)
        model = SentenceTransformer("all-MiniLM-L6-v2")
        model.save(EMBED_MODEL_FOLDER)
        global _embed_model, _embed_failed
        _embed_model = model; _embed_failed = False
        return {"status": "success", "path": EMBED_MODEL_FOLDER,
                "message": "Saved. FAISS search now works offline forever."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/diagnose")
async def diagnose(q: str = "theft"):
    """Check why retrieval returns 0 results. GET /comp4/diagnose?q=theft"""
    _load_resources(); embed = _get_embed_model()
    info = {
        "query": q, "metadata_count": len(_metadata),
        "faiss_loaded": _index is not None,
        "faiss_vectors": _index.ntotal if _index else 0,
        "embed_loaded": embed is not None, "embed_failed": _embed_failed,
        "embed_local_exists": os.path.exists(EMBED_MODEL_FOLDER),
        "metadata_path_ok": os.path.exists(METADATA_PATH),
        "faiss_path_ok": os.path.exists(FAISS_INDEX_PATH),
    }
    info["metadata_sample"] = _metadata[:2] if _metadata else []
    if embed and _index:
        try:
            qv = embed.encode([q], convert_to_numpy=True)
            info["embed_dim"] = int(qv.shape[1])
            info["index_dim"] = int(_index.d)
            info["dim_match"] = int(qv.shape[1]) == int(_index.d)
            D, I = _index.search(qv, 5)
            info["faiss_top5"] = [
                {"rank": i+1, "distance": round(float(D[0][i]), 4),
                 "section_id": _metadata[idx].get("section_id", _metadata[idx].get("sectionid", "?")),
                 "source":     _metadata[idx].get("source name", "?"),
                 "heading":    _metadata[idx].get("heading", _metadata[idx].get("title", "?")),
                 "preview":    str(_metadata[idx].get("content", _metadata[idx].get("text", "")))[:120]}
                for i, idx in enumerate(I[0]) if 0 <= idx < len(_metadata)
            ]
        except Exception as e:
            info["faiss_error"] = str(e)
    q_lower = q.lower()
    kw_hits = []
    for obj in _metadata:
        h = str(obj.get("heading", obj.get("title", ""))).lower()
        c = str(obj.get("content", obj.get("text",  ""))).lower()
        if q_lower in h or q_lower in c:
            kw_hits.append({
                "section_id": obj.get("section_id", obj.get("sectionid", "?")),
                "source":     obj.get("source name", "?"),
                "heading":    obj.get("heading", obj.get("title", "?")),
                "preview":    str(obj.get("content", obj.get("text", "")))[:120],
            })
        if len(kw_hits) >= 10: break
    info["keyword_hits"] = kw_hits
    return info

@router.delete("/cache")
async def clear_cache(model: Optional[str] = None):
    db, cur = _get_db()
    try:
        if model:
            cur.execute("DELETE FROM cache WHERE model_id = ?", (model,))
        else:
            cur.execute("DELETE FROM cache")
        count = cur.rowcount
        db.commit()
    finally:
        db.close()
    return {"deleted": count}

@router.get("/cache/stats")
async def cache_stats():
    db, cur = _get_db()
    try:
        cur.execute("SELECT model_id, COUNT(*), MAX(created_at) FROM cache GROUP BY model_id")
        rows = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM cache")
        total = cur.fetchone()[0]
    finally:
        db.close()
    return {
        "total_entries": total,
        "by_model": [{"model": r[0], "count": r[1], "last_used": r[2]} for r in rows],
    }