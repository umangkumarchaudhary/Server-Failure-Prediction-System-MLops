"""Focused smoke tests for Phase 6 telemetry adapter ingestion."""
import os
import sys
from datetime import UTC, datetime

os.environ["DEBUG"] = "false"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.services.telemetry_adapter import get_telemetry_adapter
from app.services.telemetry_normalizer import get_telemetry_normalizer


class TestPhase6Smoke:
    """Smoke coverage for collector-friendly telemetry ingestion."""

    def test_normalizer_recognizes_otel_style_metric_names(self):
        normalizer = get_telemetry_normalizer()

        assert normalizer.normalize_metric_name("system.cpu.utilization") == "cpu_pressure"
        assert normalizer.normalize_metric_name("db.client.operation.duration") == "db_latency"
        assert normalizer.normalize_metric_name("process.runtime.nodejs.eventloop.lag.max") == "event_loop_lag"

    def test_adapter_expands_and_normalizes_real_world_telemetry_samples(self):
        adapter = get_telemetry_adapter()
        timestamp = datetime.now(UTC).replace(tzinfo=None)

        points = adapter.expand_envelope(
            asset_id="payments-api-1",
            timestamp=timestamp,
            adapter_type="host",
            metrics={},
            samples=[
                {"name": "system.cpu.utilization", "value": 0.91, "unit": "ratio"},
                {"name": "http.server.request.duration", "value": 0.82, "unit": "s"},
                {"name": "system.memory.available", "value": 2_147_483_648, "unit": "bytes"},
            ],
            source="otel-collector",
            tags={"env": "prod"},
        )

        assert len(points) == 3

        by_name = {point["metric_name"]: point for point in points}
        assert round(by_name["cpu_pressure"]["metric_value"], 1) == 91.0
        assert round(by_name["latency"]["metric_value"], 0) == 820.0
        assert round(by_name["memory_headroom"]["metric_value"], 0) == 2048.0

    def test_adapter_catalog_exposes_host_app_db_and_runtime_packs(self):
        catalog = get_telemetry_adapter().supported_adapters()
        adapter_types = {item["adapter_type"] for item in catalog}

        assert {"host", "application", "database", "runtime"}.issubset(adapter_types)


if __name__ == "__main__":
    smoke = TestPhase6Smoke()
    smoke.test_normalizer_recognizes_otel_style_metric_names()
    smoke.test_adapter_expands_and_normalizes_real_world_telemetry_samples()
    smoke.test_adapter_catalog_exposes_host_app_db_and_runtime_packs()
