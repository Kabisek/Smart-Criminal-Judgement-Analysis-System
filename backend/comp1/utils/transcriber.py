import os
import json
import time
import random
import google.generativeai as genai
import whisper
import torch
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Global variable for Lazy Loading
WHISPER_MODEL = None

def get_whisper():
    """
    Loads Whisper only if absolutely necessary.
    Uses 'turbo' model (Fast) and forces GPU if available.
    """
    global WHISPER_MODEL
    if WHISPER_MODEL is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"   [Transcriber] ⚠️ Loading Whisper (Turbo) on {device.upper()}...")
        
        try:
            # 'turbo' is optimized for speed
            WHISPER_MODEL = whisper.load_model("turbo", device=device)
        except:
            print("   [Transcriber] Turbo not found, using 'medium'...")
            WHISPER_MODEL = whisper.load_model("medium", device=device)
            
    return WHISPER_MODEL

def transcribe_with_gemini(audio_path):
    """
    Primary Method: Cloud-based.
    Includes Retry Logic. Raises Error if all retries fail.
    """
    print("   [1/2] Attempting Gemini (Cloud)...")
    audio_file = None
    
    try:
        # 1. Upload File
        audio_file = genai.upload_file(path=audio_path)
        
        # 2. Wait for processing
        for _ in range(20):
            if audio_file.state.name == "ACTIVE": break
            if audio_file.state.name == "FAILED": raise ValueError("Gemini processing failed")
            time.sleep(1)
            audio_file = genai.get_file(audio_file.name)

        # 3. Initialize Model (Use 1.5-flash for better stability)
        model = genai.GenerativeModel(model_name="gemini-2.5-flash")
        
        prompt = """
        Listen to this audio.
        1. Identify language (Sinhala/Tamil/English).
        2. Transcribe exactly in original language.
        3. Translate to Professional Legal English.
        
        Return JSON ONLY:
        {
            "original_transcript": "...",
            "english_transcript": "...",
            "detected_lang": "...(SINHALA/TAMIL/ENGLISH)"
        }
        """
        
        # 4. Generate Content with Retry Logic
        max_retries = 5
        base_delay = 5
        
        for attempt in range(max_retries):
            try:
                response = model.generate_content(
                    [prompt, audio_file], 
                    generation_config={"response_mime_type": "application/json"}
                )
                return json.loads(response.text)
            
            except Exception as e:
                if "429" in str(e): # Quota Exceeded
                    wait_time = (base_delay * (attempt + 1)) + random.uniform(1, 3)
                    print(f"   ⚠️ Gemini Quota hit. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    raise e # Real error, trigger fallback immediately

        # --- CRITICAL FIX: Raise error if loop finishes without return ---
        raise ValueError("Gemini failed after max retries (Quota Exceeded)")

    except Exception as e:
        print(f"   ❌ Gemini Failed: {e}")
        raise e # Trigger fallback to Whisper
    finally:
        if audio_file:
            try: genai.delete_file(audio_file.name)
            except: pass

def transcribe_with_whisper(audio_path):
    """
    Fallback Method: Local (Slower but works offline).
    """
    print("   [2/2] Falling back to Whisper (Local)...")
    try:
        model = get_whisper()
        # Translate task forces English output directly
        result = model.transcribe(audio_path, task="translate")
        
        return {
            "original_transcript": "N/A (Whisper Translation Mode)",
            "english_transcript": result["text"].strip(),
            "detected_lang": result.get("language", "unknown")
        }
    except Exception as e:
        raise ValueError(f"Whisper Failed: {e}")

def transcribe_audio(audio_path: str, language: str = "auto") -> dict:
    if not os.path.exists(audio_path):
        raise ValueError("Audio file not found")

    # 1. Try Cloud (Fast & Accurate) - Primary Research Method
    try:
        return transcribe_with_gemini(audio_path)
    except Exception as e:
        # This block now correctly catches the error raised by transcribe_with_gemini
        print(f"   🔄 Switching to Local Whisper Model due to: {e}")

    # 2. Try Local (Backup) - Resilience Mechanism
    return transcribe_with_whisper(audio_path)