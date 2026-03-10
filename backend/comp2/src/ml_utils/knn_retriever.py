"""
KNN Retriever - Trained Nearest Neighbors model for similarity search
Uses cosine similarity to find k-nearest cases. Integrates with ChromaDB for document lookup.
KNN is compulsory for argument pattern extraction.
"""
import pickle
import logging
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np

logger = logging.getLogger(__name__)


class KNNRetriever:
    """
    Finds similar cases using trained KNN (Nearest Neighbors) model with cosine similarity.
    Maps KNN indices to ChromaDB ids for document lookup.
    """

    def __init__(
        self,
        models_dir: Optional[Path] = None,
        chroma_store=None,
    ):
        """
        Initialize KNN retriever. Loads model and builds index-to-id mapping from ChromaDB.

        Args:
            models_dir: Path to models directory (default: from config)
            chroma_store: ChromaStore instance for get_all_embeddings (default: create from config)
        """
        if models_dir is None:
            from comp2.api.config import MODELS_DIR
            models_dir = MODELS_DIR

        self.models_dir = Path(models_dir)
        self.model = None
        self.chroma_ids: List[str] = []
        self.chroma_store = chroma_store
        self._load_model()
        self._build_id_mapping()

    def _load_model(self) -> None:
        """Load KNN model from disk. Required for argument pattern extraction."""
        for name in ("final_nearest_neighbors_model.pkl", "nearest_neighbors_model.pkl"):
            path = self.models_dir / name
            if path.exists():
                try:
                    with open(path, "rb") as f:
                        self.model = pickle.load(f)
                    logger.info(f"KNN model loaded from {path}")
                    return
                except Exception as e:
                    logger.warning(f"Failed to load KNN from {path}: {e}")

        logger.warning(
            "KNN model not found. Copy final_nearest_neighbors_model.pkl from backend2/data/models. "
            "Argument pattern extraction will fail."
        )
        self.model = None

    def _build_id_mapping(self) -> None:
        """Build KNN index -> ChromaDB id mapping. KNN index i = chroma_ids[i]."""
        self.chroma_ids = []
        if self.model is None:
            return

        if self.chroma_store is None:
            try:
                from comp2.src.retrieval.chroma_store import ChromaStore
                from comp2.api.config import CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME
                self.chroma_store = ChromaStore(
                    persist_directory=str(CHROMA_PERSIST_DIR),
                    collection_name=CHROMA_COLLECTION_NAME,
                )
            except Exception as e:
                logger.warning(f"Cannot init ChromaStore for KNN mapping: {e}")
                return

        try:
            _, ids = self.chroma_store.get_all_embeddings()
            self.chroma_ids = ids
            if len(self.chroma_ids) != self.model.n_samples_fit_:
                logger.warning(
                    f"ChromaDB count ({len(self.chroma_ids)}) != KNN fitted samples "
                    f"({self.model.n_samples_fit_}). KNN mapping may be incorrect."
                )
            else:
                logger.info(f"KNN index mapping built: {len(self.chroma_ids)} ids")
        except Exception as e:
            logger.warning(f"Failed to build KNN id mapping: {e}")
            self.chroma_ids = []

    def find_similar(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
    ) -> Tuple[List[str], List[float]]:
        """
        Find similar cases using KNN (cosine similarity).
        Returns ChromaDB ids and distances for document lookup.

        Args:
            query_embedding: 1D or 2D embedding from Legal-BERT
            top_k: Number of neighbors to return

        Returns:
            (chroma_ids, distances) - empty if model/mapping unavailable
        """
        if self.model is None or not self.chroma_ids:
            return [], []

        try:
            emb = np.asarray(query_embedding, dtype=np.float32)
            if emb.ndim == 1:
                emb = emb.reshape(1, -1)

            k = min(top_k, len(self.chroma_ids), self.model.n_samples_fit_)
            if k <= 0:
                return [], []

            distances, indices = self.model.kneighbors(emb, n_neighbors=k)
            distances = distances[0].tolist()
            indices = indices[0].tolist()

            chroma_ids = []
            for i in indices:
                if 0 <= i < len(self.chroma_ids):
                    chroma_ids.append(self.chroma_ids[i])
                else:
                    logger.warning(f"KNN index {i} out of range for chroma_ids (len={len(self.chroma_ids)})")

            return chroma_ids, distances
        except Exception as e:
            logger.warning(f"KNN find_similar failed: {e}")
            return [], []

    def is_available(self) -> bool:
        """Return True if KNN model and mapping are ready."""
        return self.model is not None and len(self.chroma_ids) > 0
