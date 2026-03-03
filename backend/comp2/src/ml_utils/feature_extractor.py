"""
Feature Extraction Module
Converts text documents to vector embeddings using sentence transformers
Supports Legal-BERT (pre-trained or fine-tuned) for legal domain embeddings
"""

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from pathlib import Path
import pickle
from tqdm import tqdm
import logging
import os

logger = logging.getLogger(__name__)

class FeatureExtractor:
    """Extract vector features from text documents using Legal-BERT or other models"""
    
    def __init__(self, model_name=None, fine_tuned_model_path=None):
        """
        Initialize feature extractor with Legal-BERT (recommended for legal domain)
        
        Args:
            model_name: Name of sentence transformer model to use.
                       Defaults to 'nlpaueb/legal-bert-base-uncased' (Legal-BERT)
            fine_tuned_model_path: Path to fine-tuned model directory (optional).
                                  If provided, this will be used instead of model_name
        """
        # Determine which model to use
        if fine_tuned_model_path:
            model_path = Path(fine_tuned_model_path)
            if not model_path.exists():
                raise FileNotFoundError(f"Fine-tuned model path not found: {fine_tuned_model_path}")
            print(f"Loading fine-tuned Legal-BERT model from: {fine_tuned_model_path}")
            self.model = SentenceTransformer(str(model_path))
            self.model_name = f"Fine-tuned Legal-BERT ({fine_tuned_model_path})"
        elif model_name:
            print(f"Loading embedding model: {model_name}")
            self.model = SentenceTransformer(model_name)
            self.model_name = model_name
        else:
            # Default to Legal-BERT (pre-trained)
            default_model = 'nlpaueb/legal-bert-base-uncased'
            print(f"Loading Legal-BERT (pre-trained): {default_model}")
            print("   Note: This model is optimized for legal domain text")
            self.model = SentenceTransformer(default_model)
            self.model_name = default_model
        
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"✅ Model loaded: {self.model_name}")
        print(f"   Embedding dimension: {self.embedding_dim}")
    
    def extract_embeddings(self, texts: list, batch_size: int = 32, show_progress: bool = True) -> np.ndarray:
        """
        Extract embeddings from a list of texts
        
        Args:
            texts: List of text strings
            batch_size: Batch size for processing
            show_progress: Whether to show progress bar
            
        Returns:
            np.ndarray: Array of embeddings (n_samples, embedding_dim)
        """
        if not texts:
            return np.array([])
        
        # Convert to list of strings
        text_list = [str(text) if text else "" for text in texts]
        
        # Generate embeddings
        if show_progress:
            embeddings = self.model.encode(
                text_list,
                batch_size=batch_size,
                show_progress_bar=True,
                convert_to_numpy=True
            )
        else:
            embeddings = self.model.encode(
                text_list,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True
            )
        
        return embeddings
    
    def process_dataframe(self, df: pd.DataFrame, text_column: str = "cleaned_text", 
                         case_id_column: str = "case_id", max_chunk_size: int = 512) -> tuple:
        """
        Process DataFrame and extract features
        
        Args:
            df: DataFrame with text documents
            text_column: Column name containing text
            case_id_column: Column name containing case IDs
            max_chunk_size: Maximum characters per chunk (for long documents)
            
        Returns:
            tuple: (embeddings array, case_ids list)
        """
        print(f"Processing {len(df)} documents...")
        
        # Get texts and case IDs
        texts = df[text_column].tolist()
        case_ids = df[case_id_column].tolist()
        
        # Handle long texts by chunking (optional - can be enhanced)
        processed_texts = []
        processed_case_ids = []
        
        for text, case_id in zip(texts, case_ids):
            if len(text) > max_chunk_size * 10:  # Very long texts
                # Simple chunking: take first chunk (can be enhanced)
                text = text[:max_chunk_size * 10]
            processed_texts.append(text)
            processed_case_ids.append(case_id)
        
        # Extract embeddings
        embeddings = self.extract_embeddings(processed_texts)
        
        print(f"✅ Feature extraction complete!")
        print(f"   Embeddings shape: {embeddings.shape}")
        print(f"   Case IDs: {len(processed_case_ids)}")
        
        return embeddings, processed_case_ids
    
    def save_features(self, embeddings: np.ndarray, case_ids: list, 
                     output_dir: str = "data/features"):
        """
        Save extracted features to disk
        
        Args:
            embeddings: Embedding vectors
            case_ids: List of case IDs
            output_dir: Directory to save features
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save embeddings and case IDs
        feature_data = {
            'embeddings': embeddings,
            'case_ids': case_ids,
            'embedding_dim': embeddings.shape[1] if len(embeddings) > 0 else 0,
            'num_cases': len(case_ids)
        }
        
        feature_file = output_path / "feature_vectors.pkl"
        with open(feature_file, 'wb') as f:
            pickle.dump(feature_data, f)
        
        print(f"✅ Features saved to: {feature_file}")
        print(f"   Embeddings: {embeddings.shape}")
        print(f"   Case IDs: {len(case_ids)}")
    
    def load_features(self, feature_file: str = "data/features/feature_vectors.pkl") -> tuple:
        """
        Load features from disk
        
        Args:
            feature_file: Path to feature file
            
        Returns:
            tuple: (embeddings array, case_ids list)
        """
        feature_path = Path(feature_file)
        
        if not feature_path.exists():
            raise FileNotFoundError(f"Feature file not found: {feature_file}")
        
        with open(feature_path, 'rb') as f:
            feature_data = pickle.load(f)
        
        embeddings = feature_data['embeddings']
        case_ids = feature_data['case_ids']
        
        print(f"✅ Features loaded from: {feature_file}")
        print(f"   Embeddings shape: {embeddings.shape}")
        print(f"   Case IDs: {len(case_ids)}")
        
        return embeddings, case_ids

