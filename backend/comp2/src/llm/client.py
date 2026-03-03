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
            # Updated to current Groq model (llama-3.3-70b-versatile or llama-3.1-8b-instant)
            self.model = "llama-3.3-70b-versatile"  # Current powerful model
            # Alternative: "llama-3.1-8b-instant" for faster responses
            
        elif provider == "openrouter":
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY")
            )
            # Use a popular model on OpenRouter
            self.model = "google/gemini-pro-1.5"

        elif provider == "ollama":
            self.client = OpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama"
            )
            self.model = "llama3" # Requires 'ollama pull llama3' locally

        else:
            raise ValueError("Invalid provider. Use 'groq', 'openrouter' or 'ollama'")

    def generate(self, system_prompt, user_prompt):
        try:
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
            # Return a JSON-formatted error that can be detected
            return f'{{"error": "LLM_API_ERROR", "message": "{error_msg.replace(chr(34), chr(39))}"}}'