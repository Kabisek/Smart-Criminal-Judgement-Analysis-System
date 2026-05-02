"""
Cluster Predictor - K-Means integration for argument generation
Loads trained K-Means model and predicts cluster for new case embeddings.
Used for panel demonstration: best trained model in the pipeline.
"""
import pickle
import logging
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class ClusterPredictor:
    """
    Predicts cluster assignment for case embeddings using trained K-Means.
    K-Means was trained with L2-normalized embeddings (cosine similarity).
    """

    def __init__(self, models_dir: Optional[Path] = None):
        """
        Initialize cluster predictor. Loads K-Means from models_dir.

        Args:
            models_dir: Path to models directory (default: from config)
        """
        if models_dir is None:
            from comp2.api.config import MODELS_DIR
            models_dir = MODELS_DIR

        self.models_dir = Path(models_dir)
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        """Load K-Means model from disk. Graceful fallback if missing."""
        kmeans_path = self.models_dir / "kmeans_model.pkl"
        if not kmeans_path.exists():
            logger.warning(
                f"K-Means model not found at {kmeans_path}. "
                "Copy kmeans_model.pkl from backend2/data/models to backend/data/models. "
                "Using cluster_id=0 as fallback."
            )
            return

        try:
            with open(kmeans_path, "rb") as f:
                self.model = pickle.load(f)
            logger.info(f"K-Means model loaded from {kmeans_path}")
        except Exception as e:
            logger.warning(f"Failed to load K-Means model: {e}. Using cluster_id=0 as fallback.")
            self.model = None

    def predict_cluster(self, embedding: np.ndarray) -> int:
        """
        Predict cluster (0 to n_clusters-1) for a case embedding.

        K-Means was trained with L2-normalized embeddings. We normalize
        the query embedding the same way before prediction.

        Args:
            embedding: 1D or 2D embedding from Legal-BERT (shape: (768,) or (1, 768))

        Returns:
            Cluster ID (0 to n_clusters-1), or 0 if model not loaded
        """
        if self.model is None:
            return 0

        try:
            from sklearn.preprocessing import normalize
            emb = np.asarray(embedding, dtype=np.float32)
            if emb.ndim == 1:
                emb = emb.reshape(1, -1)
            emb_normalized = normalize(emb, norm="l2")
            labels = self.model.predict(emb_normalized)
            return int(labels[0])
        except Exception as e:
            logger.warning(f"Cluster prediction failed: {e}. Using cluster_id=0.")
            return 0
