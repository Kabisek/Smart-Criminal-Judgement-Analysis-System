# # # # # import whisper
# # # # # from typing import Tuple
# # # # # import os

# # # # # def transcribe_audio(audio_path: str, language: str = "auto") -> Tuple[str, str]:
# # # # #     """
# # # # #     Transcribe audio file with Whisper: Detects si/ta/en, translates to English.
# # # # #     Returns (transcript, detected_lang).
# # # # #     """
# # # # #     if not os.path.exists(audio_path):
# # # # #         raise ValueError("Audio file not found")
    
# # # # #     # Load model once (global for efficiency)
# # # # #     model = whisper.load_model("large-v3")  # Multilingual, high accuracy
    
# # # # #     options = {"language": language} if language != "auto" else {}
# # # # #     result = model.transcribe(audio_path, task="translate", **options)  # Always to English
    
# # # # #     detected = result.get("language", "en")
# # # # #     transcript = result["text"].strip()
    
# # # # #     return transcript, detected

# # # # import whisper
# # # # from typing import Tuple, Dict
# # # # import os

# # # # def transcribe_audio(audio_path: str, language: str = "auto") -> Dict[str, str]:
# # # #     """
# # # #     Transcribe audio file with Whisper: Detects si/ta/en.
# # # #     Returns dict with 'original_transcript' (in detected language), 'english_transcript' (translated to English), and 'detected_lang'.
# # # #     """
# # # #     if not os.path.exists(audio_path):
# # # #         raise ValueError("Audio file not found")
    
# # # #     # Load model once (global for efficiency)
# # # #     model = whisper.load_model("large-v3")  # Multilingual, high accuracy
    
# # # #     options = {"language": language} if language != "auto" else {}
    
# # # #     # First: Transcribe in original language
# # # #     original_result = model.transcribe(audio_path, task="transcribe", **options)
# # # #     detected = original_result.get("language", "en")
# # # #     original_transcript = original_result["text"].strip()
    
# # # #     # Second: Translate to English (if not already English)
# # # #     if detected == "en":
# # # #         english_transcript = original_transcript
# # # #     else:
# # # #         english_result = model.transcribe(audio_path, task="translate", **options)
# # # #         english_transcript = english_result["text"].strip()
    
# # # #     return {
# # # #         "original_transcript": original_transcript,
# # # #         "english_transcript": english_transcript,
# # # #         "detected_lang": detected
# # # #     }
# # # import os
# # # import google.generativeai as genai
# # # from dotenv import load_dotenv
# # # import json
# # # import time

# # # load_dotenv()
# # # genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# # # def transcribe_audio(audio_path: str, language: str = "auto") -> dict:
# # #     if not os.path.exists(audio_path): raise ValueError("Audio file not found")

# # #     max_retries = 3
# # #     audio_file = None
    
# # #     for attempt in range(max_retries):
# # #         try:
# # #             print(f"   [Transcriber] Uploading to Gemini (Attempt {attempt+1})...")
# # #             audio_file = genai.upload_file(path=audio_path)
# # #             break 
# # #         except Exception as e:
# # #             if attempt < max_retries - 1: time.sleep(2)
# # #             else: raise ValueError(f"Failed to upload audio: {e}")

# # #     try:
# # #         while audio_file.state.name == "PROCESSING":
# # #             time.sleep(1)
# # #             audio_file = genai.get_file(audio_file.name)

# # #         if audio_file.state.name == "FAILED": raise ValueError("Audio processing failed.")

# # #         model = genai.GenerativeModel(model_name="gemini-2.5-flash")
# # #         prompt = """
# # #         Listen to this legal audio.
# # #         Tasks: 1. Identify language. 2. Transcribe exactly. 3. Translate to Legal English.
# # #         Return JSON: {"original_transcript": "...", "english_transcript": "...", "detected_lang": "..."}
# # #         """
# # #         response = model.generate_content([prompt, audio_file], generation_config={"response_mime_type": "application/json"})
# # #         result = json.loads(response.text)
# # #         return result
# # #     finally:
# # #         if audio_file: 
# # #             try: genai.delete_file(audio_file.name)
# # #             except: pass

# # import os
# # import json
# # import time
# # import google.generativeai as genai
# # import whisper
# # from dotenv import load_dotenv

# # # --- CONFIGURATION ---
# # load_dotenv()
# # genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# # # Lazy load Whisper to save RAM until needed
# # WHISPER_MODEL = None

# # def get_whisper():
# #     global WHISPER_MODEL
# #     if WHISPER_MODEL is None:
# #         print("   [Transcriber] Loading Whisper (Large-v3)...")
# #         WHISPER_MODEL = whisper.load_model("large-v3")
# #     return WHISPER_MODEL

# # def transcribe_audio(audio_path: str, language: str = "auto") -> dict:
# #     """
# #     Hybrid Pipeline:
# #     1. Whisper (Local) -> Gets phonetic text (Draft).
# #     2. Gemini (Cloud) -> Listens to Audio + Reads Draft -> Perfects it.
# #     """
# #     if not os.path.exists(audio_path):
# #         raise ValueError("Audio file not found")

# #     # --- STEP 1: WHISPER DRAFT ---
# #     draft_text = ""
# #     try:
# #         print("   [1/2] Running Whisper Baseline...")
# #         model = get_whisper()
# #         result = model.transcribe(audio_path)
# #         draft_text = result["text"].strip()
# #         print(f"         -> Draft: {draft_text[:50]}...")
# #     except Exception as e:
# #         print(f"   ⚠️ Whisper Error: {e}. Proceeding with Gemini only.")

# #     # --- STEP 2: GEMINI REFINEMENT ---
# #     max_retries = 3
# #     audio_file = None
    
# #     for attempt in range(max_retries):
# #         try:
# #             print(f"   [2/2] Uploading to Gemini (Attempt {attempt+1})...")
# #             audio_file = genai.upload_file(path=audio_path)
# #             break 
# #         except Exception as e:
# #             if attempt < max_retries - 1: time.sleep(2)
# #             else: raise ValueError(f"Upload failed: {e}")

# #     try:
# #         while audio_file.state.name == "PROCESSING":
# #             time.sleep(1)
# #             audio_file = genai.get_file(audio_file.name)

# #         if audio_file.state.name == "FAILED": raise ValueError("Processing failed.")

# #         model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        
# #         prompt = f"""
# #         I have a legal audio file and a draft transcription (which may have errors).
        
# #         DRAFT: "{draft_text}"

# #         TASK:
# #         1. Listen to the audio.
# #         2. Use the draft to help, but CORRECT any mistakes.
# #         3. Identify the language (Sinhala/Tamil/English).
# #         4. Translate the final text to Professional Legal English.

# #         RETURN JSON ONLY:
# #         {{
# #             "original_transcript": "Corrected text in original language",
# #             "english_transcript": "Legal English translation",
# #             "detected_lang": "si/ta/en"
# #         }}
# #         """
        
# #         response = model.generate_content([prompt, audio_file], generation_config={"response_mime_type": "application/json"})
# #         return json.loads(response.text)

# #     finally:
# #         if audio_file:
# #             try: genai.delete_file(audio_file.name)
# #             except: pass


# import os
# import json
# import time
# import google.generativeai as genai
# import whisper
# import torch
# from dotenv import load_dotenv

# # --- CONFIGURATION ---
# load_dotenv()
# genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# # Global variable for Lazy Loading
# WHISPER_MODEL = None

# def get_whisper():
#     """
#     Loads Whisper only if absolutely necessary.
#     Uses 'turbo' model (Fast) and forces GPU if available.
#     """
#     global WHISPER_MODEL
#     if WHISPER_MODEL is None:
#         device = "cuda" if torch.cuda.is_available() else "cpu"
#         print(f"   [Transcriber] ⚠️ Loading Whisper (Turbo) on {device.upper()}...")
        
#         # 'turbo' is almost as accurate as 'large' but 8x faster
#         WHISPER_MODEL = whisper.load_model("turbo", device=device)
#     return WHISPER_MODEL

# def transcribe_with_gemini(audio_path):
#     """
#     Primary Method: Cloud-based (Fastest & Best for Sinhala/Tamil)
#     """
#     print("   [1/2] Attempting Gemini (Cloud)...")
#     audio_file = None
#     try:
#         audio_file = genai.upload_file(path=audio_path)
        
#         # Wait for processing (usually < 5 seconds)
#         for _ in range(10):
#             if audio_file.state.name == "ACTIVE": break
#             if audio_file.state.name == "FAILED": raise ValueError("Gemini processing failed")
#             time.sleep(1)
#             audio_file = genai.get_file(audio_file.name)

#         model = genai.GenerativeModel(model_name="gemini-2.5-flash")
        
#         prompt = """
#         Listen to this audio.
#         1. Identify language (Sinhala/Tamil/English).
#         2. Transcribe exactly in original language.
#         3. Translate to Professional Legal English.
        
#         Return JSON ONLY:
#         {
#             "original_transcript": "...",
#             "english_transcript": "...",
#             "detected_lang": "..."
#         }
#         """
        
#         response = model.generate_content(
#             [prompt, audio_file], 
#             generation_config={"response_mime_type": "application/json"}
#         )
#         return json.loads(response.text)

#     except Exception as e:
#         print(f"    Gemini Failed: {e}")
#         raise e # Trigger fallback
#     finally:
#         if audio_file:
#             try: genai.delete_file(audio_file.name)
#             except: pass

# def transcribe_with_whisper(audio_path):
#     """
#     Fallback Method: Local (Slower but works offline)
#     """
#     print("   [2/2] Falling back to Whisper (Local)...")
#     try:
#         model = get_whisper()
#         # Translate task forces English output directly
#         result = model.transcribe(audio_path, task="translate")
        
#         return {
#             "original_transcript": "N/A (Whisper Translation Mode)",
#             "english_transcript": result["text"].strip(),
#             "detected_lang": result.get("language", "unknown")
#         }
#     except Exception as e:
#         raise ValueError(f"Whisper Failed: {e}")

# def transcribe_audio(audio_path: str, language: str = "auto") -> dict:
#     if not os.path.exists(audio_path):
#         raise ValueError("Audio file not found")

#     # 1. Try Cloud (Fast)
#     try:
#         return transcribe_with_gemini(audio_path)
#     except:
#         pass # Fail silently and try local

#     # 2. Try Local (Backup)
#     return transcribe_with_whisper(audio_path)

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
print(os.getenv("GOOGLE_API_KEY"))

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
            "detected_lang": "..."
        }
        """
        
        # 4. Generate Content with Retry Logic
        max_retries = 3
        base_delay = 4
        
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