"""
Evaluation Metrics Module
Calculates various ML evaluation metrics
"""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, silhouette_score, davies_bouldin_score,
    mean_squared_error, mean_absolute_error, r2_score
)
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def calculate_classification_metrics(y_true, y_pred):
    """
    Calculate classification metrics
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        
    Returns:
        dict: Dictionary of metrics
    """
    metrics = {
        'accuracy': accuracy_score(y_true, y_pred),
        'precision': precision_score(y_true, y_pred, average='weighted', zero_division=0),
        'recall': recall_score(y_true, y_pred, average='weighted', zero_division=0),
        'f1_score': f1_score(y_true, y_pred, average='weighted', zero_division=0)
    }
    return metrics

def calculate_clustering_metrics(X, labels):
    """
    Calculate clustering evaluation metrics
    
    Args:
        X: Feature vectors
        labels: Cluster labels
        
    Returns:
        dict: Dictionary of metrics
    """
    # Remove noise points for DBSCAN
    if -1 in labels:
        mask = labels != -1
        X_clean = X[mask]
        labels_clean = labels[mask]
    else:
        X_clean = X
        labels_clean = labels
    
    if len(set(labels_clean)) < 2:
        return {
            'silhouette_score': -1,
            'davies_bouldin_score': float('inf')
        }
    
    metrics = {}
    
    try:
        metrics['silhouette_score'] = silhouette_score(X_clean, labels_clean, metric='cosine')
    except:
        metrics['silhouette_score'] = -1
    
    try:
        metrics['davies_bouldin_score'] = davies_bouldin_score(X_clean, labels_clean)
    except:
        metrics['davies_bouldin_score'] = float('inf')
    
    return metrics

def calculate_regression_metrics(y_true, y_pred):
    """
    Calculate regression metrics
    
    Args:
        y_true: True values
        y_pred: Predicted values
        
    Returns:
        dict: Dictionary of metrics
    """
    metrics = {
        'mse': mean_squared_error(y_true, y_pred),
        'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
        'mae': mean_absolute_error(y_true, y_pred),
        'r2_score': r2_score(y_true, y_pred)
    }
    return metrics

def calculate_metrics(y_true, y_pred, metric_type='classification', X=None):
    """
    Calculate appropriate metrics based on task type
    
    Args:
        y_true: True labels/values
        y_pred: Predicted labels/values
        metric_type: Type of task ('classification', 'clustering', 'regression')
        X: Feature vectors (needed for clustering)
        
    Returns:
        dict: Dictionary of metrics
    """
    if metric_type == 'classification':
        return calculate_classification_metrics(y_true, y_pred)
    elif metric_type == 'clustering':
        if X is None:
            raise ValueError("X (feature vectors) required for clustering metrics")
        return calculate_clustering_metrics(X, y_pred)
    elif metric_type == 'regression':
        return calculate_regression_metrics(y_true, y_pred)
    else:
        raise ValueError(f"Unknown metric_type: {metric_type}")

def plot_confusion_matrix(y_true, y_pred, labels=None, save_path=None, figsize=(10, 8)):
    """
    Plot confusion matrix
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        labels: Label names (optional)
        save_path: Path to save figure
        figsize: Figure size
    """
    cm = confusion_matrix(y_true, y_pred)
    
    plt.figure(figsize=figsize)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=labels, yticklabels=labels)
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Confusion matrix saved to: {save_path}")
    else:
        plt.show()

def plot_metrics_comparison(metrics_dict, save_path=None, figsize=(16, 10)):
    """
    Plot comprehensive comparison of metrics across models
    
    Args:
        metrics_dict: Dictionary of {model_name: {metric: value}}
        save_path: Path to save figure
        figsize: Figure size
    """
    # Convert to DataFrame
    df = pd.DataFrame(metrics_dict).T
    
    # Determine what metrics we have
    classification_metrics = ['accuracy', 'precision', 'recall', 'f1_score']
    clustering_metrics = ['silhouette_score', 'davies_bouldin_score']
    regression_metrics = ['r2_score', 'mse', 'rmse', 'mae']
    retrieval_metrics = ['perfect_retrieval_rate', 'average_rank']
    
    # Count available metric types
    has_classification = any(m in df.columns for m in classification_metrics)
    has_clustering = any(m in df.columns for m in clustering_metrics)
    has_regression = any(m in df.columns for m in regression_metrics)
    has_retrieval = any(m in df.columns for m in retrieval_metrics)
    
    n_plots = sum([has_classification, has_clustering, has_regression, has_retrieval])
    
    if n_plots == 0:
        print("⚠️ No metrics found to plot")
        return
    
    # Create subplots
    if n_plots <= 2:
        rows, cols = 1, n_plots
    elif n_plots <= 4:
        rows, cols = 2, 2
    else:
        rows, cols = 2, 3
    
    fig, axes = plt.subplots(rows, cols, figsize=figsize)
    if n_plots == 1:
        axes = [axes]
    else:
        axes = axes.flatten()
    
    plot_idx = 0
    
    # Plot 1: Classification Metrics
    if has_classification:
        df_class = df[[m for m in classification_metrics if m in df.columns]].dropna(axis=1, how='all')
        if not df_class.empty:
            df_class.plot(kind='bar', ax=axes[plot_idx], rot=45)
            axes[plot_idx].set_title('Classification Metrics', fontsize=12, fontweight='bold')
            axes[plot_idx].set_ylabel('Score')
            axes[plot_idx].legend(loc='best')
            axes[plot_idx].grid(axis='y', alpha=0.3)
            axes[plot_idx].set_ylim([0, 1.1])
            plot_idx += 1
    
    # Plot 2: Clustering Metrics
    if has_clustering:
        clustering_cols = [m for m in clustering_metrics if m in df.columns]
        if clustering_cols:
            df_cluster = df[clustering_cols].dropna(axis=1, how='all')
            if not df_cluster.empty:
                df_cluster.plot(kind='bar', ax=axes[plot_idx], rot=45)
                axes[plot_idx].set_title('Clustering Metrics', fontsize=12, fontweight='bold')
                axes[plot_idx].set_ylabel('Score')
                axes[plot_idx].legend(loc='best')
                axes[plot_idx].grid(axis='y', alpha=0.3)
                plot_idx += 1
    
    # Plot 3: Regression Metrics
    if has_regression:
        regression_cols = [m for m in regression_metrics if m in df.columns]
        if regression_cols:
            df_reg = df[regression_cols].dropna(axis=1, how='all')
            if not df_reg.empty:
                df_reg.plot(kind='bar', ax=axes[plot_idx], rot=45)
                axes[plot_idx].set_title('Regression Metrics', fontsize=12, fontweight='bold')
                axes[plot_idx].set_ylabel('Score')
                axes[plot_idx].legend(loc='best')
                axes[plot_idx].grid(axis='y', alpha=0.3)
                plot_idx += 1
    
    # Plot 4: Retrieval Metrics
    if has_retrieval:
        retrieval_cols = [m for m in retrieval_metrics if m in df.columns]
        if retrieval_cols:
            df_ret = df[retrieval_cols].dropna(axis=1, how='all')
            if not df_ret.empty:
                df_ret.plot(kind='bar', ax=axes[plot_idx], rot=45)
                axes[plot_idx].set_title('Retrieval Metrics', fontsize=12, fontweight='bold')
                axes[plot_idx].set_ylabel('Score')
                axes[plot_idx].legend(loc='best')
                axes[plot_idx].grid(axis='y', alpha=0.3)
                plot_idx += 1
    
    # Hide unused subplots
    for idx in range(plot_idx, len(axes)):
        axes[idx].axis('off')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Metrics comparison saved to: {save_path}")
    else:
        plt.show()

