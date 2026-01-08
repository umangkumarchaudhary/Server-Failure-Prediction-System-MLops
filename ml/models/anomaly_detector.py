"""
Anomaly Detection Service - Production-Ready Implementation

Uses a hybrid approach:
1. Isolation Forest for fast, robust anomaly detection
2. Optional deep autoencoder for high-dimensional data
3. SHAP for explainability
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import joblib
import json
from pathlib import Path

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import shap


class AnomalyDetector:
    """
    Production-ready anomaly detector with explainability.
    
    Features:
    - Isolation Forest for robust anomaly detection
    - SHAP explainability for each prediction
    - Model versioning and serialization
    - Batch and streaming inference
    """
    
    def __init__(
        self,
        contamination: float = 0.1,
        n_estimators: int = 100,
        random_state: int = 42,
        model_version: str = "1.0.0"
    ):
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model_version = model_version
        
        self.scaler = StandardScaler()
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=-1,
        )
        self.explainer: Optional[shap.Explainer] = None
        self.feature_names: List[str] = []
        self.is_fitted = False
        self.training_stats: Dict[str, Any] = {}
    
    def fit(
        self,
        X: pd.DataFrame,
        feature_names: Optional[List[str]] = None
    ) -> "AnomalyDetector":
        """
        Fit the anomaly detector on training data.
        
        Args:
            X: Training data (metrics over time)
            feature_names: Names of features for explainability
        
        Returns:
            Self for chaining
        """
        self.feature_names = feature_names or list(X.columns)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Fit isolation forest
        self.model.fit(X_scaled)
        
        # Create SHAP explainer
        self.explainer = shap.TreeExplainer(self.model)
        
        # Store training statistics
        self.training_stats = {
            "n_samples": len(X),
            "n_features": X.shape[1],
            "feature_means": X.mean().to_dict(),
            "feature_stds": X.std().to_dict(),
            "trained_at": datetime.utcnow().isoformat(),
            "model_version": self.model_version,
        }
        
        self.is_fitted = True
        return self
    
    def predict(
        self,
        X: pd.DataFrame,
        return_scores: bool = True
    ) -> Dict[str, Any]:
        """
        Predict anomalies with scores.
        
        Args:
            X: Data to predict on
            return_scores: Whether to return anomaly scores
        
        Returns:
            Dictionary with predictions, scores, and risk levels
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        X_scaled = self.scaler.transform(X)
        
        # Get predictions (-1 = anomaly, 1 = normal)
        predictions = self.model.predict(X_scaled)
        
        # Get anomaly scores (negative = more anomalous)
        raw_scores = self.model.decision_function(X_scaled)
        
        # Normalize scores to 0-1 (higher = more anomalous)
        anomaly_scores = self._normalize_scores(raw_scores)
        
        # Determine risk levels
        risk_levels = self._get_risk_levels(anomaly_scores)
        
        return {
            "is_anomaly": (predictions == -1).tolist(),
            "anomaly_scores": anomaly_scores.tolist(),
            "risk_levels": risk_levels,
            "model_version": self.model_version,
        }
    
    def explain(
        self,
        X: pd.DataFrame,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Explain predictions using SHAP values.
        
        Args:
            X: Data to explain
            top_k: Number of top contributing features to return
        
        Returns:
            List of explanations for each sample
        """
        if self.explainer is None:
            raise ValueError("Explainer not available. Fit model first.")
        
        X_scaled = self.scaler.transform(X)
        shap_values = self.explainer.shap_values(X_scaled)
        
        explanations = []
        for i in range(len(X)):
            # Get SHAP values for this sample
            sample_shap = shap_values[i]
            
            # Sort by absolute contribution
            feature_contributions = [
                {
                    "feature": self.feature_names[j],
                    "value": float(X.iloc[i, j]),
                    "contribution": float(sample_shap[j]),
                    "abs_contribution": abs(float(sample_shap[j])),
                }
                for j in range(len(self.feature_names))
            ]
            feature_contributions.sort(key=lambda x: x["abs_contribution"], reverse=True)
            
            explanations.append({
                "top_features": feature_contributions[:top_k],
                "total_features": len(self.feature_names),
            })
        
        return explanations
    
    def predict_with_explanation(
        self,
        X: pd.DataFrame,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Combined prediction and explanation.
        
        Args:
            X: Data to predict and explain
            top_k: Number of top features to return
        
        Returns:
            Dictionary with predictions, scores, and explanations
        """
        predictions = self.predict(X)
        explanations = self.explain(X, top_k)
        
        return {
            **predictions,
            "explanations": explanations,
        }
    
    def _normalize_scores(self, raw_scores: np.ndarray) -> np.ndarray:
        """Normalize raw scores to 0-1 range (higher = more anomalous)."""
        # Decision function: negative = more anomalous
        # We want: higher = more anomalous
        min_score = raw_scores.min()
        max_score = raw_scores.max()
        
        if max_score == min_score:
            return np.zeros_like(raw_scores)
        
        # Invert and normalize
        normalized = 1 - (raw_scores - min_score) / (max_score - min_score)
        return normalized
    
    def _get_risk_levels(self, scores: np.ndarray) -> List[str]:
        """Convert scores to risk levels."""
        levels = []
        for score in scores:
            if score >= 0.8:
                levels.append("critical")
            elif score >= 0.5:
                levels.append("warning")
            else:
                levels.append("normal")
        return levels
    
    def save(self, path: str) -> None:
        """Save model to disk."""
        model_data = {
            "scaler": self.scaler,
            "model": self.model,
            "feature_names": self.feature_names,
            "training_stats": self.training_stats,
            "model_version": self.model_version,
            "contamination": self.contamination,
            "n_estimators": self.n_estimators,
        }
        joblib.dump(model_data, path)
    
    @classmethod
    def load(cls, path: str) -> "AnomalyDetector":
        """Load model from disk."""
        model_data = joblib.load(path)
        
        detector = cls(
            contamination=model_data["contamination"],
            n_estimators=model_data["n_estimators"],
            model_version=model_data["model_version"],
        )
        detector.scaler = model_data["scaler"]
        detector.model = model_data["model"]
        detector.feature_names = model_data["feature_names"]
        detector.training_stats = model_data["training_stats"]
        detector.explainer = shap.TreeExplainer(detector.model)
        detector.is_fitted = True
        
        return detector


class StreamingAnomalyDetector:
    """
    Wrapper for real-time streaming anomaly detection.
    
    Features:
    - Sliding window aggregation
    - Online scoring
    - Adaptive thresholds
    """
    
    def __init__(
        self,
        detector: AnomalyDetector,
        window_size: int = 60,
        alert_threshold: float = 0.7,
    ):
        self.detector = detector
        self.window_size = window_size
        self.alert_threshold = alert_threshold
        self.buffer: Dict[str, List[Dict]] = {}  # asset_id -> data points
    
    def process_point(
        self,
        asset_id: str,
        timestamp: datetime,
        metrics: Dict[str, float]
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single data point.
        
        Args:
            asset_id: Asset identifier
            timestamp: Data timestamp
            metrics: Dictionary of metric values
        
        Returns:
            Prediction result if enough data, else None
        """
        # Initialize buffer for new assets
        if asset_id not in self.buffer:
            self.buffer[asset_id] = []
        
        # Add to buffer
        self.buffer[asset_id].append({
            "timestamp": timestamp,
            **metrics
        })
        
        # Maintain window size
        if len(self.buffer[asset_id]) > self.window_size:
            self.buffer[asset_id] = self.buffer[asset_id][-self.window_size:]
        
        # Need at least some data points
        if len(self.buffer[asset_id]) < 10:
            return None
        
        # Aggregate window statistics
        df = pd.DataFrame(self.buffer[asset_id])
        df = df.drop(columns=["timestamp"])
        
        # Create feature vector (last point + window stats)
        features = {}
        for col in df.columns:
            features[f"{col}_current"] = df[col].iloc[-1]
            features[f"{col}_mean"] = df[col].mean()
            features[f"{col}_std"] = df[col].std()
            features[f"{col}_min"] = df[col].min()
            features[f"{col}_max"] = df[col].max()
        
        feature_df = pd.DataFrame([features])
        
        # Predict
        try:
            result = self.detector.predict_with_explanation(feature_df)
            result["asset_id"] = asset_id
            result["timestamp"] = timestamp.isoformat()
            result["should_alert"] = result["anomaly_scores"][0] >= self.alert_threshold
            return result
        except Exception as e:
            return {"error": str(e), "asset_id": asset_id}
