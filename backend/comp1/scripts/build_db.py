# # import json
# # import os
# # import chromadb
# # from chromadb.utils import embedding_functions

# # # --- CONFIGURATION ---
# # DATA_DIR = "../data/structured"
# # DB_DIR = "../data/chroma_db"

# # client = chromadb.PersistentClient(path=DB_DIR)
# # emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-mpnet-base-v2")

# # collection = client.get_or_create_collection(
# #     name="legal_knowledge_base",
# #     embedding_function=emb_fn,
# #     metadata={"hnsw:space": "cosine"}
# # )

# # def clean_text(text):
# #     """Helper to clean list or string text"""
# #     if isinstance(text, list):
# #         return " ".join([str(t) for t in text])
# #     return str(text)

# # def process_file(filename, doc_type):
# #     filepath = os.path.join(DATA_DIR, filename)
# #     if not os.path.exists(filepath):
# #         print(f"⚠️  Skipping {filename} (Not found)")
# #         return

# #     try:
# #         with open(filepath, 'r', encoding='utf-8') as f:
# #             data = json.load(f)
# #     except Exception as e:
# #         print(f"❌ Error reading {filename}: {e}")
# #         return

# #     items_to_add = []

# #     # --- LOGIC FOR PENAL CODE (Chapters -> Sections) ---
# #     if "penalcodes" in filename or "chapters" in data:
# #         print(f"   -> Parsing Penal Code structure for {filename}")
# #         # Handle if wrapped in "chapters" key or is a list
# #         chapters = data.get("chapters", []) if isinstance(data, dict) else data
        
# #         for chapter in chapters:
# #             chap_title = chapter.get("chapter_title", "")
# #             for section in chapter.get("sections", []):
# #                 items_to_add.append({
# #                     "title": section.get("section_title", "Unknown"),
# #                     "section_id": section.get("section_number", "N/A"),
# #                     "content": section.get("content", ""),
# #                     "context": f"Chapter: {chap_title}",
# #                     "source": filename
# #                 })

# #     # --- LOGIC FOR PROCEDURES (Parts -> Chapters -> Sections) ---
# #     elif "procedures" in filename or "parts" in data:
# #         print(f"   -> Parsing Criminal Procedure structure for {filename}")
# #         parts = data.get("parts", [])
# #         for part in parts:
# #             for chapter in part.get("chapters", []):
# #                 for section in chapter.get("sections", []):
# #                     items_to_add.append({
# #                         "title": section.get("section_title", "Unknown"),
# #                         "section_id": section.get("section_number", "N/A"),
# #                         "content": section.get("content", ""),
# #                         "context": f"Part: {part.get('part_title', '')}",
# #                         "source": filename
# #                     })

# #     # --- LOGIC FOR LANDMARK CASES (Single Object) ---
# #     elif "landmark" in filename:
# #         print(f"   -> Parsing Landmark Case: {filename}")
# #         # Your landmark files are single objects, not lists
# #         meta = data.get("case_metadata", {})
        
# #         # specific handling for judgment text which is a list of dicts
# #         judgment_raw = data.get("judgment_text", [])
# #         judgment_str = ""
# #         if isinstance(judgment_raw, list):
# #             for j_part in judgment_raw:
# #                 if isinstance(j_part, dict):
# #                     judgment_str += j_part.get("content", "") + " "
# #                 else:
# #                     judgment_str += str(j_part) + " "
        
# #         headnotes = clean_text(data.get("headnotes", ""))
        
# #         items_to_add.append({
# #             "title": meta.get("case_name", "Unknown Case"),
# #             "section_id": meta.get("citation", meta.get("case_number", "N/A")),
# #             "content": f"{headnotes} \n {judgment_str[:8000]}", # Limit text size for embedding
# #             "context": f"Court: {meta.get('court', '')}, Judges: {clean_text(meta.get('judges', []))}",
# #             "source": filename
# #         })

# #     # --- BATCH ADD TO DB ---
# #     if not items_to_add:
# #         print(f"⚠️  No items extracted from {filename}")
# #         return

# #     documents = []
# #     metadatas = []
# #     ids = []

# #     for idx, item in enumerate(items_to_add):
# #         # Create the vector text
# #         embed_text = f"{item['title']}. {item['content']}. {item['context']}"
        
# #         documents.append(embed_text)
# #         metadatas.append({
# #             "type": doc_type,
# #             "title": item['title'],
# #             "section": str(item['section_id']), # Ensure string
# #             "source": item['source']
# #         })
# #         # Create unique ID
# #         clean_fname = filename.replace(".json", "")
# #         ids.append(f"{doc_type}_{clean_fname}_{idx}")

# #     # Add in batches
# #     batch_size = 100
# #     for i in range(0, len(documents), batch_size):
# #         collection.add(
# #             documents=documents[i:i+batch_size],
# #             metadatas=metadatas[i:i+batch_size],
# #             ids=ids[i:i+batch_size]
# #         )
    
# #     print(f"✅ Indexed {len(documents)} items from {filename}")

# # if __name__ == "__main__":
# #     print("🚀 Starting Database Build...")
    
# #     # 1. Penal Code
# #     process_file("penalcodes.json", "penal_code")
    
# #     # 2. Procedures
# #     process_file("procedures.json", "criminal_procedure")
    
# #     # 3. Landmark Cases (Add all your filenames here)
# #     landmark_files = [
# #         "landmark.json", "landmark2.json", "landmark3.json", 
# #         "landmark4.json", "landmark5.json", "landmark7.json"
# #     ]
    
# #     for lm in landmark_files:
# #         process_file(lm, "landmark_case")

# #     print("\n🎉 Database Build Complete!")

# import json
# import os
# import shutil
# import chromadb
# from chromadb.utils import embedding_functions

# # --- CONFIGURATION ---
# # Paths relative to this script
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# DATA_DIR = os.path.join(BASE_DIR, "data", "structured")
# DB_DIR = os.path.join(BASE_DIR, "data", "chroma_db")
# MODEL_PATH = os.path.join(BASE_DIR, "models", "sri_lanka_legal_bert")

# def build_db():
#     # 1. Reset DB
#     if os.path.exists(DB_DIR):
#         shutil.rmtree(DB_DIR)
#         print("  Old database deleted.")
    
#     # 2. Load YOUR Fine-Tuned Model
#     print(f" Loading Fine-Tuned Model from: {MODEL_PATH}")
#     if not os.path.exists(MODEL_PATH):
#         print(" CRITICAL ERROR: Model folder not found! Copy 'sri_lanka_legal_bert' to 'models/' folder.")
#         return

#     try:
#         # Load local model via sentence-transformers wrapper
#         emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL_PATH)
#         print("    Custom Sri Lankan Legal-BERT loaded.")
#     except Exception as e:
#         print(f"    Error loading model: {e}")
#         return

#     client = chromadb.PersistentClient(path=DB_DIR)
#     collection = client.get_or_create_collection(name="legal_knowledge_base", embedding_function=emb_fn)

#     # 3. Processing Logic
#     def process_file(filename, doc_type):
#         filepath = os.path.join(DATA_DIR, filename)
#         if not os.path.exists(filepath): return

#         try:
#             with open(filepath, 'r', encoding='utf-8') as f:
#                 data = json.load(f)
#         except: return

#         items = []
        
#         # Logic for Penal Code / Procedures (Nested)
#         if "chapters" in data or "parts" in data:
#             containers = data.get("chapters", []) + data.get("parts", [])
#             for container in containers:
#                 sub_chapters = container.get("chapters", [container])
#                 for sub in sub_chapters:
#                     for section in sub.get("sections", []):
#                         items.append({
#                             "title": section.get("section_title", "Unknown"),
#                             "section": section.get("section_number", "N/A"),
#                             "text": section.get("content", ""),
#                             "source": filename
#                         })
        
#         # Logic for Landmark Cases (Single Object)
#         elif "case_metadata" in data:
#             meta = data.get("case_metadata", {})
#             judg_text = ""
#             raw_judg = data.get("judgment_text", [])
#             for j in raw_judg:
#                 if isinstance(j, dict): judg_text += j.get("content", "") + " "
#                 else: judg_text += str(j) + " "
            
#             items.append({
#                 "title": meta.get("case_name", "Unknown"),
#                 "section": meta.get("citation", "N/A"),
#                 "text": f"{data.get('headnotes', '')} {judg_text[:8000]}", # Limit embedding size
#                 "source": filename
#             })

#         # Add to DB
#         if items:
#             docs, metas, ids = [], [], []
#             for i, item in enumerate(items):
#                 # We embed Title + Text for semantic search
#                 docs.append(f"{item['title']}. {item['text']}")
#                 # We store metadata for retrieval
#                 metas.append({
#                     "title": item['title'], 
#                     "section": str(item['section']), 
#                     "type": doc_type, 
#                     "source": item['source'],
#                     "full_text": item['text'] # Store full text for display
#                 })
#                 ids.append(f"{doc_type}_{filename}_{i}")
            
#             # Batch add
#             batch_size = 50
#             for i in range(0, len(docs), batch_size):
#                 collection.add(
#                     documents=docs[i:i+batch_size],
#                     metadatas=metas[i:i+batch_size],
#                     ids=ids[i:i+batch_size]
#                 )
#             print(f"    Indexed {len(docs)} from {filename}")

#     # 4. Run Ingestion
#     print(" Ingesting Data...")
#     process_file("penalcodes.json", "penal_code")
#     process_file("procedures.json", "criminal_procedure")
    
#     landmark_files = [f for f in os.listdir(DATA_DIR) if "landmark" in f]
#     for lm in landmark_files:
#         process_file(lm, "landmark_case")

#     print("🎉 Database Built Successfully!")

# if __name__ == "__main__":
#     build_db()


import json
import os
import shutil
import chromadb
from chromadb.utils import embedding_functions

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "structured")
DB_DIR = os.path.join(BASE_DIR, "data", "chroma_db")
MODEL_PATH = os.path.join(BASE_DIR, "models", "sri_lanka_legal_bert")

def build_db():
    if os.path.exists(DB_DIR):
        shutil.rmtree(DB_DIR)
        print("🗑️  Old database deleted.")
    
    print(f"🚀 Loading Fine-Tuned Model from: {MODEL_PATH}")
    try:
        emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL_PATH)
    except:
        print("❌ Model not found. Check path.")
        return

    client = chromadb.PersistentClient(path=DB_DIR)
    collection = client.get_or_create_collection(name="legal_knowledge_base", embedding_function=emb_fn)

    def extract_items(data, filename):
        items = []
        
        # 1. Determine Type based on Filename
        if "penal" in filename: doc_type = "penal_code"
        elif "procedure" in filename: doc_type = "criminal_procedure"
        elif "landmark" in filename: doc_type = "landmark_precedent"  # <--- HIGH VALUE
        elif "ocr" in filename: doc_type = "recent_judgement"        # <--- SUPPORTING VALUE
        else: doc_type = "general_law"

        # Helper for cases
        def process_case(case_obj):
            meta = case_obj.get("case_metadata", {})
            judg_text = ""
            for j in case_obj.get("judgment_text", []):
                if isinstance(j, dict): judg_text += j.get("content", "") + " "
                else: judg_text += str(j) + " "
            
            return {
                "title": meta.get("case_name", "Unknown Case"),
                "section": meta.get("citation", "N/A"),
                "text": f"{case_obj.get('headnotes', '')} {judg_text[:8000]}",
                "type": doc_type,
                "source": filename
            }

        # Logic: List (OCR) vs Dict (Landmark/Codes)
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict) and "case_metadata" in entry:
                    items.append(process_case(entry))
        elif isinstance(data, dict):
            if "chapters" in data or "parts" in data:
                containers = data.get("chapters", []) + data.get("parts", [])
                for container in containers:
                    sub_chapters = container.get("chapters", [container])
                    for sub in sub_chapters:
                        for section in sub.get("sections", []):
                            items.append({
                                "title": section.get("section_title", "Unknown"),
                                "section": section.get("section_number", "N/A"),
                                "text": section.get("content", ""),
                                "type": doc_type,
                                "source": filename
                            })
            elif "case_metadata" in data:
                items.append(process_case(data))

        return items

    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]
    print(f"\n📂 Found {len(files)} files...")

    for filename in files:
        filepath = os.path.join(DATA_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            items = extract_items(data, filename)
            if items:
                docs, metas, ids = [], [], []
                for i, item in enumerate(items):
                    docs.append(f"{item['title']}. {item['text']}")
                    metas.append({
                        "title": item['title'], "section": str(item['section']), 
                        "type": item['type'], "source": item['source'], "full_text": item['text']
                    })
                    ids.append(f"{item['type']}_{filename}_{i}")
                
                batch_size = 100
                for i in range(0, len(docs), batch_size):
                    collection.add(
                        documents=docs[i:i+batch_size],
                        metadatas=metas[i:i+batch_size],
                        ids=ids[i:i+batch_size]
                    )
                print(f"    Indexed {len(docs)} items from {filename} as '{items[0]['type']}'")
        except Exception as e:
            print(f"    Error {filename}: {e}")

    print("\n Database Rebuilt with Hierarchical Types!")

if __name__ == "__main__":
    build_db()