"""
Risk engine for pre-failure early warnings.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from statistics import mean
from typing import Dict, List, Optional, Sequence


@dataclass(frozen=True)
class SignalRule:
    """Definition of a telemetry signal that can contribute to failure risk."""

    signal_key: str
    label: str
    category: str
    aliases: Sequence[str]
    mode: str  # high, low, absolute
    warning_threshold: float
    critical_threshold: float
    weight: float
    recommendation: str


@dataclass
class RiskIndicator:
    """Concrete signal finding for an asset."""

    signal_key: str
    label: str
    category: str
    severity: str
    metric_name: str
    latest_value: float
    threshold: float
    trend: str
    contribution: float
    reason: str
    recommendation: str


class RiskEngine:
    """Hybrid rule and trend-based early warning engine."""

    def __init__(self):
        self.rules: Sequence[SignalRule] = (
            SignalRule(
                signal_key="cpu_pressure",
                label="CPU pressure",
                category="Infrastructure",
                aliases=("cpu_usage", "cpu_percent", "system_cpu", "host_cpu", "container_cpu"),
                mode="high",
                warning_threshold=75.0,
                critical_threshold=90.0,
                weight=12.0,
                recommendation="Scale compute capacity or identify the hottest processes before saturation causes timeouts.",
            ),
            SignalRule(
                signal_key="load_pressure",
                label="System load",
                category="Infrastructure",
                aliases=("load_1m", "load_5m", "system_load", "cpu_load"),
                mode="high",
                warning_threshold=4.0,
                critical_threshold=8.0,
                weight=10.0,
                recommendation="Inspect load spikes, noisy neighbors, or thread pool starvation before the host becomes unresponsive.",
            ),
            SignalRule(
                signal_key="memory_pressure",
                label="Memory pressure",
                category="Infrastructure",
                aliases=("memory_usage", "memory_percent", "ram_usage", "heap_usage_percent"),
                mode="high",
                warning_threshold=80.0,
                critical_threshold=92.0,
                weight=12.0,
                recommendation="Add memory headroom or reduce heap pressure before the service starts evicting or OOM-killing workloads.",
            ),
            SignalRule(
                signal_key="memory_headroom",
                label="Free memory",
                category="Infrastructure",
                aliases=("memory_available_mb", "free_memory_mb", "memory_free_mb"),
                mode="low",
                warning_threshold=2048.0,
                critical_threshold=512.0,
                weight=10.0,
                recommendation="Free memory or rebalance workloads before swap and garbage collection pauses cascade into failures.",
            ),
            SignalRule(
                signal_key="disk_pressure",
                label="Disk usage",
                category="Infrastructure",
                aliases=("disk_usage", "disk_percent", "filesystem_usage", "storage_usage"),
                mode="high",
                warning_threshold=85.0,
                critical_threshold=95.0,
                weight=12.0,
                recommendation="Clear disk pressure or expand storage before writes, logs, or checkpoints begin failing.",
            ),
            SignalRule(
                signal_key="disk_headroom",
                label="Free disk",
                category="Infrastructure",
                aliases=("disk_free_percent", "free_disk_percent", "filesystem_free_percent"),
                mode="low",
                warning_threshold=20.0,
                critical_threshold=10.0,
                weight=10.0,
                recommendation="Recover disk headroom before the system loses space for temp files, WAL, or container layers.",
            ),
            SignalRule(
                signal_key="io_wait",
                label="Disk I/O wait",
                category="Infrastructure",
                aliases=("io_wait", "disk_iowait", "iowait_percent"),
                mode="high",
                warning_threshold=20.0,
                critical_threshold=40.0,
                weight=8.0,
                recommendation="Investigate storage contention and slow volumes before latency spreads to application requests.",
            ),
            SignalRule(
                signal_key="db_latency",
                label="Database latency",
                category="Database",
                aliases=("db_latency_ms", "query_latency_ms", "db_query_ms", "slow_query_ms", "p95_query_ms"),
                mode="high",
                warning_threshold=150.0,
                critical_threshold=400.0,
                weight=14.0,
                recommendation="Review slow queries, indexes, and lock contention before the database becomes the bottleneck.",
            ),
            SignalRule(
                signal_key="db_connections",
                label="DB connections",
                category="Database",
                aliases=("db_connections_percent", "connection_pool_usage", "pool_usage", "db_pool_percent"),
                mode="high",
                warning_threshold=75.0,
                critical_threshold=90.0,
                weight=12.0,
                recommendation="Increase pool headroom or reduce burst traffic before connection exhaustion causes outages.",
            ),
            SignalRule(
                signal_key="error_rate",
                label="Error rate",
                category="Application",
                aliases=("error_rate", "http_5xx_rate", "exception_rate", "failure_rate"),
                mode="high",
                warning_threshold=0.02,
                critical_threshold=0.05,
                weight=18.0,
                recommendation="Trace recent failures and rollback risky changes before customers see a full incident.",
            ),
            SignalRule(
                signal_key="latency",
                label="Request latency",
                category="Application",
                aliases=("response_time_ms", "p95_latency_ms", "latency_ms", "request_latency_ms"),
                mode="high",
                warning_threshold=400.0,
                critical_threshold=1000.0,
                weight=14.0,
                recommendation="Inspect upstream dependencies and saturation before latency crosses your SLO boundary.",
            ),
            SignalRule(
                signal_key="queue_backlog",
                label="Queue backlog",
                category="Application",
                aliases=("queue_depth", "backlog_size", "queue_length"),
                mode="high",
                warning_threshold=100.0,
                critical_threshold=300.0,
                weight=8.0,
                recommendation="Drain the backlog or add workers before delays become visible to users.",
            ),
            SignalRule(
                signal_key="event_loop_lag",
                label="Runtime lag",
                category="Runtime",
                aliases=("event_loop_lag_ms", "loop_lag_ms", "thread_pool_lag_ms"),
                mode="high",
                warning_threshold=50.0,
                critical_threshold=150.0,
                weight=10.0,
                recommendation="Reduce blocking work or increase concurrency before the runtime stops keeping up.",
            ),
            SignalRule(
                signal_key="gc_pause",
                label="GC pause",
                category="Runtime",
                aliases=("gc_pause_ms", "gc_pause_p95_ms"),
                mode="high",
                warning_threshold=50.0,
                critical_threshold=150.0,
                weight=8.0,
                recommendation="Tune memory behavior before long GC pauses degrade throughput or trigger restarts.",
            ),
            SignalRule(
                signal_key="restart_count",
                label="Restart count",
                category="Runtime",
                aliases=("restart_count", "crash_loop_count", "container_restarts"),
                mode="high",
                warning_threshold=1.0,
                critical_threshold=3.0,
                weight=18.0,
                recommendation="Investigate restart loops immediately before the service enters a full crash cycle.",
            ),
            SignalRule(
                signal_key="clock_skew",
                label="Clock drift",
                category="Infrastructure",
                aliases=("clock_skew_ms", "ntp_offset_ms", "time_drift_ms"),
                mode="absolute",
                warning_threshold=200.0,
                critical_threshold=1000.0,
                weight=10.0,
                recommendation="Fix time synchronization before tokens, certificates, and distributed coordination begin failing.",
            ),
            SignalRule(
                signal_key="change_velocity",
                label="Change pressure",
                category="Change",
                aliases=("deploy_change_score", "package_change_score", "runtime_change_score", "config_change_score"),
                mode="high",
                warning_threshold=1.0,
                critical_threshold=2.0,
                weight=10.0,
                recommendation="Pause further changes and compare the latest deploy or config change against the observed regressions.",
            ),
            SignalRule(
                signal_key="cert_expiry",
                label="Certificate runway",
                category="Change",
                aliases=("cert_days_remaining", "secret_days_remaining"),
                mode="low",
                warning_threshold=14.0,
                critical_threshold=3.0,
                weight=6.0,
                recommendation="Rotate expiring credentials before they turn into a preventable outage.",
            ),
            SignalRule(
                signal_key="anomaly_score",
                label="Anomaly score",
                category="Prediction",
                aliases=("anomaly_score",),
                mode="high",
                warning_threshold=0.55,
                critical_threshold=0.8,
                weight=18.0,
                recommendation="Inspect the dominant anomalous signals now to prevent escalation into a customer-visible failure.",
            ),
            SignalRule(
                signal_key="rul_estimate",
                label="Remaining useful life",
                category="Prediction",
                aliases=("rul_estimate",),
                mode="low",
                warning_threshold=72.0,
                critical_threshold=24.0,
                weight=20.0,
                recommendation="Schedule maintenance or failover before the asset runs out of safe operating runway.",
            ),
        )

    def assess_asset(
        self,
        asset_id: str,
        asset_name: str,
        asset_type: str,
        metric_points: Sequence[Dict],
        prediction_points: Sequence[Dict],
    ) -> Dict:
        """Build a risk assessment from recent telemetry for a single asset."""
        indicators: List[RiskIndicator] = []
        has_telemetry = bool(metric_points or prediction_points)
        metric_series = self._group_metric_series(metric_points)

        for metric_name, values in metric_series.items():
            rule = self._find_rule(metric_name)
            if rule is None:
                continue
            indicator = self._evaluate_signal(rule, metric_name, values)
            if indicator is not None:
                indicators.append(indicator)

        prediction_series = self._group_prediction_series(prediction_points)
        for metric_name, values in prediction_series.items():
            rule = self._find_rule(metric_name)
            if rule is None:
                continue
            indicator = self._evaluate_signal(rule, metric_name, values)
            if indicator is not None:
                indicators.append(indicator)

        indicators.sort(key=lambda item: item.contribution, reverse=True)
        risk_score = min(100, round(sum(item.contribution for item in indicators)))
        risk_level = self._risk_level(risk_score)
        forecast_window = self._forecast_window(risk_score, has_telemetry)
        confidence = self._confidence(metric_points, prediction_points, indicators, has_telemetry)
        recommended_actions = self._recommendations(indicators)
        summary = self._summary(asset_name, risk_level, indicators, has_telemetry)

        return {
            "asset_id": asset_id,
            "asset_name": asset_name,
            "asset_type": asset_type,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "confidence": confidence,
            "forecast_window": forecast_window,
            "summary": summary,
            "last_metric_at": self._latest_timestamp(metric_points),
            "last_prediction_at": self._latest_timestamp(prediction_points),
            "top_signals": [indicator.label for indicator in indicators[:3]],
            "recommended_actions": recommended_actions,
            "indicators": [self._indicator_dict(indicator) for indicator in indicators[:6]],
        }

    def assess_fleet(
        self,
        assets: Sequence[Dict],
        metric_points: Sequence[Dict],
        prediction_points: Sequence[Dict],
        limit: int = 5,
    ) -> Dict:
        """Build tenant-level early warning overview across all assets."""
        metrics_by_asset = self._group_by_asset(metric_points)
        predictions_by_asset = self._group_by_asset(prediction_points)

        assessments = [
            self.assess_asset(
                asset_id=str(asset["id"]),
                asset_name=asset["name"],
                asset_type=asset["type"],
                metric_points=metrics_by_asset.get(str(asset["id"]), []),
                prediction_points=predictions_by_asset.get(str(asset["id"]), []),
            )
            for asset in assets
        ]
        assessments.sort(key=lambda item: item["risk_score"], reverse=True)

        monitored_assets = len(assessments)
        critical_assets = len([item for item in assessments if item["risk_level"] == "critical"])
        warning_assets = len([item for item in assessments if item["risk_level"] == "warning"])
        normal_assets = len([item for item in assessments if item["risk_level"] == "normal"])
        average_risk_score = round(
            mean(item["risk_score"] for item in assessments) if assessments else 0.0,
            1,
        )
        highest_risk_score = assessments[0]["risk_score"] if assessments else 0

        signal_counts = Counter()
        signal_labels: Dict[str, str] = {}
        for item in assessments:
            for indicator in item["indicators"]:
                signal_counts[indicator["signal_key"]] += 1
                signal_labels[indicator["signal_key"]] = indicator["label"]

        top_signals = [
            {
                "signal_key": signal_key,
                "label": signal_labels.get(signal_key, signal_key),
                "count": count,
            }
            for signal_key, count in signal_counts.most_common(5)
        ]

        top_assets = [self._summary_asset(item) for item in assessments[:limit]]
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "monitored_assets": monitored_assets,
            "critical_assets": critical_assets,
            "warning_assets": warning_assets,
            "normal_assets": normal_assets,
            "average_risk_score": average_risk_score,
            "highest_risk_score": highest_risk_score,
            "summary": self._fleet_summary(critical_assets, warning_assets, top_assets),
            "assets": top_assets,
            "top_signals": top_signals,
        }

    def _group_metric_series(self, metric_points: Sequence[Dict]) -> Dict[str, List[float]]:
        grouped: Dict[str, List[float]] = defaultdict(list)
        for point in sorted(metric_points, key=lambda item: item["timestamp"]):
            grouped[self._normalize(point["metric_name"])].append(float(point["metric_value"]))
        return grouped

    def _group_prediction_series(self, prediction_points: Sequence[Dict]) -> Dict[str, List[float]]:
        grouped: Dict[str, List[float]] = defaultdict(list)
        for point in sorted(prediction_points, key=lambda item: item["timestamp"]):
            if point.get("anomaly_score") is not None:
                grouped["anomaly_score"].append(float(point["anomaly_score"]))
            if point.get("rul_estimate") is not None:
                grouped["rul_estimate"].append(float(point["rul_estimate"]))
        return grouped

    def _group_by_asset(self, rows: Sequence[Dict]) -> Dict[str, List[Dict]]:
        grouped: Dict[str, List[Dict]] = defaultdict(list)
        for row in rows:
            grouped[str(row["asset_id"])].append(row)
        return grouped

    def _find_rule(self, metric_name: str) -> Optional[SignalRule]:
        normalized = self._normalize(metric_name)
        for rule in self.rules:
            if normalized == rule.signal_key:
                return rule
            if any(self._normalize(alias) in normalized for alias in rule.aliases):
                return rule
        return None

    def _evaluate_signal(self, rule: SignalRule, metric_name: str, values: Sequence[float]) -> Optional[RiskIndicator]:
        if not values:
            return None

        latest_value = float(values[-1])
        risk_strength = self._risk_strength(rule, latest_value)
        if risk_strength <= 0:
            return None

        trend = self._trend(rule.mode, values)
        bonus = 0.0
        if trend == "rising":
            bonus = 0.12
        elif trend == "spiking":
            bonus = 0.2
        elif trend == "falling" and rule.mode == "low":
            bonus = 0.12

        normalized_score = min(1.15, risk_strength + bonus)
        contribution = round(rule.weight * normalized_score, 1)
        severity = "critical" if normalized_score >= 1.0 else "elevated"
        threshold = (
            rule.critical_threshold if severity == "critical" else rule.warning_threshold
        )

        return RiskIndicator(
            signal_key=rule.signal_key,
            label=rule.label,
            category=rule.category,
            severity=severity,
            metric_name=metric_name,
            latest_value=latest_value,
            threshold=threshold,
            trend=trend,
            contribution=contribution,
            reason=self._reason(rule, latest_value, trend, severity),
            recommendation=rule.recommendation,
        )

    def _risk_strength(self, rule: SignalRule, latest_value: float) -> float:
        value = abs(latest_value) if rule.mode == "absolute" else latest_value

        if rule.mode in {"high", "absolute"}:
            if value < rule.warning_threshold:
                return 0.0
            if value >= rule.critical_threshold:
                return 1.0
            span = rule.critical_threshold - rule.warning_threshold
            if span <= 0:
                return 1.0
            return 0.4 + ((value - rule.warning_threshold) / span) * 0.6

        if value > rule.warning_threshold:
            return 0.0
        if value <= rule.critical_threshold:
            return 1.0

        span = rule.warning_threshold - rule.critical_threshold
        if span <= 0:
            return 1.0
        return 0.4 + ((rule.warning_threshold - value) / span) * 0.6

    def _trend(self, mode: str, values: Sequence[float]) -> str:
        if len(values) < 2:
            return "stable"

        history = list(values[:-1])[-5:]
        baseline = mean(history) if history else values[-1]
        latest_value = values[-1]
        if baseline == 0:
            delta_ratio = 0.0 if latest_value == 0 else 1.0
        else:
            delta_ratio = (latest_value - baseline) / abs(baseline)

        if mode in {"high", "absolute"}:
            if delta_ratio >= 0.25:
                return "spiking"
            if delta_ratio >= 0.1:
                return "rising"
            if delta_ratio <= -0.1:
                return "falling"
            return "stable"

        if delta_ratio <= -0.25:
            return "spiking"
        if delta_ratio <= -0.1:
            return "falling"
        if delta_ratio >= 0.1:
            return "rising"
        return "stable"

    def _risk_level(self, risk_score: int) -> str:
        if risk_score >= 70:
            return "critical"
        if risk_score >= 40:
            return "warning"
        return "normal"

    def _forecast_window(self, risk_score: int, has_telemetry: bool) -> str:
        if not has_telemetry:
            return "awaiting telemetry"
        if risk_score >= 85:
            return "next 1 hour"
        if risk_score >= 70:
            return "next 6 hours"
        if risk_score >= 50:
            return "next 24 hours"
        if risk_score >= 30:
            return "next 3 days"
        return "stable"

    def _confidence(
        self,
        metric_points: Sequence[Dict],
        prediction_points: Sequence[Dict],
        indicators: Sequence[RiskIndicator],
        has_telemetry: bool,
    ) -> float:
        if not has_telemetry:
            return 0.12
        coverage = min(1.0, (len(metric_points) / 60.0) + (len(prediction_points) / 20.0))
        signal_bonus = min(0.25, len(indicators) * 0.05)
        return round(min(0.98, 0.35 + (coverage * 0.4) + signal_bonus), 2)

    def _recommendations(self, indicators: Sequence[RiskIndicator]) -> List[str]:
        seen = set()
        recommendations: List[str] = []
        for indicator in indicators:
            if indicator.recommendation in seen:
                continue
            seen.add(indicator.recommendation)
            recommendations.append(indicator.recommendation)
            if len(recommendations) == 4:
                break
        return recommendations

    def _summary(
        self,
        asset_name: str,
        risk_level: str,
        indicators: Sequence[RiskIndicator],
        has_telemetry: bool,
    ) -> str:
        if not has_telemetry:
            return f"Not enough telemetry has arrived yet to estimate pre-failure risk for {asset_name}."
        if not indicators:
            return f"{asset_name} looks stable based on the latest telemetry window."
        top_labels = ", ".join(indicator.label.lower() for indicator in indicators[:2])
        if risk_level == "critical":
            return f"{asset_name} shows a high chance of failure unless {top_labels} are addressed quickly."
        if risk_level == "warning":
            return f"{asset_name} is trending away from healthy behavior due to {top_labels}."
        return f"{asset_name} has light pressure from {top_labels}, but no immediate failure pattern is visible."

    def _fleet_summary(
        self,
        critical_assets: int,
        warning_assets: int,
        top_assets: Sequence[Dict],
    ) -> str:
        if critical_assets:
            lead_asset = top_assets[0]["asset_name"] if top_assets else "the fleet"
            return f"{critical_assets} assets need immediate attention, led by {lead_asset}."
        if warning_assets:
            return f"{warning_assets} assets are trending toward risk and should be reviewed before the next load spike."
        return "No strong pre-failure pattern is visible across the latest telemetry windows."

    def _reason(self, rule: SignalRule, latest_value: float, trend: str, severity: str) -> str:
        threshold = rule.critical_threshold if severity == "critical" else rule.warning_threshold
        return (
            f"{rule.label} is at {latest_value:.2f}, crossing the {threshold:.2f} threshold with a {trend} trend."
        )

    def _latest_timestamp(self, rows: Sequence[Dict]) -> Optional[str]:
        if not rows:
            return None
        latest = max((row["timestamp"] for row in rows if row.get("timestamp") is not None), default=None)
        return latest.isoformat() if latest else None

    def _summary_asset(self, item: Dict) -> Dict:
        return {
            "asset_id": item["asset_id"],
            "asset_name": item["asset_name"],
            "asset_type": item["asset_type"],
            "risk_score": item["risk_score"],
            "risk_level": item["risk_level"],
            "confidence": item["confidence"],
            "forecast_window": item["forecast_window"],
            "summary": item["summary"],
            "last_metric_at": item["last_metric_at"],
            "last_prediction_at": item["last_prediction_at"],
            "top_signals": item["top_signals"],
        }

    def _indicator_dict(self, indicator: RiskIndicator) -> Dict:
        return {
            "signal_key": indicator.signal_key,
            "label": indicator.label,
            "category": indicator.category,
            "severity": indicator.severity,
            "metric_name": indicator.metric_name,
            "latest_value": indicator.latest_value,
            "threshold": indicator.threshold,
            "trend": indicator.trend,
            "contribution": indicator.contribution,
            "reason": indicator.reason,
        }

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


_risk_engine: Optional[RiskEngine] = None


def get_risk_engine() -> RiskEngine:
    """Get the singleton risk engine."""
    global _risk_engine
    if _risk_engine is None:
        _risk_engine = RiskEngine()
    return _risk_engine
