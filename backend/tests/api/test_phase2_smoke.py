"""
Focused smoke tests for the Phase 2 pre-failure risk engine.
"""
import os
import sys
from datetime import datetime, timedelta

os.environ.setdefault("DEBUG", "false")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.services.risk_engine import get_risk_engine


class TestPhase2Smoke:
    """Smoke coverage for the early warning risk engine."""

    def test_high_pressure_signals_raise_critical_risk(self):
        now = datetime.utcnow()
        metric_points = [
            {"asset_id": "asset-1", "timestamp": now - timedelta(minutes=20), "metric_name": "cpu_usage", "metric_value": 72.0},
            {"asset_id": "asset-1", "timestamp": now - timedelta(minutes=10), "metric_name": "cpu_usage", "metric_value": 88.0},
            {"asset_id": "asset-1", "timestamp": now, "metric_name": "cpu_usage", "metric_value": 96.0},
            {"asset_id": "asset-1", "timestamp": now - timedelta(minutes=20), "metric_name": "memory_percent", "metric_value": 78.0},
            {"asset_id": "asset-1", "timestamp": now - timedelta(minutes=10), "metric_name": "memory_percent", "metric_value": 89.0},
            {"asset_id": "asset-1", "timestamp": now, "metric_name": "memory_percent", "metric_value": 94.0},
            {"asset_id": "asset-1", "timestamp": now - timedelta(minutes=20), "metric_name": "db_latency_ms", "metric_value": 120.0},
            {"asset_id": "asset-1", "timestamp": now - timedelta(minutes=10), "metric_name": "db_latency_ms", "metric_value": 340.0},
            {"asset_id": "asset-1", "timestamp": now, "metric_name": "db_latency_ms", "metric_value": 520.0},
        ]
        prediction_points = [
            {"asset_id": "asset-1", "timestamp": now - timedelta(minutes=5), "anomaly_score": 0.84, "rul_estimate": 18.0},
            {"asset_id": "asset-1", "timestamp": now, "anomaly_score": 0.91, "rul_estimate": 12.0},
        ]

        assessment = get_risk_engine().assess_asset(
            asset_id="asset-1",
            asset_name="Database API",
            asset_type="server",
            metric_points=metric_points,
            prediction_points=prediction_points,
        )

        assert assessment["risk_level"] == "critical"
        assert assessment["risk_score"] >= 70
        assert assessment["forecast_window"] in {"next 1 hour", "next 6 hours"}
        assert assessment["indicators"]

    def test_fleet_overview_surfaces_top_risk_assets(self):
        now = datetime.utcnow()
        assets = [
            {"id": "asset-1", "name": "Database API", "type": "server"},
            {"id": "asset-2", "name": "Batch Worker", "type": "server"},
        ]
        metric_points = [
            {"asset_id": "asset-1", "timestamp": now - timedelta(minutes=10), "metric_name": "error_rate", "metric_value": 0.08},
            {"asset_id": "asset-1", "timestamp": now, "metric_name": "error_rate", "metric_value": 0.12},
            {"asset_id": "asset-2", "timestamp": now - timedelta(minutes=10), "metric_name": "cpu_usage", "metric_value": 35.0},
            {"asset_id": "asset-2", "timestamp": now, "metric_name": "cpu_usage", "metric_value": 42.0},
        ]
        prediction_points = [
            {"asset_id": "asset-1", "timestamp": now, "anomaly_score": 0.88, "rul_estimate": 20.0},
        ]

        overview = get_risk_engine().assess_fleet(assets, metric_points, prediction_points, limit=2)

        assert overview["monitored_assets"] == 2
        assert overview["assets"][0]["asset_id"] == "asset-1"
        assert overview["highest_risk_score"] >= overview["assets"][0]["risk_score"]
