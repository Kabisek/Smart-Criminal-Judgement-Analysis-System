import os
from openai import OpenAI
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, provider="groq"):
        self.provider = provider
        
        if provider == "groq":
            self.client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=os.getenv("GROQ_API_KEY")
            )
            self.model = "llama-3.3-70b-versatile"
            self._use_openai_interface = True
            
        elif provider == "google":
            # Direct Google Gemini API (Component 2 - separate key to avoid conflicts)
            import google.generativeai as genai
            api_key = os.getenv("GOOGLE_API_KEY_COMP2") or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY_COMP2 or GOOGLE_API_KEY must be set for provider 'google'")
            genai.configure(api_key=api_key)
            self._genai = genai
            self._model = genai.GenerativeModel(
                "gemini-2.5-flash-lite",
                system_instruction="You are a legal analysis assistant. Always respond with valid JSON when asked for structured output."
            )
            self._use_openai_interface = False
            
        elif provider == "openrouter":
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY")
            )
            self.model = "google/gemini-pro-1.5"
            self._use_openai_interface = True

        elif provider == "ollama":
            self.client = OpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama"
            )
            self.model = "llama3"
            self._use_openai_interface = True

        else:
            raise ValueError("Invalid provider. Use 'groq', 'google', 'openrouter' or 'ollama'")

    def generate(self, system_prompt, user_prompt):
        try:
            if self.provider == "google":
                full_prompt = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
                response = self._model.generate_content(
                    full_prompt,
                    generation_config={"temperature": 0.3, "max_output_tokens": 8192}
                )
                if not response.text:
                    raise RuntimeError("Empty response from Gemini")
                return response.text
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3
                )
                return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            logger.error(f"LLM Error: {error_msg}")
            return f'{{"error": "LLM_API_ERROR", "message": "{error_msg.replace(chr(34), chr(39))}"}}'