"""
ML Service - Orchestrates all ML operations for PredictrAI.

Provides a unified interface for:
- Model training and inference
- Batch and real-time prediction
- Multi-tenant model management
- MLflow integration
"""
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import pandas as pd
import numpy as np
import json
import logging

from ml.models.anomaly_detector import AnomalyDetector, StreamingAnomalyDetector
from ml.models.rul_forecaster import RULForecaster
from ml.models.log_analyzer import LogAnalyzer

try:
    import mlflow
    HAS_MLFLOW = True
except ImportError:
    HAS_MLFLOW = False

logger = logging.getLogger(__name__)


class MLService:
    """
    Central ML service for PredictrAI.
    
    Manages:
    - Per-tenant model storage
    - Training pipelines
    - Inference endpoints
    - Model versioning
    """
    
    def __init__(
        self,
        models_dir: str = "./models",
        mlflow_tracking_uri: Optional[str] = None,
    ):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # MLflow setup
        if HAS_MLFLOW and mlflow_tracking_uri:
            mlflow.set_tracking_uri(mlflow_tracking_uri)
        
        # Model caches (tenant_id -> model)
        self._anomaly_detectors: Dict[str, AnomalyDetector] = {}
        self._streaming_detectors: Dict[str, StreamingAnomalyDetector] = {}
        self._rul_forecasters: Dict[str, RULForecaster] = {}
        self._log_analyzers: Dict[str, LogAnalyzer] = {}
    
    def _get_tenant_dir(self, tenant_id: str) -> Path:
        """Get or create tenant model directory."""
        tenant_dir = self.models_dir / tenant_id
        tenant_dir.mkdir(parents=True, exist_ok=True)
        return tenant_dir
    
    # ==================== Anomaly Detection ====================
    
    def train_anomaly_detector(
        self,
        tenant_id: str,
        data: pd.DataFrame,
        feature_columns: List[str],
        contamination: float = 0.1,
        version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Train anomaly detector for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            data: Training data
            feature_columns: Columns to use as features
            contamination: Expected proportion of anomalies
            version: Model version string
        
        Returns:
            Training results and metrics
        """
        version = version or datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        logger.info(f"Training anomaly detector for tenant {tenant_id}")
        
        # Prepare data
        X = data[feature_columns]
        
        # Create and train model
        detector = AnomalyDetector(
            contamination=contamination,
            model_version=version,
        )
        detector.fit(X, feature_names=feature_columns)
        
        # Save model
        tenant_dir = self._get_tenant_dir(tenant_id)
        model_path = tenant_dir / f"anomaly_detector_{version}.joblib"
        detector.save(str(model_path))
        
        # Also save as latest
        latest_path = tenant_dir / "anomaly_detector_latest.joblib"
        detector.save(str(latest_path))
        
        # Cache
        self._anomaly_detectors[tenant_id] = detector
        
        # Log to MLflow
        if HAS_MLFLOW:
            with mlflow.start_run(run_name=f"anomaly_detector_{tenant_id}"):
                mlflow.log_params({
                    "tenant_id": tenant_id,
                    "contamination": contamination,
                    "n_features": len(feature_columns),
                    "n_samples": len(data),
                })
                mlflow.log_metrics({
                    "training_samples": len(data),
                })
                mlflow.log_artifact(str(model_path))
        
        return {
            "status": "success",
            "tenant_id": tenant_id,
            "model_version": version,
            "training_stats": detector.training_stats,
            "model_path": str(model_path),
        }
    
    def predict_anomalies(
        self,
        tenant_id: str,
        data: pd.DataFrame,
        with_explanation: bool = True,
    ) -> Dict[str, Any]:
        """
        Predict anomalies for tenant data.
        
        Args:
            tenant_id: Tenant identifier
            data: Data to predict on
            with_explanation: Include SHAP explanations
        
        Returns:
            Predictions with scores and explanations
        """
        detector = self._get_anomaly_detector(tenant_id)
        
        if detector is None:
            return {
                "status": "error",
                "message": f"No anomaly detector found for tenant {tenant_id}",
            }
        
        if with_explanation:
            return detector.predict_with_explanation(data)
        else:
            return detector.predict(data)
    
    def _get_anomaly_detector(self, tenant_id: str) -> Optional[AnomalyDetector]:
        """Get cached or load anomaly detector."""
        if tenant_id in self._anomaly_detectors:
            return self._anomaly_detectors[tenant_id]
        
        # Try to load from disk
        tenant_dir = self._get_tenant_dir(tenant_id)
        latest_path = tenant_dir / "anomaly_detector_latest.joblib"
        
        if latest_path.exists():
            detector = AnomalyDetector.load(str(latest_path))
            self._anomaly_detectors[tenant_id] = detector
            return detector
        
        return None
    
    # ==================== RUL Forecasting ====================
    
    def train_rul_forecaster(
        self,
        tenant_id: str,
        data: pd.DataFrame,
        feature_columns: List[str],
        rul_column: str = "RUL",
        sequence_length: int = 50,
        epochs: int = 50,
        version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Train RUL forecaster for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            data: Training data with features and RUL
            feature_columns: Feature columns
            rul_column: Target RUL column
            sequence_length: Sequence length for LSTM
            epochs: Training epochs
            version: Model version
        
        Returns:
            Training results
        """
        version = version or datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        logger.info(f"Training RUL forecaster for tenant {tenant_id}")
        
        # Prepare data
        train_df = data[feature_columns + [rul_column]]
        
        # Create and train model
        forecaster = RULForecaster(
            sequence_length=sequence_length,
            model_version=version,
        )
        forecaster.fit(train_df, rul_column=rul_column, epochs=epochs, verbose=True)
        
        # Save model
        tenant_dir = self._get_tenant_dir(tenant_id)
        model_path = tenant_dir / f"rul_forecaster_{version}.pt"
        forecaster.save(str(model_path))
        
        # Also save as latest
        latest_path = tenant_dir / "rul_forecaster_latest.pt"
        forecaster.save(str(latest_path))
        
        # Cache
        self._rul_forecasters[tenant_id] = forecaster
        
        # Log to MLflow
        if HAS_MLFLOW:
            with mlflow.start_run(run_name=f"rul_forecaster_{tenant_id}"):
                mlflow.log_params({
                    "tenant_id": tenant_id,
                    "sequence_length": sequence_length,
                    "epochs": epochs,
                    "n_features": len(feature_columns),
                })
                mlflow.log_metrics({
                    "final_train_loss": forecaster.training_stats.get("final_train_loss", 0),
                    "final_val_loss": forecaster.training_stats.get("final_val_loss", 0),
                })
                mlflow.log_artifact(str(model_path))
        
        return {
            "status": "success",
            "tenant_id": tenant_id,
            "model_version": version,
            "training_stats": forecaster.training_stats,
            "model_path": str(model_path),
        }
    
    def predict_rul(
        self,
        tenant_id: str,
        sequences: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Predict RUL for sequences.
        
        Args:
            tenant_id: Tenant identifier
            sequences: Shape (n_samples, sequence_length, n_features)
        
        Returns:
            RUL predictions with confidence intervals
        """
        forecaster = self._get_rul_forecaster(tenant_id)
        
        if forecaster is None:
            return {
                "status": "error",
                "message": f"No RUL forecaster found for tenant {tenant_id}",
            }
        
        return forecaster.predict(sequences, return_confidence=True)
    
    def _get_rul_forecaster(self, tenant_id: str) -> Optional[RULForecaster]:
        """Get cached or load RUL forecaster."""
        if tenant_id in self._rul_forecasters:
            return self._rul_forecasters[tenant_id]
        
        tenant_dir = self._get_tenant_dir(tenant_id)
        latest_path = tenant_dir / "rul_forecaster_latest.pt"
        
        if latest_path.exists():
            forecaster = RULForecaster.load(str(latest_path))
            self._rul_forecasters[tenant_id] = forecaster
            return forecaster
        
        return None
    
    # ==================== Log Analysis ====================
    
    def train_log_analyzer(
        self,
        tenant_id: str,
        logs: List[str],
        min_cluster_size: int = 5,
        version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Train log analyzer for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            logs: List of log messages
            min_cluster_size: Minimum cluster size
            version: Model version
        
        Returns:
            Training results with cluster information
        """
        version = version or datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        logger.info(f"Training log analyzer for tenant {tenant_id}")
        
        # Create and train analyzer
        analyzer = LogAnalyzer(
            min_cluster_size=min_cluster_size,
            model_version=version,
        )
        analyzer.fit(logs)
        
        # Save model
        tenant_dir = self._get_tenant_dir(tenant_id)
        model_path = tenant_dir / f"log_analyzer_{version}.joblib"
        analyzer.save(str(model_path))
        
        # Also save as latest
        latest_path = tenant_dir / "log_analyzer_latest.joblib"
        analyzer.save(str(latest_path))
        
        # Cache
        self._log_analyzers[tenant_id] = analyzer
        
        return {
            "status": "success",
            "tenant_id": tenant_id,
            "model_version": version,
            "num_clusters": len(analyzer.cluster_representatives),
            "clusters": analyzer.get_clusters(),
            "model_path": str(model_path),
        }
    
    def analyze_logs(
        self,
        tenant_id: str,
        logs: List[str],
    ) -> Dict[str, Any]:
        """
        Analyze logs for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            logs: Logs to analyze
        
        Returns:
            Analysis results
        """
        analyzer = self._get_log_analyzer(tenant_id)
        
        if analyzer is None:
            # Train on the fly if no existing model
            result = self.train_log_analyzer(tenant_id, logs)
            analyzer = self._log_analyzers.get(tenant_id)
        
        if analyzer is None:
            return {
                "status": "error",
                "message": f"Could not create log analyzer for tenant {tenant_id}",
            }
        
        return analyzer.analyze_batch(logs)
    
    def _get_log_analyzer(self, tenant_id: str) -> Optional[LogAnalyzer]:
        """Get cached or load log analyzer."""
        if tenant_id in self._log_analyzers:
            return self._log_analyzers[tenant_id]
        
        tenant_dir = self._get_tenant_dir(tenant_id)
        latest_path = tenant_dir / "log_analyzer_latest.joblib"
        
        if latest_path.exists():
            analyzer = LogAnalyzer.load(str(latest_path))
            self._log_analyzers[tenant_id] = analyzer
            return analyzer
        
        return None
    
    # ==================== Unified Prediction ====================
    
    def predict_asset_health(
        self,
        tenant_id: str,
        asset_id: str,
        metrics: pd.DataFrame,
        logs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Unified health prediction for an asset.
        
        Combines:
        - Anomaly detection
        - RUL forecasting
        - Log analysis
        
        Args:
            tenant_id: Tenant identifier
            asset_id: Asset identifier
            metrics: Recent metrics for the asset
            logs: Recent logs for the asset
        
        Returns:
            Comprehensive health assessment
        """
        result = {
            "tenant_id": tenant_id,
            "asset_id": asset_id,
            "timestamp": datetime.utcnow().isoformat(),
            "anomaly": None,
            "rul": None,
            "logs": None,
            "overall_risk": "normal",
        }
        
        # Anomaly detection
        try:
            anomaly_result = self.predict_anomalies(tenant_id, metrics, with_explanation=True)
            if "error" not in anomaly_result.get("status", ""):
                result["anomaly"] = {
                    "score": anomaly_result.get("anomaly_scores", [0])[0],
                    "risk_level": anomaly_result.get("risk_levels", ["normal"])[0],
                    "top_features": anomaly_result.get("explanations", [{}])[0].get("top_features", []),
                }
        except Exception as e:
            logger.warning(f"Anomaly detection failed: {e}")
        
        # RUL forecasting
        try:
            forecaster = self._get_rul_forecaster(tenant_id)
            if forecaster and len(metrics) >= forecaster.sequence_length:
                rul_result = forecaster.predict_single(metrics)
                if "error" not in rul_result:
                    result["rul"] = {
                        "estimate": rul_result.get("rul_estimate", [None])[0],
                        "confidence_lower": rul_result.get("confidence_lower", [None])[0],
                        "confidence_upper": rul_result.get("confidence_upper", [None])[0],
                    }
        except Exception as e:
            logger.warning(f"RUL prediction failed: {e}")
        
        # Log analysis
        if logs:
            try:
                log_result = self.analyze_logs(tenant_id, logs)
                if "error" not in log_result.get("status", ""):
                    result["logs"] = {
                        "num_clusters": log_result.get("num_clusters", 0),
                        "top_patterns": log_result.get("clusters", [])[:3],
                    }
            except Exception as e:
                logger.warning(f"Log analysis failed: {e}")
        
        # Determine overall risk
        risks = []
        if result["anomaly"]:
            risks.append(result["anomaly"]["risk_level"])
        if result["rul"] and result["rul"]["estimate"]:
            if result["rul"]["estimate"] < 10:
                risks.append("critical")
            elif result["rul"]["estimate"] < 50:
                risks.append("warning")
        
        if "critical" in risks:
            result["overall_risk"] = "critical"
        elif "warning" in risks:
            result["overall_risk"] = "warning"
        else:
            result["overall_risk"] = "normal"
        
        return result
