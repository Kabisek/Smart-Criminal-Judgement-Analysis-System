"""
Model Evaluator
Evaluates trained models using various metrics
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score
from sklearn.metrics import silhouette_score
from pathlib import Path
import pickle
import logging

from .metrics import calculate_metrics, plot_confusion_matrix, plot_metrics_comparison

logger = logging.getLogger(__name__)

class ModelEvaluator:
    """Evaluate trained ML models"""
    
    def __init__(self):
        self.evaluation_results = {}
    
    def evaluate_nearest_neighbors(self, model, embeddings, case_ids, test_samples=None):
        """
        Evaluate Nearest Neighbors model
        
        Args:
            model: Trained Nearest Neighbors model
            embeddings: Feature vectors
            case_ids: Case IDs
            test_samples: Sample indices for testing (optional)
            
        Returns:
            dict: Evaluation results
        """
        print("Evaluating Nearest Neighbors model...")
        
        # For similarity search, we evaluate retrieval quality
        # Use a sample of embeddings as queries
        if test_samples is None:
            n_test = min(100, len(embeddings) // 10)
            test_samples = np.random.choice(len(embeddings), n_test, replace=False)
        
        query_embeddings = embeddings[test_samples]
        results = []
        
        for i, query in enumerate(query_embeddings):
            distances, indices = model.kneighbors(query.reshape(1, -1), n_neighbors=5)
            
            # Check if query itself is in results (should be first for perfect retrieval)
            query_idx = test_samples[i]
            results.append({
                'query_idx': query_idx,
                'retrieved_indices': indices[0].tolist(),
                'distances': distances[0].tolist(),
                'self_rank': list(indices[0]).index(query_idx) if query_idx in indices[0] else -1
            })
        
        # Calculate retrieval metrics
        self_ranks = [r['self_rank'] for r in results if r['self_rank'] >= 0]
        perfect_retrieval = sum(1 for rank in self_ranks if rank == 0) / len(self_ranks) if self_ranks else 0
        avg_rank = np.mean(self_ranks) if self_ranks else float('inf')
        
        evaluation = {
            'model_type': 'nearest_neighbors',
            'perfect_retrieval_rate': perfect_retrieval,
            'average_rank': avg_rank,
            'n_queries': len(test_samples),
            'n_neighbors': model.n_neighbors
        }
        
        self.evaluation_results['nearest_neighbors'] = evaluation
        print(f"✅ Evaluation complete: Perfect retrieval rate = {perfect_retrieval:.2%}")
        return evaluation
    
    def evaluate_kmeans(self, model, embeddings):
        """
        Evaluate K-Means model (using cosine similarity)
        
        Args:
            model: Trained K-Means model (trained on L2-normalized embeddings)
            embeddings: Feature vectors (will be normalized for evaluation)
            
        Returns:
            dict: Evaluation results
        """
        print("Evaluating K-Means model...")
        
        # Normalize embeddings for cosine similarity (same as training)
        from sklearn.preprocessing import normalize
        embeddings_normalized = normalize(embeddings, norm='l2')
        
        labels = model.labels_
        
        # Calculate clustering metrics using normalized embeddings
        metrics = calculate_metrics(None, labels, metric_type='clustering', X=embeddings_normalized)
        
        evaluation = {
            'model_type': 'kmeans',
            'n_clusters': model.n_clusters,
            'inertia': model.inertia_,
            'silhouette_score': metrics.get('silhouette_score', -1),
            'davies_bouldin_score': metrics.get('davies_bouldin_score', float('inf'))
        }
        
        self.evaluation_results['kmeans'] = evaluation
        print(f"✅ Evaluation complete: Silhouette score = {evaluation['silhouette_score']:.3f}")
        return evaluation
    
    def evaluate_dbscan(self, model, embeddings):
        """
        Evaluate DBSCAN model
        
        Args:
            model: Trained DBSCAN model
            embeddings: Feature vectors
            
        Returns:
            dict: Evaluation results
        """
        print("Evaluating DBSCAN model...")
        
        labels = model.labels_
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)
        
        # Calculate clustering metrics (excluding noise points)
        if n_clusters >= 2:
            metrics = calculate_metrics(None, labels, metric_type='clustering', X=embeddings)
        else:
            metrics = {'silhouette_score': -1, 'davies_bouldin_score': float('inf')}
        
        evaluation = {
            'model_type': 'dbscan',
            'n_clusters': n_clusters,
            'n_noise': n_noise,
            'silhouette_score': metrics.get('silhouette_score', -1),
            'davies_bouldin_score': metrics.get('davies_bouldin_score', float('inf'))
        }
        
        self.evaluation_results['dbscan'] = evaluation
        print(f"✅ Evaluation complete: Clusters = {n_clusters}, Noise = {n_noise}")
        return evaluation
    
    def evaluate_classifier(self, model, model_name: str, embeddings: np.ndarray, 
                           true_labels: np.ndarray, test_size: float = 0.3):
        """
        Evaluate a classification model with comprehensive metrics
        
        Args:
            model: Trained classifier model
            model_name: Name of the model
            embeddings: Feature vectors
            true_labels: True labels
            test_size: Proportion of data for testing
            
        Returns:
            dict: Evaluation results with all metrics
        """
        print(f"Evaluating {model_name} classifier...")
        
        from sklearn.model_selection import train_test_split
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            embeddings, true_labels, test_size=test_size, random_state=42, stratify=true_labels
        )
        
        # For SVM, need to scale
        if model_name == 'svm':
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            y_pred = model.predict(X_test_scaled)
        else:
            y_pred = model.predict(X_test)
        
        # Calculate comprehensive metrics
        metrics = calculate_metrics(y_test, y_pred, metric_type='classification')
        
        evaluation = {
            'model_type': model_name,
            'accuracy': metrics.get('accuracy', 0),
            'precision': metrics.get('precision', 0),
            'recall': metrics.get('recall', 0),
            'f1_score': metrics.get('f1_score', 0),
            'n_samples_train': len(X_train),
            'n_samples_test': len(X_test),
            'n_classes': len(np.unique(true_labels))
        }
        
        # Store predictions for confusion matrix
        evaluation['_y_test'] = y_test
        evaluation['_y_pred'] = y_pred
        
        self.evaluation_results[model_name] = evaluation
        print(f"✅ Evaluation complete: Accuracy = {evaluation['accuracy']:.4f}, "
              f"F1 = {evaluation['f1_score']:.4f}")
        return evaluation
    
    def evaluate_all_models(self, models_dir="data/models", embeddings=None, case_ids=None):
        """
        Evaluate all models in directory with comprehensive metrics
        
        Args:
            models_dir: Directory containing model files
            embeddings: Feature vectors (needed for evaluation)
            case_ids: Case IDs (optional)
        """
        models_path = Path(models_dir)
        
        if not models_path.exists():
            raise FileNotFoundError(f"Models directory not found: {models_dir}")
        
        if embeddings is None:
            raise ValueError("embeddings required for evaluation")
        
        print("="*50)
        print("Evaluating All Models")
        print("="*50)
        
        # Get K-Means labels for classification model evaluation
        kmeans_labels = None
        kmeans_model_path = models_path / "kmeans_model.pkl"
        if kmeans_model_path.exists():
            with open(kmeans_model_path, 'rb') as f:
                kmeans_model = pickle.load(f)
            kmeans_labels = kmeans_model.labels_
        
        # 1. Evaluate Nearest Neighbors (retrieval model)
        nn_model_path = models_path / "nearest_neighbors_model.pkl"
        if nn_model_path.exists():
            with open(nn_model_path, 'rb') as f:
                nn_model = pickle.load(f)
            self.evaluate_nearest_neighbors(nn_model, embeddings, case_ids)
        
        # 2. Evaluate K-Means (clustering)
        if kmeans_model_path.exists():
            with open(kmeans_model_path, 'rb') as f:
                kmeans_model = pickle.load(f)
            self.evaluate_kmeans(kmeans_model, embeddings)
        
        # 3. Evaluate DBSCAN (clustering)
        dbscan_model_path = models_path / "dbscan_model.pkl"
        if dbscan_model_path.exists():
            try:
                with open(dbscan_model_path, 'rb') as f:
                    dbscan_model = pickle.load(f)
                self.evaluate_dbscan(dbscan_model, embeddings)
            except Exception as e:
                print(f"⚠️ DBSCAN evaluation skipped: {e}")
        
        # 4. Evaluate classification models (if labels available)
        if kmeans_labels is not None:
            # KNN Classifiers
            for k in [3, 5, 7]:
                knn_path = models_path / f"knn_classifier_k{k}_model.pkl"
                if knn_path.exists():
                    try:
                        with open(knn_path, 'rb') as f:
                            knn_model = pickle.load(f)
                        self.evaluate_classifier(knn_model, f'knn_classifier_k{k}', 
                                               embeddings, kmeans_labels)
                    except Exception as e:
                        print(f"⚠️ KNN (k={k}) evaluation skipped: {e}")
            
            # Random Forest
            rf_path = models_path / "random_forest_model.pkl"
            if rf_path.exists():
                try:
                    with open(rf_path, 'rb') as f:
                        rf_model = pickle.load(f)
                    self.evaluate_classifier(rf_model, 'random_forest', 
                                           embeddings, kmeans_labels)
                except Exception as e:
                    print(f"⚠️ Random Forest evaluation skipped: {e}")
            
            # SVM
            svm_path = models_path / "svm_model.pkl"
            svm_scaler_path = models_path / "svm_scaler_model.pkl"
            if svm_path.exists() and svm_scaler_path.exists():
                try:
                    with open(svm_path, 'rb') as f:
                        svm_model = pickle.load(f)
                    # Note: SVM evaluation handles scaling internally
                    self.evaluate_classifier(svm_model, 'svm', embeddings, kmeans_labels)
                except Exception as e:
                    print(f"⚠️ SVM evaluation skipped: {e}")
        
        print("\n" + "="*50)
        print("✅ All models evaluated!")
        print("="*50)
        
        return self.evaluation_results
    
    def save_evaluation_results(self, output_path="data/evaluation/evaluation_results.csv"):
        """
        Save evaluation results to CSV (excluding prediction arrays)
        
        Args:
            output_path: Path to save results
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Clean results (remove prediction arrays for CSV)
        clean_results = {}
        for model_name, results in self.evaluation_results.items():
            clean_results[model_name] = {k: v for k, v in results.items() 
                                        if not k.startswith('_')}
        
        # Convert to DataFrame
        df = pd.DataFrame(clean_results).T
        df.to_csv(output_file, index=True)
        
        print(f"✅ Evaluation results saved to: {output_file}")
    
    def plot_all_confusion_matrices(self, output_dir="data/evaluation"):
        """
        Plot and save confusion matrices for all classification models
        
        Args:
            output_dir: Directory to save plots
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for model_name, results in self.evaluation_results.items():
            if '_y_test' in results and '_y_pred' in results:
                try:
                    y_test = results['_y_test']
                    y_pred = results['_y_pred']
                    plot_path = output_path / f"confusion_matrix_{model_name}.png"
                    plot_confusion_matrix(y_test, y_pred, save_path=str(plot_path))
                except Exception as e:
                    print(f"⚠️ Failed to plot confusion matrix for {model_name}: {e}")
    
    def plot_metrics_comparison_all(self, output_dir="data/evaluation"):
        """
        Plot comprehensive metrics comparison for all models
        
        Args:
            output_dir: Directory to save plots
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Clean results for plotting
        clean_results = {}
        for model_name, results in self.evaluation_results.items():
            clean_results[model_name] = {k: v for k, v in results.items() 
                                        if not k.startswith('_')}
        
        try:
            plot_path = output_path / "metrics_comparison.png"
            plot_metrics_comparison(clean_results, save_path=str(plot_path))
        except Exception as e:
            print(f"⚠️ Failed to plot metrics comparison: {e}")
    
    def get_evaluation_results(self):
        """Get evaluation results"""
        return self.evaluation_results

