"""
Inference Pipeline - Real-time prediction service.

Handles:
- Streaming inference
- Batch prediction
- Result persistence
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
import logging

from ml.services.ml_service import MLService

logger = logging.getLogger(__name__)


class InferencePipeline:
    """
    Real-time inference pipeline.
    
    Features:
    - Asset-level prediction
    - Automatic alert generation
    - Result caching
    """
    
    def __init__(
        self,
        ml_service: MLService,
        alert_threshold: float = 0.7,
        rul_critical_threshold: float = 24.0,  # hours
    ):
        self.ml_service = ml_service
        self.alert_threshold = alert_threshold
        self.rul_critical_threshold = rul_critical_threshold
    
    async def process_metrics_batch(
        self,
        tenant_id: str,
        asset_id: str,
        metrics: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Process a batch of metrics and generate predictions.
        
        Args:
            tenant_id: Tenant identifier
            asset_id: Asset identifier
            metrics: DataFrame of metric values
        
        Returns:
            Prediction results with alerts
        """
        result = {
            "tenant_id": tenant_id,
            "asset_id": asset_id,
            "timestamp": datetime.utcnow().isoformat(),
            "predictions": [],
            "alerts": [],
        }
        
        # Anomaly detection
        try:
            prediction = self.ml_service.predict_anomalies(
                tenant_id=tenant_id,
                data=metrics,
                with_explanation=True,
            )
            
            if "anomaly_scores" in prediction:
                score = prediction["anomaly_scores"][-1]
                risk = prediction["risk_levels"][-1]
                
                pred_record = {
                    "type": "anomaly",
                    "anomaly_score": score,
                    "risk_level": risk,
                    "model_version": prediction.get("model_version"),
                }
                
                if "explanations" in prediction:
                    pred_record["explanation"] = prediction["explanations"][-1]
                
                result["predictions"].append(pred_record)
                
                # Generate alert if score exceeds threshold
                if score >= self.alert_threshold:
                    result["alerts"].append({
                        "type": "anomaly",
                        "severity": risk,
                        "message": f"High anomaly score detected: {score:.2f}",
                        "asset_id": asset_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "top_features": pred_record.get("explanation", {}).get("top_features", [])[:3],
                    })
        except Exception as e:
            logger.warning(f"Anomaly prediction failed: {e}")
        
        # RUL prediction
        try:
            rul_result = self.ml_service.predict_rul(tenant_id, metrics.values.reshape(1, -1, metrics.shape[1]))
            
            if "rul_estimate" in rul_result:
                rul = rul_result["rul_estimate"][0]
                
                pred_record = {
                    "type": "rul",
                    "rul_estimate": rul,
                    "confidence_lower": rul_result.get("confidence_lower", [None])[0],
                    "confidence_upper": rul_result.get("confidence_upper", [None])[0],
                    "model_version": rul_result.get("model_version"),
                }
                result["predictions"].append(pred_record)
                
                # Alert for critical RUL
                if rul and rul < self.rul_critical_threshold:
                    result["alerts"].append({
                        "type": "rul",
                        "severity": "critical" if rul < 10 else "warning",
                        "message": f"Low remaining useful life: {rul:.1f} hours",
                        "asset_id": asset_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "rul_estimate": rul,
                    })
        except Exception as e:
            logger.warning(f"RUL prediction failed: {e}")
        
        return result
    
    def generate_explanation(
        self,
        prediction: Dict[str, Any],
    ) -> str:
        """
        Generate human-readable explanation for a prediction.
        
        Args:
            prediction: Prediction result
        
        Returns:
            Natural language explanation
        """
        explanations = []
        
        if prediction.get("anomaly"):
            anomaly = prediction["anomaly"]
            score = anomaly.get("score", 0)
            risk = anomaly.get("risk_level", "normal")
            
            if risk == "critical":
                explanations.append(f"⚠️ Critical anomaly detected (score: {score:.2f})")
            elif risk == "warning":
                explanations.append(f"⚡ Warning: Elevated anomaly score ({score:.2f})")
            
            top_features = anomaly.get("top_features", [])[:3]
            if top_features:
                feature_desc = ", ".join([f"{f['feature']}" for f in top_features])
                explanations.append(f"Key contributing factors: {feature_desc}")
        
        if prediction.get("rul"):
            rul = prediction["rul"].get("estimate")
            if rul:
                if rul < 10:
                    explanations.append(f"🔴 Critical: Only {rul:.0f} hours of useful life remaining")
                elif rul < 50:
                    explanations.append(f"🟡 Warning: {rul:.0f} hours of useful life remaining")
                else:
                    explanations.append(f"🟢 Asset health: ~{rul:.0f} hours remaining")
        
        return " | ".join(explanations) if explanations else "No issues detected"
