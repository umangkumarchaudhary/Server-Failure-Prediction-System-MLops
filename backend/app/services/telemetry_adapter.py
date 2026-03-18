"""Adapter-friendly telemetry translation for host, app, DB, and runtime packs."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.telemetry_normalizer import TelemetryNormalizer, get_telemetry_normalizer


class TelemetryAdapterService:
    """Translate collector-style telemetry envelopes into canonical metric points."""

    ADAPTER_CATALOG: List[Dict[str, Any]] = [
        {
            "adapter_type": "host",
            "label": "Host / Node Collector",
            "description": "CPU, memory, disk, load, IO wait, and clock sync from nodes or VMs.",
            "recommended_metrics": [
                "system.cpu.utilization",
                "system.memory.utilization",
                "system.filesystem.utilization",
                "system.cpu.load_average.1m",
                "system.cpu.time.iowait",
                "system.ntp.offset",
            ],
            "sample_payload": {
                "asset_id": "payments-api-node-1",
                "timestamp": "2026-03-17T10:00:00Z",
                "adapter_type": "host",
                "source": "otel-collector",
                "samples": [
                    {"name": "system.cpu.utilization", "value": 0.91, "unit": "ratio"},
                    {"name": "system.memory.utilization", "value": 0.84, "unit": "ratio"},
                    {"name": "system.filesystem.utilization", "value": 0.88, "unit": "ratio"},
                    {"name": "system.cpu.load_average.1m", "value": 6.2},
                ],
            },
        },
        {
            "adapter_type": "application",
            "label": "Application / HTTP",
            "description": "Error rate, request latency, queue backlog, and service-level symptoms.",
            "recommended_metrics": [
                "http.server.error.rate",
                "http.server.request.duration",
                "messaging.queue.size",
                "error_rate",
                "p95_latency_ms",
            ],
            "sample_payload": {
                "asset_id": "payments-api",
                "timestamp": "2026-03-17T10:00:00Z",
                "adapter_type": "application",
                "source": "service-metrics",
                "samples": [
                    {"name": "http.server.error.rate", "value": 0.07, "unit": "ratio"},
                    {"name": "http.server.request.duration", "value": 0.82, "unit": "s"},
                    {"name": "messaging.queue.size", "value": 144},
                ],
            },
        },
        {
            "adapter_type": "database",
            "label": "Database Health Pack",
            "description": "Slow queries, DB latency, and connection pool saturation.",
            "recommended_metrics": [
                "db.client.operation.duration",
                "db.client.connections.usage",
                "slow_query_ms",
                "connection_pool_usage",
            ],
            "sample_payload": {
                "asset_id": "primary-postgres",
                "timestamp": "2026-03-17T10:00:00Z",
                "adapter_type": "database",
                "source": "postgres-exporter",
                "samples": [
                    {"name": "db.client.operation.duration", "value": 0.43, "unit": "s"},
                    {"name": "db.client.connections.usage", "value": 0.86, "unit": "ratio"},
                ],
            },
        },
        {
            "adapter_type": "runtime",
            "label": "Runtime / Process Health",
            "description": "Event loop lag, GC pauses, restarts, and runtime-level instability.",
            "recommended_metrics": [
                "process.runtime.nodejs.eventloop.lag.max",
                "process.runtime.jvm.gc.duration",
                "k8s.container.restart.count",
                "restart_count",
            ],
            "sample_payload": {
                "asset_id": "worker-runtime",
                "timestamp": "2026-03-17T10:00:00Z",
                "adapter_type": "runtime",
                "source": "runtime-agent",
                "samples": [
                    {"name": "process.runtime.nodejs.eventloop.lag.max", "value": 0.19, "unit": "s"},
                    {"name": "k8s.container.restart.count", "value": 2},
                ],
            },
        },
    ]

    PERCENT_SIGNALS = {"cpu_pressure", "memory_pressure", "disk_pressure", "db_connections"}
    LATENCY_SIGNALS = {"db_latency", "latency", "event_loop_lag", "gc_pause", "clock_skew"}
    BYTES_TO_MB_SIGNALS = {"memory_headroom"}
    BYTES_TO_PERCENT_SIGNALS = {"disk_headroom"}
    DAY_SIGNALS = {"cert_expiry"}

    def __init__(self, normalizer: Optional[TelemetryNormalizer] = None) -> None:
        self.normalizer = normalizer or get_telemetry_normalizer()

    def supported_adapters(self) -> List[Dict[str, Any]]:
        """Return adapter definitions for onboarding and UI surfaces."""
        return [deepcopy(adapter) for adapter in self.ADAPTER_CATALOG]

    def expand_envelope(
        self,
        asset_id: str,
        timestamp: datetime,
        adapter_type: str,
        metrics: Dict[str, float],
        samples: List[Dict[str, Any]],
        source: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """Expand an adapter payload into canonical metric points."""
        del adapter_type, source, tags
        expanded_points: List[Dict[str, Any]] = []

        for metric_name, metric_value in metrics.items():
            expanded_points.append(
                self._build_point(asset_id, timestamp, metric_name, float(metric_value), unit=None)
            )

        for sample in samples:
            expanded_points.append(
                self._build_point(
                    asset_id,
                    timestamp,
                    sample["name"],
                    float(sample["value"]),
                    unit=sample.get("unit"),
                )
            )

        return expanded_points

    def _build_point(
        self,
        asset_id: str,
        timestamp: datetime,
        metric_name: str,
        metric_value: float,
        unit: Optional[str],
    ) -> Dict[str, Any]:
        canonical_name = self.normalizer.normalize_metric_name(metric_name)
        normalized_value = self._normalize_value(canonical_name, metric_value, unit)
        return {
            "asset_id": asset_id,
            "timestamp": timestamp,
            "metric_name": canonical_name,
            "metric_value": normalized_value,
        }

    def _normalize_value(self, signal_key: str, value: float, unit: Optional[str]) -> float:
        """Normalize common collector units into the engine's expected ranges."""
        normalized_unit = (unit or "").strip().lower()

        if signal_key in self.PERCENT_SIGNALS:
            if normalized_unit in {"ratio", "1", "fraction"} or (not normalized_unit and 0.0 <= value <= 1.0):
                return value * 100.0

        if signal_key in self.LATENCY_SIGNALS:
            if normalized_unit in {"s", "sec", "second", "seconds"}:
                return value * 1000.0
            if normalized_unit in {"us", "microsecond", "microseconds"}:
                return value / 1000.0
            if normalized_unit in {"ns", "nanosecond", "nanoseconds"}:
                return value / 1_000_000.0

        if signal_key in self.BYTES_TO_MB_SIGNALS and normalized_unit in {"b", "byte", "bytes", "by"}:
            return value / (1024.0 * 1024.0)

        if signal_key in self.BYTES_TO_PERCENT_SIGNALS and normalized_unit in {"ratio", "1", "fraction"}:
            return value * 100.0

        if signal_key in self.DAY_SIGNALS and normalized_unit in {"h", "hr", "hour", "hours"}:
            return value / 24.0

        return value


_telemetry_adapter_service: Optional[TelemetryAdapterService] = None


def get_telemetry_adapter() -> TelemetryAdapterService:
    """Get the singleton telemetry adapter service."""
    global _telemetry_adapter_service
    if _telemetry_adapter_service is None:
        _telemetry_adapter_service = TelemetryAdapterService()
    return _telemetry_adapter_service
