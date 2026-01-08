"""
Drift Detection - Monitor data and model drift.

Uses Evidently for:
- Data drift detection
- Concept drift monitoring
- Retraining triggers
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
import logging

try:
    from evidently.report import Report
    from evidently.metric_preset import DataDriftPreset, TargetDriftPreset
    from evidently.metrics import DataDriftTable, DatasetDriftMetric
    HAS_EVIDENTLY = True
except ImportError:
    HAS_EVIDENTLY = False

logger = logging.getLogger(__name__)


class DriftDetector:
    """
    Production drift detector using Evidently.
    
    Monitors:
    - Feature distribution drift
    - Prediction drift
    - Model performance degradation
    """
    
    def __init__(
        self,
        drift_threshold: float = 0.5,
        feature_drift_threshold: float = 0.3,
    ):
        self.drift_threshold = drift_threshold
        self.feature_drift_threshold = feature_drift_threshold
        
        if not HAS_EVIDENTLY:
            logger.warning("Evidently not available. Drift detection will use fallback.")
    
    def detect_data_drift(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Detect data drift between reference and current data.
        
        Args:
            reference_data: Training/reference data
            current_data: Current production data
        
        Returns:
            Drift detection results
        """
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "drift_detected": False,
            "overall_drift_score": 0.0,
            "drifted_features": [],
        }
        
        if HAS_EVIDENTLY:
            return self._detect_with_evidently(reference_data, current_data)
        else:
            return self._detect_fallback(reference_data, current_data)
    
    def _detect_with_evidently(
        self,
        reference: pd.DataFrame,
        current: pd.DataFrame,
    ) -> Dict[str, Any]:
        """Detect drift using Evidently."""
        try:
            report = Report(metrics=[DatasetDriftMetric()])
            report.run(reference_data=reference, current_data=current)
            
            result_dict = report.as_dict()
            
            drift_metrics = result_dict.get("metrics", [{}])[0].get("result", {})
            
            # Parse results
            drift_detected = drift_metrics.get("dataset_drift", False)
            drift_share = drift_metrics.get("drift_share", 0)
            
            drifted_features = []
            column_drifts = drift_metrics.get("drift_by_columns", {})
            for col, info in column_drifts.items():
                if info.get("drift_detected", False):
                    drifted_features.append({
                        "feature": col,
                        "drift_score": info.get("drift_score", 0),
                        "stattest": info.get("stattest_name", "unknown"),
                    })
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "drift_detected": drift_detected,
                "overall_drift_score": drift_share,
                "drifted_features": drifted_features,
                "method": "evidently",
            }
        except Exception as e:
            logger.error(f"Evidently drift detection failed: {e}")
            return self._detect_fallback(reference, current)
    
    def _detect_fallback(
        self,
        reference: pd.DataFrame,
        current: pd.DataFrame,
    ) -> Dict[str, Any]:
        """Simple statistical drift detection fallback."""
        drifted_features = []
        drift_scores = []
        
        common_cols = list(set(reference.columns) & set(current.columns))
        
        for col in common_cols:
            if reference[col].dtype not in [np.number, 'float64', 'int64']:
                continue
            
            ref_mean = reference[col].mean()
            ref_std = reference[col].std()
            curr_mean = current[col].mean()
            
            if ref_std > 0:
                # Z-score of mean shift
                z_score = abs(curr_mean - ref_mean) / ref_std
                drift_score = min(1.0, z_score / 3)  # Normalize to 0-1
                
                drift_scores.append(drift_score)
                
                if drift_score > self.feature_drift_threshold:
                    drifted_features.append({
                        "feature": col,
                        "drift_score": drift_score,
                        "reference_mean": ref_mean,
                        "current_mean": curr_mean,
                    })
        
        overall_drift = np.mean(drift_scores) if drift_scores else 0.0
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "drift_detected": overall_drift > self.drift_threshold or len(drifted_features) >= 2,
            "overall_drift_score": overall_drift,
            "drifted_features": drifted_features,
            "method": "statistical",
        }
    
    def should_retrain(
        self,
        drift_result: Dict[str, Any],
        min_drifted_features: int = 2,
    ) -> bool:
        """
        Determine if model should be retrained based on drift.
        
        Args:
            drift_result: Result from detect_data_drift
            min_drifted_features: Minimum drifted features to trigger retrain
        
        Returns:
            True if retraining is recommended
        """
        if drift_result.get("drift_detected"):
            return True
        
        if len(drift_result.get("drifted_features", [])) >= min_drifted_features:
            return True
        
        if drift_result.get("overall_drift_score", 0) > self.drift_threshold:
            return True
        
        return False


class DriftMonitor:
    """
    Continuous drift monitoring service.
    
    Features:
    - Periodic drift checks
    - Alert generation
    - Retraining recommendations
    """
    
    def __init__(
        self,
        detector: DriftDetector,
        reference_window_days: int = 7,
    ):
        self.detector = detector
        self.reference_window_days = reference_window_days
        self.reference_data: Dict[str, pd.DataFrame] = {}  # tenant_id -> data
    
    def set_reference(self, tenant_id: str, data: pd.DataFrame):
        """Set reference data for a tenant."""
        self.reference_data[tenant_id] = data.copy()
    
    def check_drift(
        self,
        tenant_id: str,
        current_data: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Check drift for a tenant against reference.
        
        Args:
            tenant_id: Tenant identifier
            current_data: Current production data
        
        Returns:
            Drift check results
        """
        reference = self.reference_data.get(tenant_id)
        
        if reference is None:
            return {
                "status": "no_reference",
                "message": "No reference data set for this tenant",
            }
        
        drift_result = self.detector.detect_data_drift(reference, current_data)
        drift_result["tenant_id"] = tenant_id
        drift_result["should_retrain"] = self.detector.should_retrain(drift_result)
        
        return drift_result
