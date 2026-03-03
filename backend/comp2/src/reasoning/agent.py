import json
import logging

logger = logging.getLogger(__name__)

class LegalAgent:
    def __init__(self, llm_client):
        self.llm = llm_client

    def analyze(self, case_text, similar_cases):
        """Orchestrates the analysis."""
        
        # 1. Format Context (RAG)
        context = ""
        for i, case in enumerate(similar_cases):
            doc = case.get('document', {})
            text = doc.get('full_text', '') if isinstance(doc, dict) else str(doc)
            context += f"\n[PRECEDENT {i+1}]: {text[:1000]}...\n"

        # 2. Define System Persona
        system_prompt = """
        You are a distinguished Senior Counsel in Sri Lanka. 
        Your expertise covers the Penal Code, Evidence Ordinance, and Roman-Dutch Law principles.
        Analyze the provided case facts using the provided precedents.
        Output strictly in JSON format.
        """

        # 3. Define User Task
        user_prompt = f"""
        NEW CASE FACTS:
        {case_text[:2000]}

        RELEVANT PRECEDENTS (Context):
        {context}

        TASK:
        1. Identify the core legal issue.
        2. Formulate a Prosecution Argument citing specific Sri Lankan statutes.
        3. Formulate a Defense Argument focusing on reasonable doubt or procedural errors.
        4. Predict the outcome based on the precedents.

        OUTPUT JSON FORMAT:
        {{
            "legal_issue": "...",
            "prosecution_strategy": "...",
            "defense_strategy": "...",
            "relevant_laws": ["Section X", "Ordinance Y"],
            "predicted_outcome": "..."
        }}
        """

        # 4. Generate
        response = self.llm.generate(system_prompt, user_prompt)
        return self._parse_json(response)

    def _parse_json(self, text):
        try:
            clean = text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
        except:
            return {"raw_text": text, "error": "JSON Parsing Failed"}