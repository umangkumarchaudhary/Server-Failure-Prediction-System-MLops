"""Telemetry normalization helpers for ingestion and onboarding."""
from __future__ import annotations

from typing import Dict, List, Optional

from app.services.risk_engine import get_risk_engine


class TelemetryNormalizer:
    """Map related metric aliases onto canonical risk-engine signal names."""

    EXTERNAL_ALIASES: Dict[str, str] = {
        "system.cpu.utilization": "cpu_pressure",
        "system.cpu.load_average.1m": "load_pressure",
        "system.memory.utilization": "memory_pressure",
        "system.memory.available": "memory_headroom",
        "system.filesystem.utilization": "disk_pressure",
        "system.filesystem.available": "disk_headroom",
        "system.cpu.time.iowait": "io_wait",
        "db.client.operation.duration": "db_latency",
        "db.client.connections.usage": "db_connections",
        "http.server.request.duration": "latency",
        "http.server.error.rate": "error_rate",
        "messaging.queue.size": "queue_backlog",
        "process.runtime.nodejs.eventloop.lag.max": "event_loop_lag",
        "process.runtime.jvm.gc.duration": "gc_pause",
        "k8s.container.restart.count": "restart_count",
        "system.ntp.offset": "clock_skew",
    }

    def __init__(self) -> None:
        self._alias_map: Dict[str, str] = {}
        self._catalog: List[Dict[str, object]] = []
        external_aliases_by_signal: Dict[str, List[str]] = {}

        for alias, signal_key in self.EXTERNAL_ALIASES.items():
            external_aliases_by_signal.setdefault(signal_key, []).append(alias)

        for rule in get_risk_engine().rules:
            aliases = sorted(
                {
                    self._normalize(alias)
                    for alias in (
                        *rule.aliases,
                        rule.signal_key,
                        *external_aliases_by_signal.get(rule.signal_key, []),
                    )
                }
            )
            for alias in aliases:
                self._alias_map[alias] = rule.signal_key

            self._catalog.append(
                {
                    "signal_key": rule.signal_key,
                    "label": rule.label,
                    "category": rule.category,
                    "aliases": aliases,
                }
            )

        self._catalog.sort(key=lambda item: (str(item["category"]), str(item["label"])))

    def normalize_metric_name(self, metric_name: str) -> str:
        """Return the canonical signal name when the metric is recognized."""
        normalized = self._normalize(metric_name)
        return self._alias_map.get(normalized, normalized)

    def supported_signals(self) -> List[Dict[str, object]]:
        """List the canonical signal catalog for ingestion guidance."""
        return [dict(item) for item in self._catalog]

    def resolve_signal(self, metric_name: str) -> Optional[Dict[str, object]]:
        """Return the catalog entry for a known signal alias."""
        canonical = self.normalize_metric_name(metric_name)
        for item in self._catalog:
            if item["signal_key"] == canonical:
                return dict(item)
        return None

    def _normalize(self, value: str) -> str:
        return (
            value.strip()
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
            .replace(".", "_")
            .replace("/", "_")
            .replace(":", "_")
        )


_telemetry_normalizer: Optional[TelemetryNormalizer] = None


def get_telemetry_normalizer() -> TelemetryNormalizer:
    """Get the singleton telemetry normalizer."""
    global _telemetry_normalizer
    if _telemetry_normalizer is None:
        _telemetry_normalizer = TelemetryNormalizer()
    return _telemetry_normalizer
