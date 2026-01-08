"""
Unit Tests for RUL Forecaster Model.
"""
import pytest
import numpy as np
import pandas as pd
import tempfile
import os

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ml.models.rul_forecaster import RULForecaster


class TestRULForecaster:
    """Tests for RULForecaster class."""
    
    @pytest.mark.unit
    def test_initialization(self):
        """Test model initialization."""
        forecaster = RULForecaster()
        
        assert forecaster.sequence_length == 50
        assert forecaster.hidden_size == 128
        assert forecaster.is_fitted == False
    
    @pytest.mark.unit
    def test_initialization_custom_params(self):
        """Test custom parameters."""
        forecaster = RULForecaster(
            sequence_length=30,
            hidden_size=64,
            max_rul=100.0,
            model_version="2.0.0"
        )
        
        assert forecaster.sequence_length == 30
        assert forecaster.hidden_size == 64
        assert forecaster.max_rul == 100.0
    
    @pytest.mark.unit
    @pytest.mark.ml
    @pytest.mark.slow
    def test_fit(self, sample_rul_df):
        """Test model training."""
        forecaster = RULForecaster(sequence_length=20)
        forecaster.fit(
            sample_rul_df,
            rul_column="RUL",
            epochs=2,  # Quick test
            batch_size=32,
            verbose=False,
        )
        
        assert forecaster.is_fitted == True
        assert "final_train_loss" in forecaster.training_stats
        assert "final_val_loss" in forecaster.training_stats
    
    @pytest.mark.unit
    @pytest.mark.ml
    @pytest.mark.slow
    def test_predict_shape(self, sample_rul_df):
        """Test prediction output shape."""
        forecaster = RULForecaster(sequence_length=20)
        forecaster.fit(sample_rul_df, epochs=2, verbose=False)
        
        # Create test sequences
        n_samples = 5
        seq_len = 20
        n_features = len(sample_rul_df.columns) - 1  # Exclude RUL
        
        test_sequences = np.random.randn(n_samples, seq_len, n_features)
        
        result = forecaster.predict(test_sequences)
        
        assert "rul_estimate" in result
        assert len(result["rul_estimate"]) == n_samples
    
    @pytest.mark.unit
    @pytest.mark.ml
    @pytest.mark.slow
    def test_predict_with_confidence(self, sample_rul_df):
        """Test prediction with confidence intervals."""
        forecaster = RULForecaster(sequence_length=20)
        forecaster.fit(sample_rul_df, epochs=2, verbose=False)
        
        n_features = len(sample_rul_df.columns) - 1
        test_sequences = np.random.randn(3, 20, n_features)
        
        result = forecaster.predict(test_sequences, return_confidence=True)
        
        assert "rul_estimate" in result
        assert "confidence_lower" in result
        assert "confidence_upper" in result
        assert "uncertainty" in result
    
    @pytest.mark.unit
    @pytest.mark.ml
    @pytest.mark.slow
    def test_predict_single(self, sample_rul_df):
        """Test single asset prediction."""
        forecaster = RULForecaster(sequence_length=20)
        feature_cols = [c for c in sample_rul_df.columns if c != "RUL"]
        
        forecaster.fit(sample_rul_df, epochs=2, verbose=False)
        
        # Use feature columns only
        recent_data = sample_rul_df[feature_cols].tail(50)
        result = forecaster.predict_single(recent_data)
        
        assert "rul_estimate" in result
        assert result["rul_estimate"] is not None
    
    @pytest.mark.unit
    @pytest.mark.ml
    @pytest.mark.slow
    def test_save_and_load(self, sample_rul_df):
        """Test model serialization."""
        forecaster = RULForecaster(sequence_length=20, model_version="test-v1")
        forecaster.fit(sample_rul_df, epochs=2, verbose=False)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "rul_model.pt")
            forecaster.save(path)
            
            assert os.path.exists(path)
            
            loaded = RULForecaster.load(path)
            
            assert loaded.is_fitted == True
            assert loaded.model_version == "test-v1"
            assert loaded.sequence_length == 20
    
    @pytest.mark.unit
    def test_predict_without_fit_raises(self):
        """Test error when predicting without fitting."""
        forecaster = RULForecaster()
        
        with pytest.raises(ValueError, match="not fitted"):
            forecaster.predict(np.random.randn(1, 50, 5))
    
    @pytest.mark.unit
    @pytest.mark.ml
    @pytest.mark.slow
    def test_rul_values_reasonable(self, sample_rul_df):
        """Test that RUL predictions are reasonable."""
        forecaster = RULForecaster(sequence_length=20, max_rul=130.0)
        forecaster.fit(sample_rul_df, epochs=5, verbose=False)
        
        n_features = len(sample_rul_df.columns) - 1
        test_sequences = np.random.randn(10, 20, n_features)
        
        result = forecaster.predict(test_sequences, return_confidence=False)
        
        # RUL should be non-negative and not exceed max
        for rul in result["rul_estimate"]:
            assert rul >= 0, "RUL should be non-negative"
