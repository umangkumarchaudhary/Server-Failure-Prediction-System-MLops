"""
Focused smoke tests for the Phase 4 change intelligence flow.
"""
import os
import sys
from datetime import UTC, datetime, timedelta

os.environ["DEBUG"] = "false"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.api.v1.endpoints.ingest import _derive_change_metric
from app.services.change_intelligence import ChangeIntelligenceService


class TestPhase4Smoke:
    """Smoke coverage for change ingestion and correlation logic."""

    def test_change_events_map_to_change_pressure_metrics(self):
        assert _derive_change_metric("deploy", "high") == ("deploy_change_score", 1.6)
        assert _derive_change_metric("runtime", "critical") == ("runtime_change_score", 2.0)
        assert _derive_change_metric("unknown", "medium") is None

    def test_change_intelligence_enriches_risky_assets_with_likely_causes(self):
        now = datetime.now(UTC).replace(tzinfo=None)
        assessment = {
            "asset_id": "asset-1",
            "asset_name": "Payments API",
            "asset_type": "server",
            "risk_score": 78,
            "risk_level": "critical",
            "confidence": 0.84,
            "forecast_window": "next 6 hours",
            "summary": "Payments API shows a high chance of failure unless error rate is addressed quickly.",
            "last_metric_at": now.isoformat(),
            "last_prediction_at": now.isoformat(),
            "top_signals": ["Error rate"],
            "recommended_actions": ["Rollback the latest deploy before customers see a wider incident."],
            "indicators": [],
        }
        change_events = [
            {
                "id": 1,
                "asset_id": "asset-1",
                "timestamp": now - timedelta(minutes=40),
                "change_type": "deploy",
                "title": "Payments API rollout",
                "summary": "Version 2026.03.17.1 deployed to production",
                "source": "github-actions",
                "severity": "high",
                "version": "2026.03.17.1",
                "extra_data": {"commit": "abc123"},
            },
            {
                "id": 2,
                "asset_id": None,
                "timestamp": now - timedelta(hours=2),
                "change_type": "runtime",
                "title": "Python runtime patch",
                "summary": "Workers moved to Python 3.13.2",
                "source": "render",
                "severity": "medium",
                "version": "3.13.2",
                "extra_data": {},
            },
        ]

        enriched = ChangeIntelligenceService().enrich_asset_assessment(
            assessment,
            change_events,
            asset_name_lookup={"asset-1": "Payments API"},
        )

        assert enriched["change_correlation_score"] >= 0.5
        assert enriched["likely_causes"]
        assert "deploy change" in enriched["likely_causes"][0]
        assert len(enriched["recent_changes"]) == 2
        assert "Recent change activity may be contributing" in enriched["summary"]


if __name__ == "__main__":
    smoke = TestPhase4Smoke()
    smoke.test_change_events_map_to_change_pressure_metrics()
    smoke.test_change_intelligence_enriches_risky_assets_with_likely_causes()
