# # # # import chromadb
# # # # from chromadb.utils import embedding_functions
# # # # import networkx as nx
# # # # import google.generativeai as genai
# # # # import os
# # # # import json
# # # # from dotenv import load_dotenv

# # # # load_dotenv()
# # # # genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# # # # class LegalReasoningEngine:
# # # #     def __init__(self, db_path="data/chroma_db"):
# # # #         # Load Fine-Tuned Model
# # # #         BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# # # #         model_path = os.path.join(BASE_DIR, "models", "sri_lanka_legal_bert")
        
# # # #         print(f"   [Core] Loading Fine-Tuned Model from: {model_path}")
# # # #         try:
# # # #             self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_path)
# # # #         except:
# # # #             print("   ⚠️ Fine-tuned model not found. Using Base.")
# # # #             self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="nlpaueb/legal-bert-base-uncased")

# # # #         self.client = chromadb.PersistentClient(path=db_path)
# # # #         self.collection = self.client.get_collection(name="legal_knowledge_base", embedding_function=self.emb_fn)
# # # #         self.llm = genai.GenerativeModel(model_name="gemini-2.5-flash")
# # # #         print("   [Core] System Online.")

# # # #     def generate_adversarial_analysis(self, case_facts, retrieved_docs):
# # # #         """
# # # #         Forces Gemini to classify laws into Prosecution vs Defense.
# # # #         """
# # # #         context_text = ""
# # # #         doc_map = {}
# # # #         for i, doc in enumerate(retrieved_docs):
# # # #             doc_id = f"DOC_{i}"
# # # #             doc_map[doc_id] = doc
# # # #             # Send full text to LLM for accurate reasoning
# # # #             context_text += f"ID: {doc_id} | TYPE: {doc['type']} | TITLE: {doc['title']} | TEXT: {doc['excerpt'][:1000]}...\n\n"

# # # #         prompt = f"""
# # # #         You are a Senior Legal Strategist in Sri Lanka.
        
# # # #         CASE FACTS: "{case_facts}"
        
# # # #         LEGAL DATABASE RESULTS:
# # # #         {context_text}

# # # #         TASK:
# # # #         Perform an Adversarial Analysis.
# # # #         1. **Prosecution Argument**: How to prove guilt using these laws?
# # # #         2. **Defense Argument**: How to argue for acquittal/mitigation using these laws?
# # # #         3. **Classification**: For EACH document ID, assign it to "Prosecution", "Defense", or "Both".

# # # #         RETURN JSON ONLY:
# # # #         {{
# # # #             "prosecution_argument": "...",
# # # #             "defense_argument": "...",
# # # #             "classifications": {{ "DOC_0": "Prosecution", "DOC_1": "Defense" }}
# # # #         }}
# # # #         """
        
# # # #         try:
# # # #             response = self.llm.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
# # # #             return json.loads(response.text)
# # # #         except Exception as e:
# # # #             print(f"LLM Error: {e}")
# # # #             return {"prosecution_argument": "Error", "defense_argument": "Error", "classifications": {}}

# # # #     def analyze_case(self, case_facts: str):
# # # #         print(f"   [Core] Analyzing: {case_facts[:50]}...")
        
# # # #         # 1. Retrieval (Balanced)
# # # #         categories = [{"type": "penal_code", "count": 5}, {"type": "criminal_procedure", "count": 4}, {"type": "landmark_case", "count": 3}]
# # # #         all_metas, all_docs, all_ids, all_dists = [], [], [], []

# # # #         for cat in categories:
# # # #             res = self.collection.query(query_texts=[case_facts], n_results=cat['count'], where={"type": cat['type']}, include=["metadatas", "documents", "distances"])
# # # #             if res['metadatas'][0]:
# # # #                 all_metas.extend(res['metadatas'][0])
# # # #                 # Retrieve the full text stored in metadata if available, else use document
# # # #                 # In build_db.py we stored 'full_text' in metadata.
# # # #                 full_texts = [m.get('full_text', d) for m, d in zip(res['metadatas'][0], res['documents'][0])]
# # # #                 all_docs.extend(full_texts)
# # # #                 all_ids.extend(res['ids'][0])
# # # #                 all_dists.extend(res['distances'][0])

# # # #         if not all_metas: return {"error": "No matches found."}

# # # #         # Prepare for LLM
# # # #         matches_for_llm = []
# # # #         for i, meta in enumerate(all_metas):
# # # #             matches_for_llm.append({
# # # #                 "id": all_ids[i],
# # # #                 "title": meta.get('title', 'Unknown'),
# # # #                 "section": meta.get('section', 'N/A'),
# # # #                 "type": meta.get('type', 'Unknown'),
# # # #                 "excerpt": all_docs[i], # Full Text
# # # #                 "similarity": 1 - all_dists[i]
# # # #             })

# # # #         # 2. Adversarial Generation
# # # #         print(f"   [Core] Generating Adversarial Arguments...")
# # # #         analysis = self.generate_adversarial_analysis(case_facts, matches_for_llm)

# # # #         # 3. Graph Construction (2 Branches)
# # # #         G = nx.DiGraph()
# # # #         G.add_node("Case", label="Case Facts", type="root", cluster="root")
# # # #         G.add_node("Prosecution", label="Prosecution", type="party", cluster="prosecution")
# # # #         G.add_node("Defense", label="Defense", type="party", cluster="defense")
        
# # # #         G.add_edge("Case", "Prosecution", relation="alleges")
# # # #         G.add_edge("Case", "Defense", relation="defends")

# # # #         final_matches = []
# # # #         classifications = analysis.get("classifications", {})
        
# # # #         for i, match in enumerate(matches_for_llm):
# # # #             doc_key = f"DOC_{i}"
# # # #             side = classifications.get(doc_key, "Both")
            
# # # #             # Add Node with FULL Excerpt
# # # #             G.add_node(match['id'], 
# # # #                        label=match['title'], 
# # # #                        section=match['section'], 
# # # #                        type=match['type'], 
# # # #                        excerpt=match['excerpt']) # Sending full text to frontend

# # # #             if side == "Prosecution":
# # # #                 G.add_edge("Prosecution", match['id'], relation="relies_on")
# # # #             elif side == "Defense":
# # # #                 G.add_edge("Defense", match['id'], relation="relies_on")
# # # #             else:
# # # #                 G.add_edge("Prosecution", match['id'], relation="references")
# # # #                 G.add_edge("Defense", match['id'], relation="references")

# # # #             match['side'] = side
# # # #             final_matches.append(match)

# # # #         return {
# # # #             "legal_analysis": {
# # # #                 "prosecution_argument": analysis.get("prosecution_argument"),
# # # #                 "defense_argument": analysis.get("defense_argument")
# # # #             },
# # # #             "matches": final_matches,
# # # #             "graph_data": nx.cytoscape_data(G)
# # # #         }

# # # import chromadb
# # # from chromadb.utils import embedding_functions
# # # import networkx as nx
# # # import google.generativeai as genai
# # # import os
# # # import json
# # # from dotenv import load_dotenv

# # # load_dotenv()
# # # genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# # # class LegalResourceExtractor:
# # #     def __init__(self, db_path="data/chroma_db"):
# # #         # Load Fine-Tuned Model
# # #         BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# # #         model_path = os.path.join(BASE_DIR, "models", "sri_lanka_legal_bert")
        
# # #         print(f"   [Core] Loading Fine-Tuned Model: {model_path}")
# # #         try:
# # #             self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_path)
# # #         except:
# # #             print("   ⚠️ Fine-tuned model not found. Using Base.")
# # #             self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="nlpaueb/legal-bert-base-uncased")

# # #         self.client = chromadb.PersistentClient(path=db_path)
# # #         self.collection = self.client.get_collection(name="legal_knowledge_base", embedding_function=self.emb_fn)
# # #         self.llm = genai.GenerativeModel(model_name="gemini-1.5-flash")
# # #         print("   [Core] Resource Extraction Engine Online.")

# # #     def generate_defense_query(self, case_facts):
# # #         """
# # #         Generates a search query to find Defense-specific resources.
# # #         """
# # #         prompt = f"""
# # #         CASE FACTS: "{case_facts}"
# # #         TASK: Generate a search query to find legal DEFENSES, EXCEPTIONS, or PROCEDURAL LOOPHOLES for this case in Sri Lankan Law.
# # #         OUTPUT: Just the search query string.
# # #         """
# # #         try:
# # #             response = self.llm.generate_content(prompt)
# # #             return response.text.strip()
# # #         except:
# # #             return f"Legal defenses exceptions mitigation for {case_facts}"

# # #     def classify_resources(self, case_facts, retrieved_docs):
# # #         """
# # #         Tags resources as Prosecution, Defense, or Procedure.
# # #         """
# # #         context_text = ""
# # #         for i, doc in enumerate(retrieved_docs):
# # #             doc_id = f"DOC_{i}"
# # #             context_text += f"ID: {doc_id} | TITLE: {doc['title']} | TEXT: {doc['excerpt'][:300]}...\n"

# # #         prompt = f"""
# # #         Role: Legal Data Classifier.
# # #         CASE FACTS: "{case_facts}"
# # #         LEGAL RESOURCES:
# # #         {context_text}

# # #         TASK: Classify each resource into EXACTLY ONE category:
# # #         1. "Prosecution": Laws defining the crime or proving guilt.
# # #         2. "Defense": Exceptions, defenses, or case law helping the accused.
# # #         3. "Procedure": Neutral procedural steps (Inquest, Arrest, Bail, Investigations).

# # #         RETURN JSON ONLY: {{ "classifications": {{ "DOC_0": "Prosecution", "DOC_1": "Defense" }} }}
# # #         """
# # #         try:
# # #             response = self.llm.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
# # #             return json.loads(response.text).get("classifications", {})
# # #         except Exception as e:
# # #             print(f"   ⚠️ Classification Error: {e}")
# # #             return {}

# # #     def extract_resources(self, case_facts: str):
# # #         print(f"   [Core] Extracting Resources for: {case_facts[:50]}...")
        
# # #         # --- STEP 1: DUAL SEARCH (Facts + Counter-Facts) ---
# # #         prosecution_query = case_facts
# # #         defense_query = self.generate_defense_query(case_facts)
        
# # #         search_queries = [prosecution_query, defense_query]
        
# # #         categories = [
# # #             {"type": "penal_code", "count": 3}, 
# # #             {"type": "criminal_procedure", "count": 3},
# # #             {"type": "landmark_case", "count": 2}
# # #         ]

# # #         unique_results = {} 

# # #         for query_text in search_queries:
# # #             for cat in categories:
# # #                 # --- FIX IS HERE: Removed "ids" from include list ---
# # #                 res = self.collection.query(
# # #                     query_texts=[query_text], 
# # #                     n_results=cat['count'], 
# # #                     where={"type": cat['type']}, 
# # #                     include=["metadatas", "documents", "distances"] 
# # #                 )
                
# # #                 # Chroma returns 'ids' by default, so we can still access them safely
# # #                 if res['ids'] and res['ids'][0]:
# # #                     for i in range(len(res['ids'][0])):
# # #                         uid = res['ids'][0][i]
# # #                         if uid not in unique_results:
# # #                             meta = res['metadatas'][0][i]
# # #                             full_text = meta.get('full_text', res['documents'][0][i])
                            
# # #                             # Clean up headnotes if they are raw JSON strings in the data
# # #                             excerpt = full_text
# # #                             try:
# # #                                 if excerpt.startswith("[{'point_number'"):
# # #                                     # It's an ugly stringified list, let's just use the title or a snippet
# # #                                     excerpt = excerpt.split("}]", 1)[-1].strip()
# # #                             except: pass

# # #                             unique_results[uid] = {
# # #                                 "id": uid,
# # #                                 "title": self.clean_title(meta.get('title', 'Unknown')),
# # #                                 "section": self.clean_title(meta.get('section', 'N/A')),
# # #                                 "type": meta.get('type', 'Unknown'),
# # #                                 "excerpt": excerpt,
# # #                                 "distance": res['distances'][0][i],
# # #                                 # Carry over metadata fields
# # #                                 "judge": meta.get("judges", "Not Documented"),
# # #                                 "place": meta.get("court", "Supreme Court"),
# # #                                 "outcome": meta.get("outcome", "See Ratio"),
# # #                                 "hn_str": meta.get("hn_str", "")
# # #                             }
# # #         all_matches = list(unique_results.values())
        
# # #         if not all_matches: return {"error": "No matches found."}

# # #         # --- STEP 2: CLASSIFICATION ---
# # #         print(f"   [Core] Classifying {len(all_matches)} Resources...")
        
# # #         matches_for_llm = []
# # #         for match in all_matches:
# # #             matches_for_llm.append({
# # #                 "title": match['title'],
# # #                 "type": match['type'],
# # #                 "excerpt": match['excerpt']
# # #             })

# # #         classifications = self.classify_resources(case_facts, matches_for_llm)

# # #         # --- STEP 3: GRAPH & GROUPING ---
# # #         G = nx.DiGraph()
# # #         G.add_node("Case", label="Case Facts", type="root", cluster="root")
        
# # #         G.add_node("Prosecution_Branch", label="Prosecution Resources", type="branch_hub", cluster="prosecution")
# # #         G.add_node("Defense_Branch", label="Defense Resources", type="branch_hub", cluster="defense")
# # #         G.add_node("Procedure_Branch", label="Procedural Steps", type="branch_hub", cluster="procedure")
        
# # #         G.add_edge("Case", "Prosecution_Branch", relation="investigates")
# # #         G.add_edge("Case", "Defense_Branch", relation="investigates")
# # #         G.add_edge("Case", "Procedure_Branch", relation="requires")

# # #         # Buckets for clean JSON output
# # #         grouped_resources = {
# # #             "prosecution_resources": [],
# # #             "defense_resources": [],
# # #             "procedural_resources": []
# # #         }
        
# # #         for i, match in enumerate(all_matches):
# # #             doc_key = f"DOC_{i}"
            
# # #             # Fallback logic
# # #             default_side = "Procedure" if match['type'] == 'criminal_procedure' else "Prosecution"
# # #             side = classifications.get(doc_key, default_side)
            
# # #             # Add Node
# # #             G.add_node(match['id'], 
# # #                        label=match['title'], 
# # #                        section=match['section'], 
# # #                        type=match['type'], 
# # #                        excerpt=match['excerpt'])

# # #             # Link to Branch & Add to Bucket
# # #             if side == "Prosecution":
# # #                 G.add_edge("Prosecution_Branch", match['id'], relation="charges")
# # #                 match['side'] = "Prosecution"
# # #                 grouped_resources["prosecution_resources"].append(match)
# # #             elif side == "Defense":
# # #                 G.add_edge("Defense_Branch", match['id'], relation="defends_with")
# # #                 match['side'] = "Defense"
# # #                 grouped_resources["defense_resources"].append(match)
# # #             else:
# # #                 G.add_edge("Procedure_Branch", match['id'], relation="step")
# # #                 match['side'] = "Procedure"
# # #                 grouped_resources["procedural_resources"].append(match)

# # #             match['similarity'] = round(1 - match['distance'], 4)
# # #             del match['distance'] 

# # #         return {
# # #             "summary": f"Extracted {len(all_matches)} legal resources.",
# # #             "structured_data": grouped_resources,
# # #             "graph_data": nx.cytoscape_data(G)
# # #         }


# # """
# # ===============================================================================
# # INTELLIGENT LEGAL INTELLIGENCE LAYER (Research Component)
# # ===============================================================================

# # SCOPE BOUNDARY: Information Extraction (IE) and Knowledge Representation

# # This module transforms unstructured, multilingual legal content into 
# # mathematically structured knowledge graphs and JSON schemas.

# # WHAT THIS COMPONENT DOES:
# #   ✓ Ingests raw legal text (multilingual audio → transcribed English)
# #   ✓ Performs semantic retrieval using fine-tuned Legal-BERT embeddings
# #   ✓ Decomposes statutes into legal elements (Act + Intent + Knowledge)
# #   ✓ Extracts structured data (Definition, Punishment, Elements, Ratio Decidendi)
# #   ✓ Builds hierarchical knowledge graphs (Landmark > Recent > Statutes)
# #   ✓ Outputs STRUCTURED JSON (not narrative text)

# # WHAT THIS COMPONENT DOES NOT DO:
# #   ✗ Does NOT write final legal briefs or arguments (Application Layer)
# #   ✗ Does NOT generate persuasive narrative text (Teammate's component)
# #   ✗ Does NOT chat with users (Interaction Layer)

# # ARCHITECTURE:
# #   - Hybrid Neuro-Symbolic: Combines Neural Networks (Vector Search) with
# #     Symbolic Logic (Statutory Decomposition / Element Mapping)
# #   - Domain-Adapted: Uses Fine-Tuned Sri Lankan Legal-BERT
# #   - Explainable AI (XAI): Breaks laws into verifiable elements
# # ===============================================================================
# # """

# # import chromadb
# # from chromadb.utils import embedding_functions
# # import networkx as nx
# # import google.generativeai as genai
# # import os
# # import json
# # from dotenv import load_dotenv

# # load_dotenv()
# # genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


# # class LegalContentNormalizer:
# #     """
# #     RESEARCH MODULE: Semantic Information Extraction (IE) - Statutory Decomposition
    
# #     Converts unstructured legal text into structured JSON schemas using
# #     Hybrid Neuro-Symbolic architecture.
# #     """
    
# #     def __init__(self, llm):
# #         self.llm = llm

# #     def _clean_text(self, text, max_length=3000):
# #         """Clean and truncate text for LLM processing"""
# #         if not text:
# #             return ""
# #         # Remove excessive whitespace
# #         text = " ".join(text.split())
# #         # Truncate to avoid context window issues
# #         if len(text) > max_length:
# #             text = text[:max_length] + "..."
# #         return text

# #     def normalize_statute(self, title, raw_text):
# #         """
# #         STATUTORY DECOMPOSITION: Extract legal elements from statutes
# #         """
# #         cleaned_text = self._clean_text(raw_text, max_length=3000)
        
# #         prompt = f"""
# #         Analyze this Sri Lankan Statute using Statutory Decomposition:
# #         TITLE: {title}
# #         TEXT: "{cleaned_text}"

# #         TASK: Extract into a structured JSON object:
# #         1. "definition": The core legal definition of the offence (one sentence).
# #         2. "legal_elements": Decompose into required elements:
# #            - "actus_reus": The physical act or conduct required
# #            - "mens_rea": The mental state required (intent, knowledge, recklessness, negligence)
# #            - "knowledge_requirements": Any specific knowledge or awareness requirements
# #            - "circumstances": Any specific circumstances or conditions
# #         3. "punishment": The specific penalty (imprisonment years, fine amount, or both).
# #         4. "exceptions": Any exceptions, provisos, defenses, or exemptions mentioned.

# #         CRITICAL: Return ONLY valid JSON. No narrative text. No markdown formatting.

# #         Example format:
# #         {{
# #             "definition": "Whoever...",
# #             "legal_elements": {{
# #                 "actus_reus": "...",
# #                 "mens_rea": "...",
# #                 "knowledge_requirements": "...",
# #                 "circumstances": "..."
# #             }},
# #             "punishment": "...",
# #             "exceptions": "..."
# #         }}
# #         """
# #         try:
# #             response = self.llm.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
# #             result_text = response.text.strip()
            
# #             # Remove markdown code blocks if present
# #             if result_text.startswith("```json"):
# #                 result_text = result_text[7:]
# #             if result_text.startswith("```"):
# #                 result_text = result_text[3:]
# #             if result_text.endswith("```"):
# #                 result_text = result_text[:-3]
# #             result_text = result_text.strip()
            
# #             result = json.loads(result_text)
            
# #             # Ensure legal_elements structure exists
# #             if "legal_elements" not in result or not isinstance(result["legal_elements"], dict):
# #                 result["legal_elements"] = {
# #                     "actus_reus": result.get("definition", "See definition"),
# #                     "mens_rea": "See definition",
# #                     "knowledge_requirements": "N/A",
# #                     "circumstances": "N/A"
# #                 }
            
# #             return result
# #         except json.JSONDecodeError as e:
# #             print(f"   [Normalizer] JSON Parse Error for {title}: {e}")
# #             # Return minimal structure
# #             return {
# #                 "definition": cleaned_text[:500] if cleaned_text else "Extraction failed",
# #                 "legal_elements": {
# #                     "actus_reus": "See definition",
# #                     "mens_rea": "See definition",
# #                     "knowledge_requirements": "N/A",
# #                     "circumstances": "N/A"
# #                 },
# #                 "punishment": "See full text",
# #                 "exceptions": "N/A"
# #             }
# #         except Exception as e:
# #             print(f"   [Normalizer] Error extracting {title}: {e}")
# #             return {
# #                 "definition": cleaned_text[:500] if cleaned_text else "Extraction failed",
# #                 "legal_elements": {
# #                     "actus_reus": "Extraction failed - see full text",
# #                     "mens_rea": "Extraction failed - see full text",
# #                     "knowledge_requirements": "N/A",
# #                     "circumstances": "N/A"
# #                 },
# #                 "punishment": "See full text",
# #                 "exceptions": "N/A"
# #             }

# #     def normalize_case(self, title, raw_text):
# #         """
# #         JUDGMENT EXTRACTION: Extract structured information from case law
# #         """
# #         cleaned_text = self._clean_text(raw_text, max_length=4000)
        
# #         prompt = f"""
# #         Analyze this Sri Lankan Judgment:
# #         CASE: {title}
# #         TEXT: "{cleaned_text}"

# #         TASK: Extract into a JSON object:
# #         1. "legal_issue": What was the main question of law? (One sentence)
# #         2. "held": The final decision (Allowed/Dismissed/Convicted/Acquitted).
# #         3. "ratio_decidendi": The core legal reasoning or principle established (binding precedent).

# #         CRITICAL: Return ONLY valid JSON. No narrative text. No markdown formatting.

# #         Example format:
# #         {{
# #             "legal_issue": "...",
# #             "held": "...",
# #             "ratio_decidendi": "..."
# #         }}
# #         """
# #         try:
# #             response = self.llm.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
# #             result_text = response.text.strip()
            
# #             # Remove markdown code blocks if present
# #             if result_text.startswith("```json"):
# #                 result_text = result_text[7:]
# #             if result_text.startswith("```"):
# #                 result_text = result_text[3:]
# #             if result_text.endswith("```"):
# #                 result_text = result_text[:-3]
# #             result_text = result_text.strip()
            
# #             result = json.loads(result_text)
# #             return result
# #         except json.JSONDecodeError as e:
# #             print(f"   [Normalizer] JSON Parse Error for case {title}: {e}")
# #             return {
# #                 "legal_issue": "Extraction failed - see full text",
# #                 "held": "N/A",
# #                 "ratio_decidendi": cleaned_text[:500] if cleaned_text else "Extraction failed"
# #             }
# #         except Exception as e:
# #             print(f"   [Normalizer] Error extracting case {title}: {e}")
# #             return {
# #                 "legal_issue": "N/A",
# #                 "held": "N/A",
# #                 "ratio_decidendi": cleaned_text[:500] if cleaned_text else "Extraction failed"
# #             }


# # class LegalResourceExtractor:
# #     def __init__(self, db_path="data/chroma_db"):
# #         BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# #         model_path = os.path.join(BASE_DIR, "models", "sri_lanka_legal_bert")
        
# #         print(f"   [Core] Loading Model: {model_path}")
# #         try:
# #             self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_path)
# #         except:
# #             self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="nlpaueb/legal-bert-base-uncased")

# #         self.client = chromadb.PersistentClient(path=db_path)
# #         self.collection = self.client.get_collection(name="legal_knowledge_base", embedding_function=self.emb_fn)
# #         self.llm = genai.GenerativeModel(model_name="gemini-2.5-flash")
        
# #         # Initialize the Normalizer (Hybrid Neuro-Symbolic Architecture)
# #         self.normalizer = LegalContentNormalizer(self.llm)
# #         print("   [Core] ✓ Extraction Engine Online (Information Extraction Layer)")

# #     def generate_defense_query(self, case_facts):
# #         try:
# #             prompt = f"CASE FACTS: '{case_facts}'\nTASK: Generate search keywords for legal DEFENSES and EXCEPTIONS in Sri Lanka."
# #             return self.llm.generate_content(prompt).text.strip()
# #         except:
# #             return f"Legal defenses exceptions mitigation for {case_facts}"

# #     def classify_resources(self, case_facts, retrieved_docs):
# #         context_text = ""
# #         for i, doc in enumerate(retrieved_docs):
# #             context_text += f"ID: DOC_{i} | TITLE: {doc['title']} | TEXT: {doc['excerpt'][:200]}...\n"

# #         prompt = f"""
# #         Role: Legal Classifier.
# #         CASE: "{case_facts}"
# #         RESOURCES:
# #         {context_text}
# #         TASK: Classify each DOC into: "Prosecution", "Defense", or "Procedure".
# #         RETURN JSON: {{ "classifications": {{ "DOC_0": "Prosecution" }} }}
# #         """
# #         try:
# #             response = self.llm.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
# #             return json.loads(response.text).get("classifications", {})
# #         except: return {}

# #     def extract_resources(self, case_facts: str):
# #         print(f"   [Core] Extracting Resources for: {case_facts[:50]}...")
        
# #         prosecution_query = case_facts
# #         defense_query = self.generate_defense_query(case_facts)
# #         search_queries = [prosecution_query, defense_query]
        
# #         # --- HIERARCHICAL RETRIEVAL CONFIGURATION ---
# #         categories = [
# #             {"type": "penal_code", "count": 3}, 
# #             {"type": "criminal_procedure", "count": 3},
# #             {"type": "landmark_precedent", "count": 2}, # High Priority
# #             {"type": "recent_judgement", "count": 2}    # Supporting
# #         ]

# #         unique_results = {} 

# #         for query_text in search_queries:
# #             for cat in categories:
# #                 res = self.collection.query(
# #                     query_texts=[query_text], 
# #                     n_results=cat['count'], 
# #                     where={"type": cat['type']}, 
# #                     include=["metadatas", "documents", "distances"]
# #                 )
                
# #                 if res['ids'] and res['ids'][0]:
# #                     for i in range(len(res['ids'][0])):
# #                         uid = res['ids'][0][i]
# #                         if uid not in unique_results:
# #                             meta = res['metadatas'][0][i]
# #                             full_text = meta.get('full_text', res['documents'][0][i])
# #                             unique_results[uid] = {
# #                                 "id": uid, "title": meta.get('title', 'Unknown'), "section": meta.get('section', 'N/A'),
# #                                 "type": meta.get('type', 'Unknown'), "excerpt": full_text, "distance": res['distances'][0][i]
# #                             }

# #         all_matches = list(unique_results.values())
# #         if not all_matches: return {"error": "No matches found."}

# #         # --- STEP 2: CLASSIFICATION ---
# #         matches_for_llm = [{"title": m['title'], "type": m['type'], "excerpt": m['excerpt']} for m in all_matches]
# #         classifications = self.classify_resources(case_facts, matches_for_llm)

# #         # --- STEP 3: SEMANTIC NORMALIZATION (Statutory Decomposition) ---
# #         print("   [Core] Performing Statutory Decomposition (IE)...")

# #         # --- GRAPH CONSTRUCTION ---
# #         G = nx.DiGraph()
# #         G.add_node("Case", label="Case Facts", type="root")
        
# #         # Hubs
# #         G.add_node("Prosecution", label="Prosecution", type="branch")
# #         G.add_node("Defense", label="Defense", type="branch")
# #         G.add_node("Procedure", label="Procedure", type="branch")
        
# #         # New Hubs for Case Law Hierarchy
# #         G.add_node("Binding_Precedents", label="Binding Precedents (Landmark)", type="authority_hub")
# #         G.add_node("Persuasive_Authority", label="Recent Judgments", type="authority_hub")

# #         G.add_edge("Case", "Prosecution"); G.add_edge("Case", "Defense"); G.add_edge("Case", "Procedure")
# #         G.add_edge("Case", "Binding_Precedents"); G.add_edge("Case", "Persuasive_Authority")

# #         grouped_resources = {
# #             "prosecution_resources": [],
# #             "defense_resources": [],
# #             "procedural_resources": [],
# #             "binding_precedents": [],   # Landmark
# #             "recent_judgments": []      # OCR
# #         }
        
# #         for i, match in enumerate(all_matches):
# #             doc_key = f"DOC_{i}"
# #             default_side = "Procedure" if match['type'] == 'criminal_procedure' else "Prosecution"
# #             side = classifications.get(doc_key, default_side)
            
# #             # --- STATUTORY DECOMPOSITION: Extract Structured Elements ---
# #             raw_text = match.get('excerpt', '')
# #             structured_content = {}
            
# #             if match['type'] in ['penal_code', 'criminal_procedure']:
# #                 # For statutes: Decompose into Act + Intent + Knowledge elements
# #                 structured_content = self.normalizer.normalize_statute(match['title'], raw_text)
# #             elif match['type'] in ['landmark_precedent', 'recent_judgement']:
# #                 # For cases: Extract Issue + Holding + Ratio Decidendi
# #                 structured_content = self.normalizer.normalize_case(match['title'], raw_text)
            
# #             # Merge structured content into match object
# #             match.update(structured_content)
# #             # Remove raw text to keep JSON clean (optional - you can keep it if needed)
# #             if 'excerpt' in match:
# #                 match['raw_text'] = match['excerpt']  # Keep for reference
# #                 # del match['excerpt']  # Uncomment if you want to remove raw text
            
# #             G.add_node(match['id'], label=match['title'], section=match['section'], type=match['type'])
            
# #             # Logic for Statutes (Penal/Procedure)
# #             if match['type'] in ['penal_code', 'criminal_procedure']:
# #                 if side == "Prosecution":
# #                     G.add_edge("Prosecution", match['id'])
# #                     grouped_resources["prosecution_resources"].append(match)
# #                 elif side == "Defense":
# #                     G.add_edge("Defense", match['id'])
# #                     grouped_resources["defense_resources"].append(match)
# #                 else:
# #                     G.add_edge("Procedure", match['id'])
# #                     grouped_resources["procedural_resources"].append(match)
            
# #             # Logic for Case Law Hierarchy
# #             elif match['type'] == 'landmark_precedent':
# #                 G.add_edge("Binding_Precedents", match['id'])
# #                 grouped_resources["binding_precedents"].append(match)
            
# #             elif match['type'] == 'recent_judgement':
# #                 G.add_edge("Persuasive_Authority", match['id'])
# #                 grouped_resources["recent_judgments"].append(match)

# #             match['side'] = side
# #             match['similarity'] = round(1 - match['distance'], 4)
# #             del match['distance']

# #         return {
# #             "summary": "Semantic Information Extraction Complete. Structured data ready for downstream processing.",
# #             "structured_data": grouped_resources,
# #             "graph_data": nx.cytoscape_data(G),
# #             "scope_note": "This output contains STRUCTURED DATA (JSON). It does NOT contain narrative arguments or persuasive text. Use this data to build legal arguments in the Application Layer."
# #         }

# import chromadb
# from chromadb.utils import embedding_functions
# import networkx as nx
# import google.generativeai as genai
# import os
# import json
# import time
# import random
# from dotenv import load_dotenv

# load_dotenv()
# genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# class LegalContentNormalizer:
#     """
#     RESEARCH MODULE: Semantic Information Extraction (IE).
#     Extracts structured fields, but does NOT replace the full text.
#     """
#     def __init__(self, llm):
#         self.llm = llm

#     def _call_gemini_safe(self, prompt):
#         max_retries = 3
#         base_delay = 2 

#         for attempt in range(max_retries):
#             try:
#                 time.sleep(base_delay) 
#                 response = self.llm.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
#                 return json.loads(response.text)
#             except Exception as e:
#                 if "429" in str(e):
#                     wait_time = (base_delay * (attempt + 1)) + random.uniform(1, 3)
#                     print(f"   ⚠️ Quota hit. Waiting {wait_time:.1f}s...")
#                     time.sleep(wait_time)
#                 else:
#                     print(f"   ❌ Gemini Error: {e}")
#                     return None
#         return None

#     def normalize_statute(self, title, raw_text):
#         # We try to extract specific fields, but we won't rely on this for the full text
#         prompt = f"""
#         Analyze this Sri Lankan Statute:
#         TITLE: {title}
#         TEXT: "{raw_text[:6000]}" 

#         TASK: Extract the following into a JSON object:
#         1. "definition": The core legal definition.
#         2. "punishment": The specific penalty (e.g., "Death", "10 years RI").
#         3. "exceptions": Any exceptions or defenses mentioned.

#         Return JSON ONLY.
#         """
#         result = self._call_gemini_safe(prompt)
#         if result: return result
#         return {"definition": "Available in full text", "punishment": "Available in full text", "exceptions": "N/A"}

#     def normalize_case(self, title, raw_text):
#         prompt = f"""
#         Analyze this Sri Lankan Judgment:
#         CASE: {title}
#         TEXT: "{raw_text[:6000]}"

#         TASK: Extract the following into a JSON object:
#         1. "legal_issue": The main legal question.
#         2. "held": The final decision (e.g., "Appeal Allowed").
#         3. "ratio_decidendi": The core legal principle established.

#         Return JSON ONLY.
#         """
#         result = self._call_gemini_safe(prompt)
#         if result: return result
#         return {"legal_issue": "Available in full text", "held": "Available in full text", "ratio_decidendi": "Available in full text"}

# class LegalResourceExtractor:
#     def __init__(self, db_path="data/chroma_db"):
#         BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#         model_path = os.path.join(BASE_DIR, "models", "sri_lanka_legal_bert")
        
#         print(f"   [Core] Loading Custom Model: {model_path}")
#         try:
#             self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_path)
#         except:
#             self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="nlpaueb/legal-bert-base-uncased")

#         self.client = chromadb.PersistentClient(path=db_path)
#         self.collection = self.client.get_collection(name="legal_knowledge_base", embedding_function=self.emb_fn)
#         self.llm = genai.GenerativeModel(model_name="gemini-2.5-flash")
#         self.normalizer = LegalContentNormalizer(self.llm)
#         print("   [Core] Extraction Engine Online.")

#     def generate_defense_query(self, case_facts):
#         try:
#             prompt = f"CASE FACTS: '{case_facts}'\nTASK: Generate search keywords for legal DEFENSES."
#             return self.llm.generate_content(prompt).text.strip()
#         except:
#             return f"Legal defenses exceptions mitigation for {case_facts}"

#     def classify_resources(self, case_facts, retrieved_docs):
#         context_text = ""
#         for i, doc in enumerate(retrieved_docs):
#             doc_id = f"DOC_{i}"
#             context_text += f"ID: {doc_id} | TITLE: {doc['title']}\n"

#         prompt = f"""
#         Role: Legal Classifier.
#         CASE: "{case_facts}"
#         RESOURCES: {context_text}
#         TASK: Classify each DOC into: "Prosecution", "Defense", or "Procedure".
#         RETURN JSON: {{ "classifications": {{ "DOC_0": "Prosecution" }} }}
#         """
#         try:
#             response = self.llm.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
#             return json.loads(response.text).get("classifications", {})
#         except: return {}

#     def clean_title(self, title):
#         return title.replace(".pdf", "").replace("_", " ").replace(".json", "").title()

#     def extract_resources(self, case_facts: str):
#         print(f"   [Core] Extracting Resources for: {case_facts[:50]}...")
        
#         prosecution_query = case_facts
#         defense_query = self.generate_defense_query(case_facts)
#         search_queries = [prosecution_query, defense_query]
        
#         categories = [
#             {"type": "penal_code", "count": 5}, 
#             {"type": "criminal_procedure", "count": 5},
#             {"type": "landmark_precedent", "count": 3},
#             {"type": "recent_judgement", "count": 3}
#         ]

#         unique_results = {} 

#         for query_text in search_queries:
#             for cat in categories:
#                 res = self.collection.query(
#                     query_texts=[query_text], 
#                     n_results=cat['count'], 
#                     where={"type": cat['type']}, 
#                     include=["metadatas", "documents", "distances"]
#                 )
                
#                 if res['ids'] and res['ids'][0]:
#                     for i in range(len(res['ids'][0])):
#                         # Similarity Threshold
#                         similarity = 1 - res['distances'][0][i]
#                         if similarity < 0.75: continue 

#                         uid = res['ids'][0][i]
#                         if uid not in unique_results:
#                             meta = res['metadatas'][0][i]
#                             # CRITICAL: Get the full text from metadata (preferred) or document
#                             full_text = meta.get('full_text', res['documents'][0][i])
#                             clean_t = self.clean_title(meta.get('title', 'Unknown'))
#                             clean_s = self.clean_title(meta.get('section', 'N/A'))
                            
#                             unique_results[uid] = {
#                                 "id": uid,
#                                 "title": clean_t,
#                                 "section": clean_s,
#                                 "type": meta.get('type', 'Unknown'),
#                                 "full_text": full_text, # <--- STORE FULL TEXT HERE
#                                 "similarity": round(similarity, 4)
#                             }

#         all_matches = list(unique_results.values())
#         all_matches.sort(key=lambda x: x['similarity'], reverse=True)
        
#         if not all_matches: return {"error": "No relevant legal resources found."}

#         # --- CLASSIFICATION ---
#         matches_for_llm = [{"title": m['title']} for m in all_matches]
#         classifications = self.classify_resources(case_facts, matches_for_llm)

#         # --- NORMALIZATION & GRAPH ---
#         print(f"   [Core] Normalizing {len(all_matches)} Resources...")
        
#         grouped_resources = {
#             "prosecution_resources": [],
#             "defense_resources": [],
#             "procedural_resources": [],
#             "binding_precedents": [],
#             "recent_judgments": []
#         }
        
#         G = nx.DiGraph()
#         G.add_node("Case", label="Case Facts", type="root")
#         for hub in ["Prosecution", "Defense", "Procedure", "Binding_Precedents", "Persuasive_Authority"]:
#             G.add_node(hub, label=hub.replace("_", " "), type="hub")
#             G.add_edge("Case", hub)

#         for i, match in enumerate(all_matches):
#             doc_key = f"DOC_{i}"
#             default_side = "Procedure" if match['type'] == 'criminal_procedure' else "Prosecution"
#             side = classifications.get(doc_key, default_side)
            
#             # 1. Normalize Content (Extract fields)
#             structured_content = {}
#             if match['type'] in ['penal_code', 'criminal_procedure']:
#                 structured_content = self.normalizer.normalize_statute(match['title'], match['full_text'])
#             else:
#                 structured_content = self.normalizer.normalize_case(match['title'], match['full_text'])
            
#             match.update(structured_content)
            
#             # 2. Graph Logic
#             G.add_node(match['id'], label=match['title'], type=match['type'])
            
#             if match['type'] == 'landmark_precedent':
#                 G.add_edge("Binding_Precedents", match['id'])
#                 grouped_resources["binding_precedents"].append(match)
#             elif match['type'] == 'recent_judgement':
#                 G.add_edge("Persuasive_Authority", match['id'])
#                 grouped_resources["recent_judgments"].append(match)
#             else:
#                 if side == "Prosecution":
#                     G.add_edge("Prosecution", match['id'])
#                     grouped_resources["prosecution_resources"].append(match)
#                 elif side == "Defense":
#                     G.add_edge("Defense", match['id'])
#                     grouped_resources["defense_resources"].append(match)
#                 else:
#                     G.add_edge("Procedure", match['id'])
#                     grouped_resources["procedural_resources"].append(match)

#         return {
#             "summary": f"Extracted {len(all_matches)} high-relevance legal resources.",
#             "structured_data": grouped_resources,
#             "graph_data": nx.cytoscape_data(G)
#         }
import chromadb
from chromadb.utils import embedding_functions
import networkx as nx
import google.generativeai as genai
import os
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class LegalResourceExtractor:
    def __init__(self, db_path="data/chroma_db"):
        # Load Fine-Tuned Model
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(BASE_DIR, "models", "sri_lanka_legal_bert")
        
        print(f"   [Core] Loading Fine-Tuned Model: {model_path}")
        try:
            self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_path)
        except:
            print("   ⚠️ Fine-tuned model not found. Using Base.")
            self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="nlpaueb/legal-bert-base-uncased")

        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name="legal_knowledge_base", embedding_function=self.emb_fn
        )
        
        # Only use Gemini for the final summary or complex query generation (Minimal usage)
        self.llm = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
        
        # --- PRE-COMPUTE ANCHOR VECTORS (The Research Part) ---
        print("   [Core] Pre-computing Semantic Axes...")
        # --- PRE-COMPUTE ANCHOR VECTORS (Refined for Legal Precision) ---
        print("   [Core] Pre-computing Semantic Axes...")
        self.anchors = {
    # Prosecution: Focused on 'Proving the Ingredients' and 'Liability'
         "Prosecution": self.emb_fn([
        "guilty of the offence of punishable with imprisonment fine "
        "whoever commits shall be punished liability for the act "
        "voluntarily causing hurt intention to cause death knowledge of likelihood "
        "wrongful gain wrongful loss dishonest intention criminal misappropriation "
        "abatement of offence common intention in furtherance of a criminal act"
    ])[0],

    # Defense: Focused on 'Statutory Exceptions' and 'General Defences' 
    "Defense": self.emb_fn([
        "nothing is an offence which general exceptions special exception "
        "right of private defence of the body and property justified by law "
        "act of a person of unsound mind intoxication against his will "
        "good faith without any criminal intention mistake of fact "
        "grave and sudden provocation sudden fight without premeditation "
        "benefit of the doubt acquittal mitigation of sentence"
    ])[0],
            # Procedure: Focus on the PROCESS (Investigation -> Trial)
            "Procedure": self.emb_fn([
                "investigation inquiry arrest bail medical examination report magistrate police warrant "
                "summons jurisdiction evidence witness statement complaint first information report "
                "charge sheet indictment trial procedure judgment appeal revision"
            ])[0]
        }
        print("   [Core] Engine Online.")

    def generate_defense_query(self, case_facts):
        """
        Uses LLM only for query expansion (Low cost, high value).
        """
        try:
            prompt = f"CASE FACTS: '{case_facts}'\nTASK: Generate search keywords for legal DEFENSES."
            return self.llm.generate_content(prompt).text.strip()
        except:
            return f"Legal defenses exceptions mitigation for {case_facts}"

    def classify_local(self, text, doc_type, section="N/A"):
        """
        Classifies resources using Vector Cosine Similarity (No Gemini).
        """
        # 1. Hard Rules (100% Accuracy for obvious types)
        if doc_type == "criminal_procedure": return "Procedure"
        if doc_type == "landmark_precedent": return "Binding Precedents" # Special handling later
        if doc_type == "recent_judgement": return "Persuasive Authority"

        # Defense Heuristic: Sri Lanka Penal Code Sections 69 to 99 are General Exceptions (Defense)
        if doc_type == "penal_code" and section != "N/A":
            import re
            match = re.search(r'\b(?:Section|Sec\.?)\s*(\d+[a-zA-Z]?)\b', section, re.IGNORECASE)
            if not match:
                match = re.search(r'\b(\d+[a-zA-Z]?)\b', section)
            
            if match:
                try:
                    num_str = re.search(r'\d+', match.group(1)).group()
                    sec_num = int(num_str)
                    if 69 <= sec_num <= 99:
                        return "Defense"
                except:
                    pass

        # 2. Vector Math for Penal Code / Ambiguous items
        # Embed the text using the local model
        doc_vector = self.emb_fn([text])[0]
        
        # Calculate similarity to anchors
        scores = {}
        for category, anchor_vector in self.anchors.items():
            # Reshape for sklearn
            v1 = np.array(doc_vector).reshape(1, -1)
            v2 = np.array(anchor_vector).reshape(1, -1)
            scores[category] = cosine_similarity(v1, v2)[0][0]

        # Return the category with the highest score
        best_category = max(scores, key=scores.get)
        return best_category

    def normalize_landmark_case(self, title, text, existing_details=None):
        """
        Extracts Judge, Place, and Outcome (Sentence) from a landmark case summary.
        Also extracts key headnote points.
        Prioritizes existing details from metadata.
        """
        if existing_details and existing_details.get("judges") != "Not Documented":
            # If we already have metadata from the DB, just parse the headnotes if missing
            if not existing_details.get("headnotes") and existing_details.get("hn_str"):
                existing_details["headnotes"] = [p.strip() for p in existing_details["hn_str"].split("|")[:5]]
            return existing_details

        # Truncate text to avoid context limit but keep enough for extraction
        sample_text = text[:3000]
        prompt = f"""
        Analyze this Sri Lankan Landmark Case:
        TITLE: {title}
        TEXT: {sample_text}

        TASK: Extract the following into a valid JSON object:
        1. "judges": The name(s) of the presiding judge(s).
        2. "place": The court or city where the judgment was delivered.
        3. "outcome": The final ruling or sentence (one sentence).
        4. "headnotes": A list of the 3-5 most important legal principles established (max 15 words per point).

        RETURN ONLY JSON:
        {{
            "judges": "...",
            "place": "...",
            "outcome": "...",
            "headnotes": ["Point 1", "Point 2", "Point 3"]
        }}
        """
        try:
            res = self.llm.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            return json.loads(res.text)
        except Exception as e:
            print(f"   ⚠️ Landmark Normalization Error: {e}")
            return {
                "judges": "Not Documented",
                "place": "Supreme Court",
                "outcome": "See Ratio",
                "headnotes": []
            }

    def clean_title(self, title):
        return title.replace(".pdf", "").replace("_", " ").replace(".json", "").title()

    def extract_resources(self, case_facts: str):
        print(f"   [Core] Extracting Resources for: {case_facts[:50]}...")
        
        # --- STEP 1: RETRIEVAL ---
        prosecution_query = case_facts
        defense_query = self.generate_defense_query(case_facts)
        search_queries = [prosecution_query, defense_query]
        
        categories = [
            {"type": "penal_code", "count": 5}, 
            {"type": "criminal_procedure", "count": 5},
            {"type": "landmark_precedent", "count": 2}
        ]

        unique_results = {} 

        for query_text in search_queries:
            for cat in categories:
                res = self.collection.query(
                    query_texts=[query_text], 
                    n_results=cat['count'], 
                    where={"type": cat['type']}, 
                    include=["metadatas", "documents", "distances"]
                )
                
                if res['ids'] and res['ids'][0]:
                    for i in range(len(res['ids'][0])):
                        uid = res['ids'][0][i]
                        if uid not in unique_results:
                            meta = res['metadatas'][0][i]
                            full_text = meta.get('full_text', res['documents'][0][i])
                            clean_t = self.clean_title(meta.get('title', 'Unknown'))
                            clean_s = self.clean_title(meta.get('section', 'N/A'))
                            
                            # Robustly clean raw JSON headnotes from the excerpt
                            excerpt = full_text
                            try:
                                import re
                                # Pattern to find stringified list of dicts at the start or middle
                                json_pattern = r'\[\s*{\s*[\'"]point_number[\'"]\s*:.*?\s*}\s*(?:,\s*{\s*[\'"]point_number[\'"]\s*:.*?\s*}\s*)*\]'
                                
                                # If it's there, we might want to extract the points before stripping
                                hn_match = re.search(json_pattern, excerpt)
                                if hn_match:
                                    raw_hn = hn_match.group(0)
                                    excerpt = excerpt.replace(raw_hn, "").strip()
                                    
                                    # If hn_str is missing, try to reconstruct it from this raw JSON
                                    if not meta.get("hn_str"):
                                        try:
                                            import ast
                                            parsed_hn = ast.literal_eval(raw_hn)
                                            meta["hn_str"] = " | ".join([p.get("summary", "") for p in parsed_hn if isinstance(p, dict)])
                                        except: pass
                            except Exception as e:
                                print(f"   ⚠️ Excerpt cleaning error: {e}")

                            unique_results[uid] = {
                                "id": uid,
                                "title": clean_t,
                                "section": clean_s,
                                "type": meta.get('type', 'Unknown'),
                                "excerpt": excerpt,
                                "distance": res['distances'][0][i],
                                # Carry over metadata fields
                                "judges": meta.get("judges", "Not Documented"),
                                "place": meta.get("place", "Supreme Court"), # Try 'place' key first
                                "court": meta.get("court", "Supreme Court"), # Fallback to 'court'
                                "outcome": meta.get("outcome", "See Ratio"),
                                "hn_str": meta.get("hn_str", ""),
                                "refs_str": meta.get("refs_str", ""),
                                "judg_json": meta.get("judg_json", "[]")
                            }

        all_matches = list(unique_results.values())
        all_matches.sort(key=lambda x: x['distance'])
        
        if not all_matches: return {"error": "No matches found."}

        # --- STEP 2: LOCAL CLASSIFICATION (Fast & Research-Grade) ---
        print(f"   [Core] Classifying {len(all_matches)} Resources using Vector Math...")
        
        G = nx.DiGraph()
        G.add_node("Case", label="Case Facts", type="root")
        
        # ── HIERARCHICAL HUB TOPOLOGY ──────────────────────────────────────
        # Penal Code hub sits between Case and the Prosecution/Defense branches.
        # This reflects that both adversarial branches are derived from the
        # Sri Lanka Penal Code, while Procedure and Case Law are separate axes.
        G.add_node("Penal_Code",          label="Penal Code",               type="statute_hub")
        G.add_node("Prosecution",         label="Prosecution Resources",     type="branch_hub")
        G.add_node("Defense",             label="Defense Resources",         type="branch_hub")
        G.add_node("Procedure",           label="Criminal Procedure",        type="branch_hub")
        G.add_node("Binding_Precedents",  label="Binding Precedents",        type="branch_hub")

        # Case → Penal_Code → Prosecution / Defense
        G.add_edge("Case",        "Penal_Code",           relation="governed_by")
        G.add_edge("Penal_Code",  "Prosecution",          relation="charges_under")
        G.add_edge("Penal_Code",  "Defense",              relation="exceptions_under")
        # Case directly → Procedure and Case Law
        G.add_edge("Case",        "Procedure",            relation="requires")
        G.add_edge("Case",        "Binding_Precedents",   relation="precedent_from")

        hubs = ["Penal_Code", "Prosecution", "Defense", "Procedure", "Binding_Precedents"]

        grouped_resources = {
            "prosecution_resources": [],
            "defense_resources": [],
            "procedural_resources": [],
            "binding_precedents": []
        }

        for match in all_matches:
            # Use Local Vector Math to decide side
            side = self.classify_local(match['excerpt'], match['type'], match['section'])
            
            # Map 'side' to our JSON buckets
            target_bucket = ""
            if side == "Prosecution":        target_bucket = "prosecution_resources"
            elif side == "Defense":          target_bucket = "defense_resources"
            elif side == "Procedure":        target_bucket = "procedural_resources"
            elif side == "Binding Precedents": target_bucket = "binding_precedents"
            # Hiding Persuasive Authority from UI as requested
            elif side == "Persuasive Authority": continue
            
            # Add document node
            G.add_node(match['id'], label=match['title'], section=match['section'], type=match['type'])
            
            # Link to the correct Hub based on classification
            hub_name = side.replace(" ", "_")  # e.g. "Binding Precedents" → "Binding_Precedents"
            if hub_name in hubs:
                G.add_edge(hub_name, match['id'], relation="applies")
            
            # Add to JSON bucket
            if target_bucket:
                match['side'] = side
                match['similarity'] = round(1 - match['distance'], 4)
                del match['distance']
                
                # --- LANDMARK ENHANCEMENT ---
                if match['type'] == 'landmark_precedent':
                    print(f"   [Core] Refining Landmark: {match['title']}...")
                    # Pass existing metadata to normalize_landmark_case
                    details = self.normalize_landmark_case(match['title'], match['excerpt'], existing_details=match.copy())
                    match.update(details)
                    
                    # Add Graph Branches (Judges, Place, Outcome)
                    for attr_type, attr_val in [("Judges", match.get("judges")), ("Place", match.get("place")), ("Outcome", match.get("outcome"))]:
                        if attr_val and attr_val not in ["Not Documented", "N/A"]:
                            attr_id = f"{match['id']}_{attr_type}"
                            G.add_node(attr_id, label=f"{attr_type}: {str(attr_val)[:20]}", type="attribute")
                            G.add_edge(match['id'], attr_id, relation="detail")
                
                grouped_resources[target_bucket].append(match)

        # --- FINAL PASS: HIGHLIGHT RECOMMENDATIONS ---
        # Sort landmark cases by similarity and pick the best one to recommend
        if grouped_resources["binding_precedents"]:
            # Strictly limit to top 2
            grouped_resources["binding_precedents"] = grouped_resources["binding_precedents"][:2]
            # Already sorted by distance (ascending), so first is best
            grouped_resources["binding_precedents"][0]["recommended"] = True

        return {
            "summary": f"Extracted {len(all_matches)} resources. Priority given to Landmark Precedents.",
            "structured_data": grouped_resources,
            "graph_data": nx.cytoscape_data(G)
        }