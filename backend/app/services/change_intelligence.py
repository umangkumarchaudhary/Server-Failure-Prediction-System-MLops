"""Correlation helpers for deploy, runtime, and config changes."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence


class ChangeIntelligenceService:
    """Score and summarize recent changes around a risky asset."""

    def __init__(self) -> None:
        self.severity_weights = {
            "critical": 1.0,
            "high": 0.9,
            "warning": 0.8,
            "medium": 0.65,
            "low": 0.4,
            "info": 0.25,
        }
        self.type_weights = {
            "deploy": 1.0,
            "package": 0.95,
            "runtime": 0.95,
            "config": 0.9,
            "feature_flag": 0.85,
            "schema": 0.9,
            "infra": 0.8,
        }

    def enrich_asset_assessment(
        self,
        assessment: Dict[str, Any],
        change_events: Sequence[Dict[str, Any]],
        asset_name_lookup: Optional[Dict[str, str]] = None,
        horizon_hours: int = 24,
    ) -> Dict[str, Any]:
        """Attach likely change causes and recent change context to an asset assessment."""
        enriched = dict(assessment)
        scored_events = self._score_events(change_events, horizon_hours=horizon_hours)
        recent_changes = [
            self._serialize_event(event, asset_name_lookup=asset_name_lookup)
            for event in scored_events[:3]
        ]

        risk_level = str(assessment.get("risk_level", "normal"))
        risk_multiplier = 1.0 if risk_level == "critical" else 0.75 if risk_level == "warning" else 0.35
        change_correlation_score = round(
            min(1.0, (scored_events[0]["correlation_score"] if scored_events else 0.0) * risk_multiplier),
            2,
        )

        likely_causes = []
        if risk_level in {"warning", "critical"}:
            for event in recent_changes[:2]:
                if event["correlation_score"] < 0.35:
                    continue
                cause = f"{event['change_type'].replace('_', ' ')} change: {event['title']}"
                if event.get("version"):
                    cause += f" ({event['version']})"
                likely_causes.append(cause)

        enriched["recent_changes"] = recent_changes
        enriched["change_correlation_score"] = change_correlation_score
        enriched["likely_causes"] = likely_causes

        if likely_causes and risk_level in {"warning", "critical"}:
            enriched["summary"] = (
                f"{assessment['summary']} Recent change activity may be contributing, led by {likely_causes[0]}."
            )

        return enriched

    def summarize_recent_changes(
        self,
        change_events: Sequence[Dict[str, Any]],
        asset_name_lookup: Optional[Dict[str, str]] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Return the most recent tenant-wide change feed entries."""
        ordered = sorted(
            [self._normalize_event(event) for event in change_events],
            key=lambda item: item["timestamp"],
            reverse=True,
        )
        return [
            self._serialize_event(event, asset_name_lookup=asset_name_lookup)
            for event in ordered[:limit]
        ]

    def count_change_correlated_assets(self, assets: Sequence[Dict[str, Any]]) -> int:
        """Count how many assets have both risk and meaningful change correlation."""
        return len(
            [
                asset
                for asset in assets
                if asset.get("risk_level") in {"warning", "critical"}
                and float(asset.get("change_correlation_score", 0.0)) >= 0.3
            ]
        )

    def _score_events(
        self,
        change_events: Sequence[Dict[str, Any]],
        horizon_hours: int,
    ) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        horizon = timedelta(hours=horizon_hours)
        scored: List[Dict[str, Any]] = []

        for raw_event in change_events:
            event = self._normalize_event(raw_event)
            age = now - event["timestamp"]
            if age > horizon:
                continue

            recency = max(0.1, 1.0 - (age.total_seconds() / horizon.total_seconds()))
            severity = self.severity_weights.get(event["severity"], 0.55)
            change_type = self.type_weights.get(event["change_type"], 0.7)
            asset_scope = 1.0 if event.get("asset_id") else 0.8

            event["correlation_score"] = round(min(1.0, recency * 0.45 + severity * 0.35 + change_type * 0.2) * asset_scope, 2)
            scored.append(event)

        return sorted(
            scored,
            key=lambda item: (item["correlation_score"], item["timestamp"]),
            reverse=True,
        )

    def _normalize_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        timestamp = event.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).replace(tzinfo=None)

        metadata = event.get("metadata")
        if metadata is None:
            metadata = event.get("extra_data") or {}

        return {
            "id": int(event.get("id", 0) or 0),
            "asset_id": event.get("asset_id"),
            "timestamp": timestamp or datetime.utcnow(),
            "change_type": str(event.get("change_type", "change")).strip().lower().replace(" ", "_"),
            "title": event.get("title", "Change event"),
            "summary": event.get("summary"),
            "source": event.get("source"),
            "severity": str(event.get("severity", "medium")).strip().lower(),
            "version": event.get("version"),
            "metadata": metadata,
            "correlation_score": float(event.get("correlation_score", 0.0) or 0.0),
        }

    def _serialize_event(
        self,
        event: Dict[str, Any],
        asset_name_lookup: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        normalized = self._normalize_event(event)
        asset_id = normalized.get("asset_id")
        return {
            "id": normalized["id"],
            "asset_id": asset_id,
            "asset_name": asset_name_lookup.get(str(asset_id)) if asset_id and asset_name_lookup else None,
            "timestamp": normalized["timestamp"].isoformat(),
            "change_type": normalized["change_type"],
            "title": normalized["title"],
            "summary": normalized["summary"],
            "source": normalized["source"],
            "severity": normalized["severity"],
            "version": normalized["version"],
            "metadata": normalized["metadata"],
            "correlation_score": normalized["correlation_score"],
        }


_change_intelligence: Optional[ChangeIntelligenceService] = None


def get_change_intelligence() -> ChangeIntelligenceService:
    """Get the singleton change intelligence service."""
    global _change_intelligence
    if _change_intelligence is None:
        _change_intelligence = ChangeIntelligenceService()
    return _change_intelligence
