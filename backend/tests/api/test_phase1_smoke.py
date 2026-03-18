"""
Focused smoke tests for the Phase 1 consistency fixes.
"""
from datetime import datetime
import os
import sys

import pandas as pd

os.environ.setdefault("DEBUG", "false")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.api.v1.endpoints.copilot import get_copilot_service
from app.api.v1.endpoints.mcp import get_mcp_server
from app.api.v1.endpoints.ml_guard import get_prediction_monitor
from app.models.models import Asset
from app.schemas.schemas import AssetResponse


class TestPhase1Smoke:
    """Smoke coverage for the first phase wiring changes."""

    def test_asset_response_reads_extra_data_as_metadata(self):
        asset = Asset(
            id="asset-1",
            tenant_id="tenant-1",
            name="Pump A",
            type="machine",
            tags=["critical"],
            extra_data={"manufacturer": "Acme"},
            risk_level="warning",
            created_at=datetime.utcnow(),
        )

        response = AssetResponse.model_validate(asset)

        assert response.metadata == {"manufacturer": "Acme"}

    def test_prediction_monitor_default_reference_supports_prediction_checks(self):
        monitor = get_prediction_monitor("prediction")
        report = monitor.detect_prediction_drift(
            pd.DataFrame([{"prediction": 0.2}, {"prediction": 0.4}, {"prediction": 0.5}]),
            "prediction",
        )

        assert "error" not in report
        assert report["summary"]["total_columns"] == 1

    def test_lazy_ml_services_are_importable_from_backend_startup_path(self):
        assert type(get_copilot_service()).__name__ == "CopilotService"
        assert type(get_mcp_server()).__name__ == "SensorMindMCPServer"
