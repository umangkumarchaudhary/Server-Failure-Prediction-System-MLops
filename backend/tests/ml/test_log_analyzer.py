"""
Unit Tests for Log Analyzer Model.
"""
import pytest
import os
import tempfile

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ml.models.log_analyzer import LogAnalyzer, LogPreprocessor


class TestLogPreprocessor:
    """Tests for LogPreprocessor class."""
    
    @pytest.mark.unit
    def test_preprocess_removes_timestamps(self):
        """Test timestamp normalization."""
        log = "2026-01-08T10:00:00Z Error occurred in module"
        result = LogPreprocessor.preprocess(log)
        
        assert "<TIMESTAMP>" in result
        assert "2026" not in result
    
    @pytest.mark.unit
    def test_preprocess_removes_ips(self):
        """Test IP address normalization."""
        log = "Connection failed to 192.168.1.100"
        result = LogPreprocessor.preprocess(log)
        
        assert "<IP>" in result
        assert "192.168.1.100" not in result
    
    @pytest.mark.unit
    def test_preprocess_removes_uuids(self):
        """Test UUID normalization."""
        log = "Request 550e8400-e29b-41d4-a716-446655440000 failed"
        result = LogPreprocessor.preprocess(log)
        
        assert "<UUID>" in result
    
    @pytest.mark.unit
    def test_extract_error_keywords(self):
        """Test error keyword extraction."""
        log = "ERROR: DatabaseConnectionError - Failed to connect"
        keywords = LogPreprocessor.extract_error_keywords(log)
        
        assert len(keywords) > 0


class TestLogAnalyzer:
    """Tests for LogAnalyzer class."""
    
    @pytest.mark.unit
    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer = LogAnalyzer(use_tfidf_fallback=True)
        
        assert analyzer.min_cluster_size == 5
        assert analyzer.is_fitted == False
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_fit(self, sample_logs):
        """Test fitting on logs."""
        analyzer = LogAnalyzer(
            min_cluster_size=3,
            use_tfidf_fallback=True
        )
        analyzer.fit(sample_logs)
        
        assert analyzer.is_fitted == True
        assert len(analyzer.cluster_representatives) > 0
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_predict(self, sample_logs):
        """Test cluster prediction."""
        analyzer = LogAnalyzer(
            min_cluster_size=3,
            use_tfidf_fallback=True
        )
        analyzer.fit(sample_logs)
        
        new_logs = [
            "ERROR Connection failed to sensor",
            "INFO System started",
            "WARNING Temperature high",
        ]
        
        predictions = analyzer.predict(new_logs)
        
        assert len(predictions) == 3
        assert all(isinstance(p, int) for p in predictions)
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_analyze_batch(self, sample_logs):
        """Test batch analysis."""
        analyzer = LogAnalyzer(
            min_cluster_size=3,
            use_tfidf_fallback=True
        )
        
        result = analyzer.analyze_batch(sample_logs)
        
        assert "total_logs" in result
        assert "num_clusters" in result
        assert "clusters" in result
        assert result["total_logs"] == len(sample_logs)
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_find_similar_logs(self, sample_logs):
        """Test similar log retrieval."""
        analyzer = LogAnalyzer(
            min_cluster_size=3,
            use_tfidf_fallback=True
        )
        analyzer.fit(sample_logs)
        
        query = "ERROR Connection timeout to sensor"
        similar = analyzer.find_similar_logs(query, top_k=3)
        
        assert len(similar) == 3
        assert "log" in similar[0]
        assert "similarity" in similar[0]
        assert 0 <= similar[0]["similarity"] <= 1
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_save_and_load(self, sample_logs):
        """Test serialization."""
        analyzer = LogAnalyzer(
            min_cluster_size=3,
            use_tfidf_fallback=True,
            model_version="test-v1"
        )
        analyzer.fit(sample_logs)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "log_analyzer.joblib")
            analyzer.save(path)
            
            assert os.path.exists(path)
            
            loaded = LogAnalyzer.load(path)
            
            assert loaded.is_fitted == True
            assert loaded.model_version == "test-v1"
    
    @pytest.mark.unit
    @pytest.mark.ml
    def test_cluster_representatives_have_keywords(self, sample_logs):
        """Test that cluster representatives include error keywords."""
        analyzer = LogAnalyzer(
            min_cluster_size=3,
            use_tfidf_fallback=True
        )
        analyzer.fit(sample_logs)
        
        clusters = analyzer.get_clusters()
        
        for cluster_id, info in clusters.items():
            assert "representative" in info
            assert "size" in info
            assert info["size"] > 0
