"""
Focused smoke tests for the Phase 3 telemetry normalization and alert sync flow.
"""
import asyncio
import os
import sys
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

os.environ["DEBUG"] = "false"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.models.models import Asset
from app.services.risk_alert_service import RISK_ALERT_SOURCE, RiskAlertService
from app.services.telemetry_normalizer import get_telemetry_normalizer


class FakeResult:
    """Small stand-in for the SQLAlchemy async result interface used by smoke tests."""

    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows

    def scalars(self):
        return self


class FakeAsyncSession:
    """Queue-based async session stub for deterministic service tests."""

    def __init__(self, results):
        self._results = list(results)
        self.added = []

    async def execute(self, _query):
        if not self._results:
            raise AssertionError("Unexpected execute() call with no fake result prepared.")
        return self._results.pop(0)

    async def flush(self):
        return None

    def add(self, instance):
        self.added.append(instance)


class TestPhase3Smoke:
    """Smoke coverage for telemetry normalization and automated risk alerts."""

    def test_normalizer_maps_aliases_to_canonical_names(self):
        normalizer = get_telemetry_normalizer()

        assert normalizer.normalize_metric_name("cpu_percent") == "cpu_pressure"
        assert normalizer.normalize_metric_name("db_query_ms") == "db_latency"
        assert normalizer.normalize_metric_name("custom_signal") == "custom_signal"

    async def test_risk_alert_sync_creates_and_resolves_alerts(self):
        now = datetime.now(UTC).replace(tzinfo=None)
        asset = Asset(
            id="asset-1",
            tenant_id="tenant-1",
            name="Payments API",
            type="server",
            tags=[],
            extra_data={},
            risk_level="normal",
            created_at=now,
        )

        creation_session = FakeAsyncSession(
            [
                FakeResult([asset]),
                FakeResult(
                    [
                        SimpleNamespace(
                            asset_id="asset-1",
                            timestamp=now - timedelta(minutes=10),
                            metric_name="cpu_percent",
                            metric_value=88.0,
                        ),
                        SimpleNamespace(
                            asset_id="asset-1",
                            timestamp=now,
                            metric_name="cpu_percent",
                            metric_value=96.0,
                        ),
                        SimpleNamespace(
                            asset_id="asset-1",
                            timestamp=now,
                            metric_name="db_query_ms",
                            metric_value=460.0,
                        ),
                    ]
                ),
                FakeResult(
                    [
                        SimpleNamespace(
                            asset_id="asset-1",
                            timestamp=now,
                            anomaly_score=0.9,
                            rul_estimate=18.0,
                        )
                    ]
                ),
                FakeResult([]),
                FakeResult([]),
            ]
        )

        service = RiskAlertService()
        creation_result = await service.sync_for_assets(
            creation_session,
            tenant_id="tenant-1",
            asset_ids=["asset-1"],
        )

        assert creation_result["alerts_created"] == 1
        assert creation_result["assets_with_telemetry"] == 1
        assert asset.risk_level in {"warning", "critical"}
        assert asset.health_score is not None and asset.health_score < 60
        assert creation_session.added

        created_alert = creation_session.added[0]
        assert created_alert.channel == RISK_ALERT_SOURCE
        assert created_alert.status == "active"
        assert created_alert.severity in {"warning", "critical"}

        resolve_session = FakeAsyncSession(
            [
                FakeResult([asset]),
                FakeResult(
                    [
                        SimpleNamespace(
                            asset_id="asset-1",
                            timestamp=now + timedelta(minutes=15),
                            metric_name="cpu_percent",
                            metric_value=34.0,
                        ),
                        SimpleNamespace(
                            asset_id="asset-1",
                            timestamp=now + timedelta(minutes=15),
                            metric_name="db_query_ms",
                            metric_value=42.0,
                        ),
                    ]
                ),
                FakeResult([]),
                FakeResult([]),
                FakeResult([created_alert]),
            ]
        )

        resolve_result = await service.sync_for_assets(
            resolve_session,
            tenant_id="tenant-1",
            asset_ids=["asset-1"],
        )

        assert resolve_result["alerts_resolved"] == 1
        assert asset.risk_level == "normal"
        assert asset.health_score == 100.0
        assert created_alert.status == "resolved"


if __name__ == "__main__":
    smoke = TestPhase3Smoke()
    smoke.test_normalizer_maps_aliases_to_canonical_names()
    asyncio.run(smoke.test_risk_alert_sync_creates_and_resolves_alerts())
