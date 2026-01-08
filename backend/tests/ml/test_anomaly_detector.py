"""
Unit Tests for Anomaly Detection Model.
"""
import pytest
import numpy as np
import pandas as pd
import tempfile
import os

# Add parent to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ml.models.anomaly_detector import AnomalyDetector, StreamingAnomalyDetector


class TestAnomalyDetector:
    """Tests for AnomalyDetector class."""
    
    @pytest.mark.unit
    def test_initialization(self):
        """Test model initialization with default parameters."""
        detector = AnomalyDetector()
        
        assert detector.contamination == 0.1
        assert detector.n_estimators == 100
        assert detector.is_fitted == False
    
    @pytest.mark.unit
    def test_initialization_custom_params(self):
        """Test model initialization with custom parameters."""
        detector = AnomalyDetector(
            contamination=0.05,
            n_estimators=50,
            model_version="2.0.0"
        )
        
        assert detector.contamination == 0.05
        assert detector.n_estimators == 50
        assert detector.model_version == "2.0.0"
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_fit(self, sample_metrics_df):
        """Test model fitting."""
        detector = AnomalyDetector()
        detector.fit(sample_metrics_df)
        
        assert detector.is_fitted == True
        assert detector.feature_names == list(sample_metrics_df.columns)
        assert "n_samples" in detector.training_stats
        assert detector.training_stats["n_samples"] == len(sample_metrics_df)
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_predict(self, sample_metrics_df):
        """Test prediction output structure."""
        detector = AnomalyDetector()
        detector.fit(sample_metrics_df)
        
        result = detector.predict(sample_metrics_df.head(10))
        
        assert "is_anomaly" in result
        assert "anomaly_scores" in result
        assert "risk_levels" in result
        assert len(result["is_anomaly"]) == 10
        assert all(isinstance(x, bool) for x in result["is_anomaly"])
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_predict_detects_anomalies(self, sample_metrics_with_anomalies):
        """Test that detector identifies anomalies."""
        detector = AnomalyDetector(contamination=0.1)
        
        # Fit on normal data
        normal_data = sample_metrics_with_anomalies.head(400)
        detector.fit(normal_data)
        
        # Predict on data with anomalies
        anomaly_data = sample_metrics_with_anomalies.tail(50)
        result = detector.predict(anomaly_data)
        
        # Should detect some anomalies
        anomaly_count = sum(result["is_anomaly"])
        assert anomaly_count > 0, "Should detect at least some anomalies"
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_explain(self, sample_metrics_df):
        """Test SHAP explanation generation."""
        detector = AnomalyDetector()
        detector.fit(sample_metrics_df)
        
        explanations = detector.explain(sample_metrics_df.head(5), top_k=3)
        
        assert len(explanations) == 5
        assert "top_features" in explanations[0]
        assert len(explanations[0]["top_features"]) == 3
        assert "feature" in explanations[0]["top_features"][0]
        assert "contribution" in explanations[0]["top_features"][0]
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_predict_with_explanation(self, sample_metrics_df):
        """Test combined prediction and explanation."""
        detector = AnomalyDetector()
        detector.fit(sample_metrics_df)
        
        result = detector.predict_with_explanation(sample_metrics_df.head(5))
        
        assert "is_anomaly" in result
        assert "anomaly_scores" in result
        assert "explanations" in result
        assert len(result["explanations"]) == 5
    
    @pytest.mark.unit
    def test_predict_without_fit_raises(self):
        """Test that predicting without fitting raises error."""
        detector = AnomalyDetector()
        df = pd.DataFrame({"a": [1, 2, 3]})
        
        with pytest.raises(ValueError, match="not fitted"):
            detector.predict(df)
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_save_and_load(self, sample_metrics_df):
        """Test model serialization."""
        detector = AnomalyDetector(model_version="test-v1")
        detector.fit(sample_metrics_df)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "model.joblib")
            detector.save(path)
            
            assert os.path.exists(path)
            
            loaded = AnomalyDetector.load(path)
            
            assert loaded.is_fitted == True
            assert loaded.model_version == "test-v1"
            assert loaded.feature_names == detector.feature_names
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_risk_levels(self, sample_metrics_df):
        """Test risk level categorization."""
        detector = AnomalyDetector()
        detector.fit(sample_metrics_df)
        
        result = detector.predict(sample_metrics_df.head(10))
        
        valid_levels = {"normal", "warning", "critical"}
        assert all(level in valid_levels for level in result["risk_levels"])
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_scores_normalized(self, sample_metrics_df):
        """Test that anomaly scores are in [0, 1] range."""
        detector = AnomalyDetector()
        detector.fit(sample_metrics_df)
        
        result = detector.predict(sample_metrics_df)
        
        scores = result["anomaly_scores"]
        assert all(0 <= s <= 1 for s in scores), "Scores should be normalized to [0, 1]"


class TestStreamingAnomalyDetector:
    """Tests for StreamingAnomalyDetector class."""
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_streaming_detection(self, sample_metrics_df):
        """Test streaming anomaly detection."""
        from datetime import datetime
        
        # Create base detector
        base_detector = AnomalyDetector()
        base_detector.fit(sample_metrics_df)
        
        # Create streaming detector
        streaming = StreamingAnomalyDetector(
            detector=base_detector,
            window_size=20,
            alert_threshold=0.7
        )
        
        # Process points
        for i in range(25):
            result = streaming.process_point(
                asset_id="asset_1",
                timestamp=datetime.utcnow(),
                metrics={
                    "temperature": 65 + np.random.randn() * 10,
                    "vibration": 0.5 + np.random.randn() * 0.1,
                    "pressure": 100 + np.random.randn() * 15,
                    "rpm": 1500 + np.random.randn() * 100,
                    "current": 10 + np.random.randn() * 2,
                }
            )
        
        # After enough points, should get results
        assert result is not None
        assert "asset_id" in result
