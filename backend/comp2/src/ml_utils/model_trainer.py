"""
Model Training Module
Trains multiple ML models and compares their performance
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neighbors import NearestNeighbors, KNeighborsClassifier
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from pathlib import Path
import pickle
import logging

logger = logging.getLogger(__name__)

class ModelTrainer:
    """Train and compare multiple ML models"""
    
    def __init__(self):
        self.models = {}
        self.model_results = {}
    
    def train_nearest_neighbors(self, embeddings: np.ndarray, n_neighbors: int = 5, 
                                metric: str = 'cosine', save_path: str = None):
        """
        Train Nearest Neighbors model for similarity search
        
        Args:
            embeddings: Feature vectors
            n_neighbors: Number of neighbors
            metric: Distance metric ('cosine', 'euclidean', etc.)
            save_path: Path to save the model
            
        Returns:
            NearestNeighbors: Trained model
        """
        print(f"Training Nearest Neighbors model (k={n_neighbors}, metric={metric})...")
        
        model = NearestNeighbors(n_neighbors=n_neighbors, metric=metric, algorithm='brute')
        model.fit(embeddings)
        
        self.models['nearest_neighbors'] = model
        self.model_results['nearest_neighbors'] = {
            'n_neighbors': n_neighbors,
            'metric': metric,
            'n_samples': len(embeddings)
        }
        
        if save_path:
            self.save_model(model, save_path, 'nearest_neighbors')
        
        print(f"✅ Nearest Neighbors model trained on {len(embeddings)} samples")
        return model
    
    def train_kmeans(self, embeddings: np.ndarray, n_clusters: int = 10, 
                    save_path: str = None):
        """
        Train K-Means clustering model using cosine similarity
        
        Uses L2 normalization to make euclidean distance equivalent to cosine similarity
        for normalized vectors, which is ideal for text embeddings.
        
        Args:
            embeddings: Feature vectors
            n_clusters: Number of clusters
            save_path: Path to save the model
            
        Returns:
            KMeans: Trained model
        """
        print(f"Training K-Means model (clusters={n_clusters}, using cosine similarity via L2 normalization)...")
        
        # Normalize embeddings for cosine similarity (L2 normalization makes euclidean = cosine)
        from sklearn.preprocessing import normalize
        embeddings_normalized = normalize(embeddings, norm='l2')
        
        model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        model.fit(embeddings_normalized)
        
        self.models['kmeans'] = model
        self.models['kmeans_normalizer'] = 'l2'  # Store normalization type
        self.model_results['kmeans'] = {
            'n_clusters': n_clusters,
            'n_samples': len(embeddings),
            'inertia': model.inertia_,
            'similarity_metric': 'cosine (via L2 normalization)'
        }
        
        if save_path:
            self.save_model(model, save_path, 'kmeans')
            # Save normalization flag
            import pickle
            norm_path = Path(save_path) / "kmeans_normalizer.pkl"
            with open(norm_path, 'wb') as f:
                pickle.dump('l2', f)
        
        print(f"✅ K-Means model trained with {n_clusters} clusters")
        print(f"   Inertia: {model.inertia_:.2f}")
        print(f"   Using cosine similarity (L2-normalized embeddings)")
        return model
    
    def train_dbscan(self, embeddings: np.ndarray, eps: float = 0.5, 
                    min_samples: int = 5, save_path: str = None):
        """
        Train DBSCAN clustering model
        
        Args:
            embeddings: Feature vectors
            eps: Maximum distance between samples in same cluster
            min_samples: Minimum samples in a cluster
            save_path: Path to save the model
            
        Returns:
            DBSCAN: Trained model
        """
        print(f"Training DBSCAN model (eps={eps}, min_samples={min_samples})...")
        
        model = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
        labels = model.fit_predict(embeddings)
        
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)
        
        self.models['dbscan'] = model
        self.model_results['dbscan'] = {
            'eps': eps,
            'min_samples': min_samples,
            'n_clusters': n_clusters,
            'n_noise': n_noise,
            'n_samples': len(embeddings)
        }
        
        if save_path:
            self.save_model(model, save_path, 'dbscan')
        
        print(f"✅ DBSCAN model trained")
        print(f"   Clusters found: {n_clusters}")
        print(f"   Noise points: {n_noise}")
        return model
    
    def train_pca(self, embeddings: np.ndarray, n_components: int = 50, 
                 save_path: str = None):
        """
        Train PCA for dimensionality reduction
        
        Args:
            embeddings: Feature vectors
            n_components: Number of components
            save_path: Path to save the model
            
        Returns:
            PCA: Trained model
        """
        print(f"Training PCA model (components={n_components})...")
        
        model = PCA(n_components=n_components, random_state=42)
        model.fit(embeddings)
        
        explained_variance = model.explained_variance_ratio_.sum()
        
        self.models['pca'] = model
        self.model_results['pca'] = {
            'n_components': n_components,
            'explained_variance': explained_variance,
            'n_samples': len(embeddings)
        }
        
        if save_path:
            self.save_model(model, save_path, 'pca')
        
        print(f"✅ PCA model trained")
        print(f"   Explained variance: {explained_variance:.2%}")
        return model
    
    def train_knn_classifier(self, embeddings: np.ndarray, labels: np.ndarray, 
                             n_neighbors: int = 5, save_path: str = None):
        """
        Train K-Nearest Neighbors Classifier
        
        Args:
            embeddings: Feature vectors
            labels: Target labels (e.g., cluster labels)
            n_neighbors: Number of neighbors
            save_path: Path to save the model
            
        Returns:
            KNeighborsClassifier: Trained model
        """
        print(f"Training KNN Classifier (k={n_neighbors})...")
        
        model = KNeighborsClassifier(n_neighbors=n_neighbors, metric='cosine')
        model.fit(embeddings, labels)
        
        self.models[f'knn_classifier_k{n_neighbors}'] = model
        self.model_results[f'knn_classifier_k{n_neighbors}'] = {
            'n_neighbors': n_neighbors,
            'metric': 'cosine',
            'n_samples': len(embeddings),
            'n_classes': len(np.unique(labels))
        }
        
        if save_path:
            self.save_model(model, save_path, f'knn_classifier_k{n_neighbors}')
        
        print(f"✅ KNN Classifier (k={n_neighbors}) trained on {len(embeddings)} samples")
        return model
    
    def train_random_forest(self, embeddings: np.ndarray, labels: np.ndarray,
                           n_estimators: int = 100, max_depth: int = 10,
                           save_path: str = None):
        """
        Train Random Forest Classifier
        
        Args:
            embeddings: Feature vectors
            labels: Target labels
            n_estimators: Number of trees
            max_depth: Maximum depth of trees
            save_path: Path to save the model
            
        Returns:
            RandomForestClassifier: Trained model
        """
        print(f"Training Random Forest Classifier (trees={n_estimators}, max_depth={max_depth})...")
        
        model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=42,
            n_jobs=-1
        )
        model.fit(embeddings, labels)
        
        self.models['random_forest'] = model
        self.model_results['random_forest'] = {
            'n_estimators': n_estimators,
            'max_depth': max_depth,
            'n_samples': len(embeddings),
            'n_classes': len(np.unique(labels)),
            'feature_importance_mean': model.feature_importances_.mean()
        }
        
        if save_path:
            self.save_model(model, save_path, 'random_forest')
        
        print(f"✅ Random Forest trained with {n_estimators} trees")
        print(f"   Feature importance mean: {model.feature_importances_.mean():.4f}")
        return model
    
    def train_svm(self, embeddings: np.ndarray, labels: np.ndarray,
                 kernel: str = 'rbf', C: float = 1.0, save_path: str = None):
        """
        Train Support Vector Machine
        
        Args:
            embeddings: Feature vectors
            labels: Target labels
            kernel: Kernel type ('rbf', 'linear', 'poly')
            C: Regularization parameter
            save_path: Path to save the model
            
        Returns:
            SVC: Trained model
        """
        print(f"Training SVM Classifier (kernel={kernel}, C={C})...")
        
        # Scale features for SVM
        scaler = StandardScaler()
        embeddings_scaled = scaler.fit_transform(embeddings)
        
        model = SVC(kernel=kernel, C=C, random_state=42, probability=True)
        model.fit(embeddings_scaled, labels)
        
        self.models['svm'] = model
        self.models['svm_scaler'] = scaler  # Save scaler for later use
        self.model_results['svm'] = {
            'kernel': kernel,
            'C': C,
            'n_samples': len(embeddings),
            'n_classes': len(np.unique(labels)),
            'n_support_vectors': len(model.support_vectors_)
        }
        
        if save_path:
            self.save_model(model, save_path, 'svm')
            self.save_model(scaler, save_path, 'svm_scaler')
        
        print(f"✅ SVM trained with {kernel} kernel")
        print(f"   Support vectors: {len(model.support_vectors_)}")
        return model
    
    def train_all_models(self, embeddings: np.ndarray, output_dir: str = "data/models", 
                        use_cluster_labels: bool = True):
        """
        Train all available models
        
        Args:
            embeddings: Feature vectors
            output_dir: Directory to save models
            use_cluster_labels: If True, use K-Means labels for classification models
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print("="*50)
        print("Training Multiple Models")
        print("="*50)
        
        # 1. Train Nearest Neighbors (most important for similarity search)
        self.train_nearest_neighbors(embeddings, n_neighbors=5, save_path=str(output_path))
        
        # 2. Train clustering models
        n_clusters = min(10, len(embeddings) // 100)  # Adaptive number of clusters
        if n_clusters >= 2:
            kmeans_model = self.train_kmeans(embeddings, n_clusters=n_clusters, save_path=str(output_path))
            
            # Use K-Means labels for classification models if requested
            if use_cluster_labels:
                cluster_labels = kmeans_model.labels_
            else:
                cluster_labels = None
        
        # 3. Train DBSCAN clustering
        try:
            dbscan_model = self.train_dbscan(embeddings, eps=0.5, min_samples=5, save_path=str(output_path))
        except Exception as e:
            print(f"⚠️ DBSCAN training skipped: {e}")
        
        # 4. Train PCA for dimensionality reduction
        n_components = min(50, embeddings.shape[1] // 2)
        if n_components >= 2:
            self.train_pca(embeddings, n_components=n_components, save_path=str(output_path))
        
        # 5. Train classification models (if labels available)
        if use_cluster_labels and cluster_labels is not None:
            # KNN Classifiers with different k values
            for k in [3, 5, 7]:
                try:
                    self.train_knn_classifier(embeddings, cluster_labels, n_neighbors=k, save_path=str(output_path))
                except Exception as e:
                    print(f"⚠️ KNN (k={k}) training skipped: {e}")
            
            # Random Forest
            try:
                self.train_random_forest(embeddings, cluster_labels, n_estimators=100, 
                                       max_depth=10, save_path=str(output_path))
            except Exception as e:
                print(f"⚠️ Random Forest training skipped: {e}")
            
            # SVM (with scaling)
            try:
                self.train_svm(embeddings, cluster_labels, kernel='rbf', C=1.0, save_path=str(output_path))
            except Exception as e:
                print(f"⚠️ SVM training skipped: {e}")
        else:
            print("\n⚠️ Classification models skipped (no labels available)")
        
        print("\n" + "="*50)
        print("✅ All models trained successfully!")
        print("="*50)
    
    def save_model(self, model, base_path: str, model_name: str):
        """
        Save a trained model to disk
        
        Args:
            model: Trained model object
            base_path: Base directory path
            model_name: Name of the model
        """
        save_path = Path(base_path) / f"{model_name}_model.pkl"
        with open(save_path, 'wb') as f:
            pickle.dump(model, f)
        print(f"   Model saved to: {save_path}")
    
    def load_model(self, model_path: str):
        """
        Load a trained model from disk
        
        Args:
            model_path: Path to model file
            
        Returns:
            Loaded model object
        """
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        return model
    
    def get_model_results(self):
        """Get results from all trained models"""
        return self.model_results

