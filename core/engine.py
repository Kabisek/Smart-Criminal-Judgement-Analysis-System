# import chromadb
# from chromadb.utils import embedding_functions
# from sklearn.cluster import DBSCAN
# import numpy as np
# import networkx as nx
# import google.generativeai as genai
# import os
# from dotenv import load_dotenv

# # Load API Key
# load_dotenv()
# genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# class LegalReasoningEngine:
#     def __init__(self, db_path="data/chroma_db"):
#         print(f"   [Core] Connecting to DB at {db_path}...")
#         self.client = chromadb.PersistentClient(path=db_path)
#         self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-mpnet-base-v2")
#         self.collection = self.client.get_collection(
#             name="legal_knowledge_base", 
#             embedding_function=self.emb_fn
#         )
#         self.llm = genai.GenerativeModel(model_name="gemini-2.5-flash")
#         print(f"   [Core] Engine Online. RAG Ready.")

#     def generate_legal_opinion(self, case_facts, retrieved_docs):
#         """
#         Generates a legal argument based on the FULL retrieved context.
#         """
#         context_text = ""
#         for doc in retrieved_docs:
#             # CHANGED: Sending FULL text to the AI for better accuracy
#             context_text += f"- [{doc['type'].upper()}] {doc['title']} (Section {doc['section']}): {doc['excerpt']}\n\n"

#         prompt = f"""
#         You are a Senior Legal Analyst for the Supreme Court of Sri Lanka.
        
#         CASE FACTS:
#         "{case_facts}"

#         RELEVANT LAWS & PRECEDENTS FOUND IN DATABASE:
#         {context_text}

#         TASK:
#         Write a professional "Preliminary Legal Opinion".
#         1. Identify the likely charges based on the Penal Codes provided.
#         2. Suggest the procedural steps based on the Criminal Procedures provided.
#         3. Cite relevant Landmark Cases if they appear in the context.
        
#         Use the full details provided in the context to make your argument specific.
#         """
        
#         try:
#             response = self.llm.generate_content(prompt)
#             return response.text
#         except Exception as e:
#             return f"Could not generate opinion: {e}"

#     def analyze_case(self, case_facts: str):
#         print(f"   [Core] 1. Retrieval (Searching Vector DB)...")
        
#         categories = [
#             {"type": "penal_code", "count": 4},
#             {"type": "criminal_procedure", "count": 4},
#             {"type": "landmark_case", "count": 3}
#         ]

#         all_metas = []
#         all_embeddings = []
#         all_distances = []
#         all_ids = []
#         all_documents = []

#         for cat in categories:
#             results = self.collection.query(
#                 query_texts=[case_facts],
#                 n_results=cat['count'],
#                 where={"type": cat['type']}, 
#                 include=["metadatas", "documents", "embeddings", "distances"]
#             )
#             if results['metadatas'][0]:
#                 all_metas.extend(results['metadatas'][0])
#                 all_embeddings.extend(results['embeddings'][0])
#                 all_distances.extend(results['distances'][0])
#                 all_ids.extend(results['ids'][0])
#                 all_documents.extend(results['documents'][0])

#         if not all_metas:
#             return {"summary": "No matches.", "matches": [], "graph_data": {}}

#         # --- 2. CLUSTERING ---
#         print(f"   [Core] 2. Clustering (DBSCAN)...")
#         if len(all_embeddings) > 1:
#             clustering = DBSCAN(eps=0.3, min_samples=2, metric='cosine').fit(all_embeddings)
#             labels = clustering.labels_
#         else:
#             labels = [0] * len(all_embeddings)

#         # --- 3. GRAPH CONSTRUCTION ---
#         print(f"   [Core] 3. Graph Construction (NetworkX)...")
#         G = nx.DiGraph()
#         G.add_node("Current_Case", label="Case Facts", type="root", cluster="root")
        
#         hubs = {
#             "hub_penal": {"label": "Applicable Laws", "type": "category_hub"},
#             "hub_proc":  {"label": "Procedures",       "type": "category_hub"},
#             "hub_case":  {"label": "Precedents",       "type": "category_hub"}
#         }
#         for hid, hdata in hubs.items():
#             G.add_node(hid, label=hdata['label'], type=hdata['type'], cluster="hub")
#             G.add_edge("Current_Case", hid, relation="investigates")

#         structured_matches = []
        
#         for i, meta in enumerate(all_metas):
#             similarity = 1 - all_distances[i]
#             if similarity < 0.05: continue

#             node_id = all_ids[i]
#             cluster_id = int(labels[i])
#             title = meta.get('title', 'Unknown')
#             doc_type = meta.get('type', 'Unknown')
#             section = meta.get('section', 'N/A')
#             source = meta.get('source', 'Unknown')
            
#             # --- CHANGED: NO TRUNCATION ---
#             full_text = all_documents[i] 
#             excerpt = full_text # We now send the WHOLE text
#             # ------------------------------

#             # Add to Graph
#             G.add_node(node_id, label=title, type=doc_type, cluster=cluster_id, section=section, excerpt=excerpt)
            
#             if doc_type == "penal_code": G.add_edge("hub_penal", node_id, weight=similarity)
#             elif doc_type == "criminal_procedure": G.add_edge("hub_proc", node_id, weight=similarity)
#             elif doc_type == "landmark_case": G.add_edge("hub_case", node_id, weight=similarity)

#             structured_matches.append({
#                 "title": title, "type": doc_type, "section": section, 
#                 "excerpt": excerpt, "similarity": round(similarity, 2)
#             })

#         # Cross-linking
#         nodes = list(G.nodes(data=True))
#         for i in range(len(nodes)):
#             for j in range(i + 1, len(nodes)):
#                 n1, d1 = nodes[i]
#                 n2, d2 = nodes[j]
#                 if "hub_" in str(n1) or "hub_" in str(n2) or "Current_Case" in str(n1): continue
                
#                 if d1.get('cluster') == d2.get('cluster') and d1.get('cluster') != -1:
#                     if d1.get('type') != d2.get('type'):
#                         G.add_edge(n1, n2, relation="cross_reference", weight=0.5)

#         # --- 4. GENERATION ---
#         print(f"   [Core] 4. Generating Legal Opinion (LLM)...")
#         legal_opinion = self.generate_legal_opinion(case_facts, structured_matches)

#         return {
#             "legal_opinion": legal_opinion,
#             "matches": structured_matches,
#             "graph_data": nx.cytoscape_data(G)
#         }

import chromadb
from chromadb.utils import embedding_functions
import networkx as nx
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class LegalReasoningEngine:
    def __init__(self, db_path="data/chroma_db"):
        # Load Fine-Tuned Model
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(BASE_DIR, "models", "sri_lanka_legal_bert")
        
        print(f"   [Core] Loading Fine-Tuned Model from: {model_path}")
        try:
            self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_path)
        except:
            print("   ⚠️ Fine-tuned model not found. Using Base.")
            self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="nlpaueb/legal-bert-base-uncased")

        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_collection(name="legal_knowledge_base", embedding_function=self.emb_fn)
        self.llm = genai.GenerativeModel(model_name="gemini-2.5-flash")
        print("   [Core] System Online.")

    def generate_adversarial_analysis(self, case_facts, retrieved_docs):
        """
        Forces Gemini to classify laws into Prosecution vs Defense.
        """
        context_text = ""
        doc_map = {}
        for i, doc in enumerate(retrieved_docs):
            doc_id = f"DOC_{i}"
            doc_map[doc_id] = doc
            # Send full text to LLM for accurate reasoning
            context_text += f"ID: {doc_id} | TYPE: {doc['type']} | TITLE: {doc['title']} | TEXT: {doc['excerpt'][:1000]}...\n\n"

        prompt = f"""
        You are a Senior Legal Strategist in Sri Lanka.
        
        CASE FACTS: "{case_facts}"
        
        LEGAL DATABASE RESULTS:
        {context_text}

        TASK:
        Perform an Adversarial Analysis.
        1. **Prosecution Argument**: How to prove guilt using these laws?
        2. **Defense Argument**: How to argue for acquittal/mitigation using these laws?
        3. **Classification**: For EACH document ID, assign it to "Prosecution", "Defense", or "Both".

        RETURN JSON ONLY:
        {{
            "prosecution_argument": "...",
            "defense_argument": "...",
            "classifications": {{ "DOC_0": "Prosecution", "DOC_1": "Defense" }}
        }}
        """
        
        try:
            response = self.llm.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            return json.loads(response.text)
        except Exception as e:
            print(f"LLM Error: {e}")
            return {"prosecution_argument": "Error", "defense_argument": "Error", "classifications": {}}

    def analyze_case(self, case_facts: str):
        print(f"   [Core] Analyzing: {case_facts[:50]}...")
        
        # 1. Retrieval (Balanced)
        categories = [{"type": "penal_code", "count": 5}, {"type": "criminal_procedure", "count": 4}, {"type": "landmark_case", "count": 3}]
        all_metas, all_docs, all_ids, all_dists = [], [], [], []

        for cat in categories:
            res = self.collection.query(query_texts=[case_facts], n_results=cat['count'], where={"type": cat['type']}, include=["metadatas", "documents", "distances"])
            if res['metadatas'][0]:
                all_metas.extend(res['metadatas'][0])
                # Retrieve the full text stored in metadata if available, else use document
                # In build_db.py we stored 'full_text' in metadata.
                full_texts = [m.get('full_text', d) for m, d in zip(res['metadatas'][0], res['documents'][0])]
                all_docs.extend(full_texts)
                all_ids.extend(res['ids'][0])
                all_dists.extend(res['distances'][0])

        if not all_metas: return {"error": "No matches found."}

        # Prepare for LLM
        matches_for_llm = []
        for i, meta in enumerate(all_metas):
            matches_for_llm.append({
                "id": all_ids[i],
                "title": meta.get('title', 'Unknown'),
                "section": meta.get('section', 'N/A'),
                "type": meta.get('type', 'Unknown'),
                "excerpt": all_docs[i], # Full Text
                "similarity": 1 - all_dists[i]
            })

        # 2. Adversarial Generation
        print(f"   [Core] Generating Adversarial Arguments...")
        analysis = self.generate_adversarial_analysis(case_facts, matches_for_llm)

        # 3. Graph Construction (2 Branches)
        G = nx.DiGraph()
        G.add_node("Case", label="Case Facts", type="root", cluster="root")
        G.add_node("Prosecution", label="Prosecution", type="party", cluster="prosecution")
        G.add_node("Defense", label="Defense", type="party", cluster="defense")
        
        G.add_edge("Case", "Prosecution", relation="alleges")
        G.add_edge("Case", "Defense", relation="defends")

        final_matches = []
        classifications = analysis.get("classifications", {})
        
        for i, match in enumerate(matches_for_llm):
            doc_key = f"DOC_{i}"
            side = classifications.get(doc_key, "Both")
            
            # Add Node with FULL Excerpt
            G.add_node(match['id'], 
                       label=match['title'], 
                       section=match['section'], 
                       type=match['type'], 
                       excerpt=match['excerpt']) # Sending full text to frontend

            if side == "Prosecution":
                G.add_edge("Prosecution", match['id'], relation="relies_on")
            elif side == "Defense":
                G.add_edge("Defense", match['id'], relation="relies_on")
            else:
                G.add_edge("Prosecution", match['id'], relation="references")
                G.add_edge("Defense", match['id'], relation="references")

            match['side'] = side
            final_matches.append(match)

        return {
            "legal_analysis": {
                "prosecution_argument": analysis.get("prosecution_argument"),
                "defense_argument": analysis.get("defense_argument")
            },
            "matches": final_matches,
            "graph_data": nx.cytoscape_data(G)
        }