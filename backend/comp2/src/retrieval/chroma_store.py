"""
ChromaDB Vector Store for Component 2
Stores legal case embeddings for similarity search.
Uses separate directory (chroma_db_comp2) to avoid conflict with Component 1.
"""

import numpy as np
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


class ChromaStore:
    """
    ChromaDB vector store for legal case embeddings (Component 2).
    Stores embeddings with metadata for similarity search.
    """

    def __init__(
        self,
        persist_directory: str = "data/chroma_db_comp2",
        collection_name: str = "legal_cases",
    ):
        """
        Initialize ChromaDB store.

        Args:
            persist_directory: Path to persist ChromaDB data (separate from comp1)
            collection_name: Name of the collection
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("chromadb not installed. Run: pip install chromadb")

        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self._initialized = False

    def _get_client(self):
        """Lazy init client"""
        if self.client is None:
            self.persist_directory.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(anonymized_telemetry=False),
            )
        return self.client

    def _get_collection(self, create: bool = True):
        """Get or create collection (when create=True)."""
        client = self._get_client()
        if create:
            self.collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        else:
            self.collection = client.get_collection(name=self.collection_name)
        return self.collection

    def add_embeddings(
        self,
        ids: List[str],
        embeddings: np.ndarray,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        batch_size: int = 100,
    ) -> int:
        """
        Add embeddings to ChromaDB.

        Args:
            ids: Case IDs
            embeddings: Embedding vectors (N, dim)
            documents: Text content for each case
            metadatas: Optional metadata per case (values must be str, int, float, bool)
            batch_size: Batch size for adding

        Returns:
            Number of records added
        """
        collection = self._get_collection()

        # Convert embeddings to list of lists (ChromaDB requirement)
        emb_list = embeddings.tolist() if isinstance(embeddings, np.ndarray) else embeddings

        # Sanitize metadata: ChromaDB only accepts str, int, float, bool
        def sanitize_meta(m: Dict) -> Dict:
            if m is None:
                return {}
            out = {}
            for k, v in m.items():
                try:
                    if v is None or (isinstance(v, (int, float)) and np.isnan(v)):
                        continue
                except (TypeError, ValueError):
                    pass
                if v == "" and k != "case_id":
                    continue
                out[k] = str(v) if not isinstance(v, (str, int, float, bool)) else v
            return out

        meta_list = [sanitize_meta(m) for m in (metadatas or [{}] * len(ids))]
        # Ensure non-empty metadata (ChromaDB requires at least one key)
        for j, (mid, meta) in enumerate(zip(ids, meta_list)):
            if not meta:
                meta_list[j] = {"id": str(mid)}

        # Truncate long documents (ChromaDB has limits)
        doc_list = [str(d)[:10000] if d else "" for d in documents]

        # Add in batches
        for i in range(0, len(ids), batch_size):
            end = min(i + batch_size, len(ids))
            collection.add(
                ids=ids[i:end],
                embeddings=emb_list[i:end],
                documents=doc_list[i:end],
                metadatas=meta_list[i:end],
            )

        logger.info(f"Added {len(ids)} records to ChromaDB collection '{self.collection_name}'")
        return len(ids)

    def search(
        self,
        query_embedding: np.ndarray,
        n_results: int = 10,
        include: Optional[List[str]] = None,
    ) -> Tuple[List[str], List[float], List[Dict], List[str]]:
        """
        Search for similar cases.

        Args:
            query_embedding: Query vector (1, dim) or (dim,)
            n_results: Number of results to return
            include: Fields to include (documents, metadatas, distances)

        Returns:
            (ids, distances, metadatas, documents)
        """
        collection = self._get_collection(create=False)

        if isinstance(query_embedding, np.ndarray):
            if query_embedding.ndim == 1:
                query_embedding = query_embedding.reshape(1, -1)
            query_list = query_embedding.tolist()
        else:
            query_list = [query_embedding]

        include = include or ["documents", "metadatas", "distances"]
        results = collection.query(
            query_embeddings=query_list,
            n_results=min(n_results, collection.count()),
            include=include,
        )

        ids = results["ids"][0] if results["ids"] else []
        distances = results["distances"][0] if "distances" in results and results["distances"] else []
        metadatas = results["metadatas"][0] if "metadatas" in results and results["metadatas"] else []
        documents = results["documents"][0] if "documents" in results and results["documents"] else []

        return ids, distances, metadatas, documents

    def count(self) -> int:
        """Return number of records in collection"""
        try:
            collection = self._get_collection(create=False)
            return collection.count()
        except Exception:
            return 0

    def get_all_embeddings(self) -> Tuple[np.ndarray, List[str]]:
        """
        Get all embeddings and ChromaDB ids from the collection.
        Used for KNN index-to-id mapping (same order as training data).

        Returns:
            (embeddings array, chroma_ids list)
        """
        collection = self._get_collection(create=False)
        n = collection.count()
        if n == 0:
            return np.array([]).reshape(0, 0), []

        result = collection.get(include=["embeddings", "metadatas"])
        ids = result["ids"]
        emb_list = result["embeddings"]
        metadatas = result.get("metadatas") or []

        embeddings = np.array(emb_list, dtype=np.float32)
        return embeddings, ids

    def get_by_ids(
        self,
        ids: List[str],
        include: Optional[List[str]] = None,
    ) -> Tuple[List[Dict], List[str]]:
        """
        Fetch documents and metadata by ChromaDB ids.

        Args:
            ids: ChromaDB ids to fetch
            include: Fields to include (default: documents, metadatas)

        Returns:
            (metadatas list, documents list) - flat lists in same order as ids
        """
        if not ids:
            return [], []
        collection = self._get_collection(create=False)
        include = include or ["documents", "metadatas"]
        result = collection.get(ids=ids, include=include)
        metadatas = result.get("metadatas") or []
        documents = result.get("documents") or []
        return list(metadatas), list(documents)
