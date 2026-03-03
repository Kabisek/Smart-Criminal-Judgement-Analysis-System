import pickle
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors
import os

class VectorEngine:
    def __init__(self, data_dir="./data", model_name=None, fine_tuned_model_path=None):
        """
        Initialize Vector Engine for similarity search
        
        Args:
            data_dir: Directory containing data files
            model_name: Embedding model name (defaults to Legal-BERT)
            fine_tuned_model_path: Path to fine-tuned model (optional)
        """
        self.data_dir = Path(data_dir)
        self.vectors_path = self.data_dir / "vectors/feature_vectors.pkl"
        self.cases_path = self.data_dir / "processed/successful_cases.pkl"
        self.model_path = self.data_dir / "vectors/nn_model.pkl"
        
        # Load Embedding Model - Use Legal-BERT by default
        if fine_tuned_model_path:
            model_path = Path(fine_tuned_model_path)
            if not model_path.exists():
                raise FileNotFoundError(f"Fine-tuned model path not found: {fine_tuned_model_path}")
            print(f"Loading fine-tuned Legal-BERT from: {fine_tuned_model_path}")
            self.encoder = SentenceTransformer(str(model_path))
        elif model_name:
            print(f"Loading embedding model: {model_name}")
            self.encoder = SentenceTransformer(model_name)
        else:
            # Default to Legal-BERT (pre-trained)
            default_model = 'nlpaueb/legal-bert-base-uncased'
            print(f"Loading Legal-BERT (pre-trained): {default_model}")
            self.encoder = SentenceTransformer(default_model)
        
        self.case_db = {}
        self.nn_model = None
        self.case_ids = []
        
        self._load_data()

    def _load_data(self):
        """Loads the pre-computed vectors and case text."""
        if not self.vectors_path.exists():
            print("⚠️ No vector database found. Please run the training pipeline first.")
            return

        # Load Vectors
        with open(self.vectors_path, 'rb') as f:
            data = pickle.load(f)
            self.embeddings = data['embeddings']
            self.case_ids = data['case_ids']

        # Load Text Data
        with open(self.cases_path, 'rb') as f:
            cases = pickle.load(f)
            self.case_db = {c['case_id']: c for c in cases}

        # Load or Train NN Model
        if self.model_path.exists():
            with open(self.model_path, 'rb') as f:
                self.nn_model = pickle.load(f)
        else:
            # Train on the fly if model file missing
            self.nn_model = NearestNeighbors(n_neighbors=5, metric='cosine')
            self.nn_model.fit(self.embeddings)

    def search(self, query_text, top_k=3):
        """Finds similar cases."""
        query_vec = self.encoder.encode(query_text[:2000]).reshape(1, -1)
        distances, indices = self.nn_model.kneighbors(query_vec, n_neighbors=top_k)
        
        results = []
        for idx in indices[0]:
            c_id = self.case_ids[idx]
            if c_id in self.case_db:
                results.append(self.case_db[c_id])
        return results