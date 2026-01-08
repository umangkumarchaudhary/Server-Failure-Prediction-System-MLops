"""
Log Analyzer - Production-Ready NLP Implementation

Uses transformer embeddings + clustering for:
1. Log message clustering (error pattern detection)
2. Root cause phrase extraction
3. Anomaly correlation
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from collections import Counter
import re
import json
from pathlib import Path

from sklearn.cluster import HDBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import joblib

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


class LogPreprocessor:
    """Preprocessor for log messages."""
    
    # Common patterns to normalize
    PATTERNS = [
        (r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[.\d]*[Z]?', '<TIMESTAMP>'),
        (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '<IP>'),
        (r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b', '<UUID>'),
        (r'\b[0-9a-fA-F]{24,}\b', '<HEX>'),
        (r'\b\d+\b', '<NUM>'),
        (r'\/[^\s]+', '<PATH>'),
        (r'http[s]?://[^\s]+', '<URL>'),
        (r'\S+@\S+', '<EMAIL>'),
    ]
    
    @classmethod
    def preprocess(cls, text: str) -> str:
        """Normalize log message for clustering."""
        result = text.lower().strip()
        
        for pattern, replacement in cls.PATTERNS:
            result = re.sub(pattern, replacement, result)
        
        # Remove multiple spaces
        result = re.sub(r'\s+', ' ', result)
        
        return result
    
    @classmethod
    def extract_error_keywords(cls, text: str) -> List[str]:
        """Extract error-related keywords from log."""
        error_patterns = [
            r'error[:\s]+(\w+)',
            r'exception[:\s]+(\w+)',
            r'failed[:\s]+(\w+)',
            r'failure[:\s]+(\w+)',
            r'critical[:\s]+(\w+)',
            r'fatal[:\s]+(\w+)',
        ]
        
        keywords = []
        text_lower = text.lower()
        
        for pattern in error_patterns:
            matches = re.findall(pattern, text_lower)
            keywords.extend(matches)
        
        return keywords


class LogAnalyzer:
    """
    Production-ready log analyzer.
    
    Features:
    - Transformer-based embeddings (or TF-IDF fallback)
    - HDBSCAN clustering for automatic cluster discovery
    - Representative message extraction
    - Root cause phrase detection
    - Anomaly correlation
    """
    
    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        min_cluster_size: int = 5,
        min_samples: int = 3,
        use_tfidf_fallback: bool = True,
        model_version: str = "1.0.0",
    ):
        self.embedding_model_name = embedding_model
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.use_tfidf_fallback = use_tfidf_fallback
        self.model_version = model_version
        
        # Initialize embedding model
        if HAS_SENTENCE_TRANSFORMERS:
            self.embedding_model = SentenceTransformer(embedding_model)
            self.use_tfidf = False
        elif use_tfidf_fallback:
            self.embedding_model = None
            self.tfidf = TfidfVectorizer(max_features=1000, stop_words='english')
            self.use_tfidf = True
        else:
            raise ImportError("sentence-transformers not available and TF-IDF fallback disabled")
        
        self.clusterer = HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric='euclidean',
        )
        
        self.cluster_representatives: Dict[int, Dict] = {}
        self.embeddings_cache: Optional[np.ndarray] = None
        self.logs_cache: Optional[List[str]] = None
        self.is_fitted = False
    
    def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for texts."""
        if self.use_tfidf:
            return self.tfidf.fit_transform(texts).toarray()
        else:
            return self.embedding_model.encode(texts, show_progress_bar=False)
    
    def fit(self, logs: List[str]) -> "LogAnalyzer":
        """
        Fit the analyzer on log messages.
        
        Args:
            logs: List of raw log messages
        
        Returns:
            Self for chaining
        """
        # Preprocess
        processed = [LogPreprocessor.preprocess(log) for log in logs]
        
        # Get embeddings
        embeddings = self._get_embeddings(processed)
        
        # Cluster
        labels = self.clusterer.fit_predict(embeddings)
        
        # Extract cluster representatives
        self.cluster_representatives = {}
        unique_labels = set(labels)
        
        for label in unique_labels:
            if label == -1:  # Noise
                continue
            
            mask = labels == label
            cluster_logs = [logs[i] for i in range(len(logs)) if mask[i]]
            cluster_embeddings = embeddings[mask]
            
            # Find centroid
            centroid = cluster_embeddings.mean(axis=0)
            
            # Find most representative log (closest to centroid)
            distances = np.linalg.norm(cluster_embeddings - centroid, axis=1)
            representative_idx = np.argmin(distances)
            
            # Extract common keywords
            all_keywords = []
            for log in cluster_logs[:50]:  # Sample for performance
                all_keywords.extend(LogPreprocessor.extract_error_keywords(log))
            common_keywords = [kw for kw, _ in Counter(all_keywords).most_common(5)]
            
            self.cluster_representatives[label] = {
                "size": len(cluster_logs),
                "representative": cluster_logs[representative_idx],
                "keywords": common_keywords,
                "sample_logs": cluster_logs[:5],
            }
        
        self.embeddings_cache = embeddings
        self.logs_cache = logs
        self.labels_cache = labels
        self.is_fitted = True
        
        return self
    
    def get_clusters(self) -> Dict[int, Dict]:
        """Get all cluster information."""
        return self.cluster_representatives
    
    def predict(self, logs: List[str]) -> List[int]:
        """
        Predict cluster assignments for new logs.
        
        Args:
            logs: List of log messages
        
        Returns:
            List of cluster IDs (-1 for noise/new cluster)
        """
        if not self.is_fitted:
            raise ValueError("Analyzer not fitted. Call fit() first.")
        
        processed = [LogPreprocessor.preprocess(log) for log in logs]
        
        if self.use_tfidf:
            embeddings = self.tfidf.transform(processed).toarray()
        else:
            embeddings = self.embedding_model.encode(processed, show_progress_bar=False)
        
        # Approximate prediction using existing cluster centroids
        predictions = []
        for emb in embeddings:
            best_cluster = -1
            best_similarity = 0.3  # Threshold
            
            for label, info in self.cluster_representatives.items():
                # Get cluster centroid from cached data
                mask = self.labels_cache == label
                centroid = self.embeddings_cache[mask].mean(axis=0)
                
                similarity = cosine_similarity([emb], [centroid])[0, 0]
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_cluster = label
            
            predictions.append(best_cluster)
        
        return predictions
    
    def analyze_batch(
        self,
        logs: List[str],
        timestamps: Optional[List[datetime]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a batch of logs with full statistics.
        
        Args:
            logs: List of log messages
            timestamps: Optional timestamps for temporal analysis
        
        Returns:
            Comprehensive analysis results
        """
        if not logs:
            return {"error": "No logs provided"}
        
        # Fit if not already
        if not self.is_fitted:
            self.fit(logs)
        
        # Get predictions
        clusters = self.predict(logs)
        
        # Aggregate statistics
        cluster_counts = Counter(clusters)
        
        # Build response
        analysis = {
            "total_logs": len(logs),
            "num_clusters": len([c for c in cluster_counts if c != -1]),
            "noise_count": cluster_counts.get(-1, 0),
            "clusters": [],
        }
        
        for cluster_id, count in sorted(cluster_counts.items(), key=lambda x: -x[1]):
            if cluster_id == -1:
                continue
            
            cluster_info = self.cluster_representatives.get(cluster_id, {})
            analysis["clusters"].append({
                "cluster_id": cluster_id,
                "count": count,
                "percentage": round(count / len(logs) * 100, 2),
                "representative": cluster_info.get("representative", ""),
                "keywords": cluster_info.get("keywords", []),
            })
        
        return analysis
    
    def find_similar_logs(
        self,
        query_log: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find logs similar to a query log.
        
        Args:
            query_log: Log message to search for
            top_k: Number of results to return
        
        Returns:
            List of similar logs with similarity scores
        """
        if not self.is_fitted or self.logs_cache is None:
            raise ValueError("Analyzer not fitted. Call fit() first.")
        
        processed = LogPreprocessor.preprocess(query_log)
        
        if self.use_tfidf:
            query_embedding = self.tfidf.transform([processed]).toarray()[0]
        else:
            query_embedding = self.embedding_model.encode([processed])[0]
        
        # Compute similarities
        similarities = cosine_similarity([query_embedding], self.embeddings_cache)[0]
        
        # Get top-k
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                "log": self.logs_cache[idx],
                "similarity": float(similarities[idx]),
                "cluster_id": int(self.labels_cache[idx]),
            })
        
        return results
    
    def correlate_with_anomalies(
        self,
        logs: List[str],
        log_timestamps: List[datetime],
        anomaly_timestamps: List[datetime],
        window_minutes: int = 5,
    ) -> Dict[str, Any]:
        """
        Find log patterns that correlate with anomalies.
        
        Args:
            logs: Log messages
            log_timestamps: Timestamps for logs
            anomaly_timestamps: When anomalies occurred
            window_minutes: Time window to consider
        
        Returns:
            Correlated log patterns
        """
        from datetime import timedelta
        
        # Find logs near anomalies
        near_anomaly_logs = []
        
        for anomaly_time in anomaly_timestamps:
            window_start = anomaly_time - timedelta(minutes=window_minutes)
            window_end = anomaly_time + timedelta(minutes=window_minutes)
            
            for i, log_time in enumerate(log_timestamps):
                if window_start <= log_time <= window_end:
                    near_anomaly_logs.append(logs[i])
        
        if not near_anomaly_logs:
            return {"correlated_patterns": [], "message": "No logs found near anomalies"}
        
        # Cluster near-anomaly logs
        if len(near_anomaly_logs) >= self.min_cluster_size:
            mini_analyzer = LogAnalyzer(
                embedding_model=self.embedding_model_name,
                min_cluster_size=min(3, len(near_anomaly_logs) // 2),
                use_tfidf_fallback=self.use_tfidf_fallback,
            )
            mini_analyzer.fit(near_anomaly_logs)
            
            return {
                "correlated_patterns": list(mini_analyzer.cluster_representatives.values()),
                "total_near_anomaly_logs": len(near_anomaly_logs),
            }
        else:
            return {
                "correlated_patterns": [],
                "near_anomaly_logs": near_anomaly_logs[:10],
                "message": "Not enough logs for clustering",
            }
    
    def save(self, path: str) -> None:
        """Save analyzer to disk."""
        model_data = {
            "cluster_representatives": self.cluster_representatives,
            "embeddings_cache": self.embeddings_cache,
            "logs_cache": self.logs_cache,
            "labels_cache": self.labels_cache if hasattr(self, 'labels_cache') else None,
            "model_version": self.model_version,
            "min_cluster_size": self.min_cluster_size,
            "min_samples": self.min_samples,
            "use_tfidf": self.use_tfidf,
        }
        
        if self.use_tfidf:
            model_data["tfidf"] = self.tfidf
        
        joblib.dump(model_data, path)
    
    @classmethod
    def load(cls, path: str) -> "LogAnalyzer":
        """Load analyzer from disk."""
        model_data = joblib.load(path)
        
        analyzer = cls(
            min_cluster_size=model_data["min_cluster_size"],
            min_samples=model_data["min_samples"],
            use_tfidf_fallback=model_data["use_tfidf"],
            model_version=model_data["model_version"],
        )
        
        analyzer.cluster_representatives = model_data["cluster_representatives"]
        analyzer.embeddings_cache = model_data["embeddings_cache"]
        analyzer.logs_cache = model_data["logs_cache"]
        analyzer.labels_cache = model_data.get("labels_cache")
        
        if model_data["use_tfidf"]:
            analyzer.tfidf = model_data["tfidf"]
            analyzer.use_tfidf = True
        
        analyzer.is_fitted = True
        
        return analyzer
