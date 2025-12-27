# # import whisper
# # from typing import Tuple
# # import os

# # def transcribe_audio(audio_path: str, language: str = "auto") -> Tuple[str, str]:
# #     """
# #     Transcribe audio file with Whisper: Detects si/ta/en, translates to English.
# #     Returns (transcript, detected_lang).
# #     """
# #     if not os.path.exists(audio_path):
# #         raise ValueError("Audio file not found")
    
# #     # Load model once (global for efficiency)
# #     model = whisper.load_model("large-v3")  # Multilingual, high accuracy
    
# #     options = {"language": language} if language != "auto" else {}
# #     result = model.transcribe(audio_path, task="translate", **options)  # Always to English
    
# #     detected = result.get("language", "en")
# #     transcript = result["text"].strip()
    
# #     return transcript, detected

# import whisper
# from typing import Tuple, Dict
# import os

# def transcribe_audio(audio_path: str, language: str = "auto") -> Dict[str, str]:
#     """
#     Transcribe audio file with Whisper: Detects si/ta/en.
#     Returns dict with 'original_transcript' (in detected language), 'english_transcript' (translated to English), and 'detected_lang'.
#     """
#     if not os.path.exists(audio_path):
#         raise ValueError("Audio file not found")
    
#     # Load model once (global for efficiency)
#     model = whisper.load_model("large-v3")  # Multilingual, high accuracy
    
#     options = {"language": language} if language != "auto" else {}
    
#     # First: Transcribe in original language
#     original_result = model.transcribe(audio_path, task="transcribe", **options)
#     detected = original_result.get("language", "en")
#     original_transcript = original_result["text"].strip()
    
#     # Second: Translate to English (if not already English)
#     if detected == "en":
#         english_transcript = original_transcript
#     else:
#         english_result = model.transcribe(audio_path, task="translate", **options)
#         english_transcript = english_result["text"].strip()
    
#     return {
#         "original_transcript": original_transcript,
#         "english_transcript": english_transcript,
#         "detected_lang": detected
#     }
import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
import time

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def transcribe_audio(audio_path: str, language: str = "auto") -> dict:
    if not os.path.exists(audio_path): raise ValueError("Audio file not found")

    max_retries = 3
    audio_file = None
    
    for attempt in range(max_retries):
        try:
            print(f"   [Transcriber] Uploading to Gemini (Attempt {attempt+1})...")
            audio_file = genai.upload_file(path=audio_path)
            break 
        except Exception as e:
            if attempt < max_retries - 1: time.sleep(2)
            else: raise ValueError(f"Failed to upload audio: {e}")

    try:
        while audio_file.state.name == "PROCESSING":
            time.sleep(1)
            audio_file = genai.get_file(audio_file.name)

        if audio_file.state.name == "FAILED": raise ValueError("Audio processing failed.")

        model = genai.GenerativeModel(model_name="gemini-2.5-flash")
        prompt = """
        Listen to this legal audio.
        Tasks: 1. Identify language. 2. Transcribe exactly. 3. Translate to Legal English.
        Return JSON: {"original_transcript": "...", "english_transcript": "...", "detected_lang": "..."}
        """
        response = model.generate_content([prompt, audio_file], generation_config={"response_mime_type": "application/json"})
        result = json.loads(response.text)
        return result
    finally:
        if audio_file: 
            try: genai.delete_file(audio_file.name)
            except: pass