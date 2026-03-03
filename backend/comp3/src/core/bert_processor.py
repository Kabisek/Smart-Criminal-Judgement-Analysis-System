"""
BERT processor for generating Legal-BERT embeddings
"""
import torch
from transformers import AutoTokenizer, AutoModel
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class BERTProcessor:
    """Handles BERT embedding generation for legal text"""
    
    def __init__(self, model_name: str = "nlpaueb/legal-bert-base-uncased", device: str = "cpu"):
        """
        Initialize BERT processor
        
        Args:
            model_name: HuggingFace model name
            device: Device to run model on ('cpu' or 'cuda')
        """
        self.model_name = model_name
        self.device = torch.device(device)
        
        logger.info(f"Loading BERT model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()
        logger.info("BERT model loaded successfully")
    
    def get_embedding(self, text: str, max_length: int = 512) -> np.ndarray:
        """
        Generate BERT embedding for input text
        
        Args:
            text: Input text to embed
            max_length: Maximum sequence length
            
        Returns:
            768-dimensional embedding array
        """
        # Truncate text if too long
        text = text[:2000]
        
        # Tokenize text
        inputs = self.tokenizer(
            text,
            return_tensors='pt',
            truncation=True,
            max_length=max_length,
            padding='max_length'
        )
        
        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate embedding
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Use [CLS] token embedding (first token)
        embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()
        return embedding.flatten()
    
    def get_embeddings_batch(self, texts: list, max_length: int = 512) -> np.ndarray:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of input texts
            max_length: Maximum sequence length
            
        Returns:
            Array of embeddings (n_texts, 768)
        """
        embeddings = []
        for text in texts:
            embedding = self.get_embedding(text, max_length)
            embeddings.append(embedding)
        
        return np.array(embeddings)
