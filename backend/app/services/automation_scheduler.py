"""Background automation for recurring risk sync and drift monitoring."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from time import perf_counter
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd
from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session_maker
from app.models import Asset, Metric, Prediction, Tenant
from app.services.notification_orchestrator import NotificationOrchestrator, get_notification_orchestrator
from app.services.risk_alert_service import RiskAlertService, get_risk_alert_service
from app.services.telemetry_normalizer import TelemetryNormalizer, get_telemetry_normalizer
from ml.guard.drift import DriftMonitor


logger = logging.getLogger(__name__)


@dataclass
class AutomationJobState:
    """Mutable status for a scheduled automation job."""

    job_key: str
    label: str
    interval_seconds: int
    last_status: str = "idle"
    last_started_at: Optional[datetime] = None
    last_finished_at: Optional[datetime] = None
    last_duration_ms: Optional[int] = None
    last_error: Optional[str] = None
    last_summary: Dict[str, Any] = field(default_factory=dict)
    total_runs: int = 0
    success_runs: int = 0
    failure_runs: int = 0
    is_running: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize status for API responses."""
        return {
            "job_key": self.job_key,
            "label": self.label,
            "interval_seconds": self.interval_seconds,
            "last_status": self.last_status,
            "last_started_at": self.last_started_at.isoformat() if self.last_started_at else None,
            "last_finished_at": self.last_finished_at.isoformat() if self.last_finished_at else None,
            "last_duration_ms": self.last_duration_ms,
            "last_error": self.last_error,
            "last_summary": self.last_summary,
            "total_runs": self.total_runs,
            "success_runs": self.success_runs,
            "failure_runs": self.failure_runs,
            "is_running": self.is_running,
        }


class AutomationSchedulerService:
    """Recurring background automation for risk sync and drift checks."""

    def __init__(
        self,
        risk_alert_service: Optional[RiskAlertService] = None,
        notification_orchestrator: Optional[NotificationOrchestrator] = None,
        telemetry_normalizer: Optional[TelemetryNormalizer] = None,
        session_factory=async_session_maker,
        enabled: Optional[bool] = None,
        risk_sync_interval_seconds: Optional[int] = None,
        drift_check_interval_seconds: Optional[int] = None,
    ):
        self.risk_alert_service = risk_alert_service or get_risk_alert_service()
        self.notification_orchestrator = notification_orchestrator or get_notification_orchestrator()
        self.telemetry_normalizer = telemetry_normalizer or get_telemetry_normalizer()
        self.session_factory = session_factory
        self.enabled = settings.AUTOMATION_ENABLED if enabled is None else enabled
        self.notify_on_drift = settings.AUTOMATION_NOTIFY_ON_DRIFT
        self.risk_lookback_hours = settings.AUTOMATION_RISK_LOOKBACK_HOURS
        self.metric_limit = settings.AUTOMATION_DRIFT_METRIC_LIMIT
        self.prediction_limit = settings.AUTOMATION_DRIFT_PREDICTION_LIMIT

        self.jobs: Dict[str, AutomationJobState] = {
            "risk_sync": AutomationJobState(
                job_key="risk_sync",
                label="Risk Alert Sync",
                interval_seconds=(
                    risk_sync_interval_seconds
                    if risk_sync_interval_seconds is not None
                    else settings.AUTOMATION_RISK_SYNC_INTERVAL_SECONDS
                ),
            ),
            "drift_monitor": AutomationJobState(
                job_key="drift_monitor",
                label="Drift Monitor",
                interval_seconds=(
                    drift_check_interval_seconds
                    if drift_check_interval_seconds is not None
                    else settings.AUTOMATION_DRIFT_CHECK_INTERVAL_SECONDS
                ),
            ),
        }
        self._job_locks = {job_key: asyncio.Lock() for job_key in self.jobs}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._stop_event = asyncio.Event()
        self._started_at: Optional[datetime] = None
        self._tenant_drift_state: Dict[str, Dict[str, Any]] = {}

    async def start(self) -> None:
        """Start recurring automation jobs."""
        if self._tasks:
            return

        self._started_at = datetime.utcnow()
        self._stop_event = asyncio.Event()

        if not self.enabled:
            for state in self.jobs.values():
                state.last_status = "disabled"
            logger.info("Background automation is disabled by configuration.")
            return

        for job_key in self.jobs:
            self._tasks[job_key] = asyncio.create_task(
                self._job_loop(job_key),
                name=f"automation-{job_key}",
            )
        logger.info("Background automation scheduler started with %d jobs.", len(self._tasks))

    async def stop(self) -> None:
        """Stop recurring automation jobs."""
        self._stop_event.set()
        tasks = list(self._tasks.values())
        self._tasks.clear()
        if tasks:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("Background automation scheduler stopped.")

    def status(self) -> Dict[str, Any]:
        """Return the current scheduler status."""
        return {
            "enabled": self.enabled,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "running_jobs": sum(1 for state in self.jobs.values() if state.is_running),
            "jobs": [state.to_dict() for state in self.jobs.values()],
        }

    async def run_now(self, job_key: str = "all") -> Dict[str, Any]:
        """Trigger one or all automation jobs immediately."""
        target_jobs = list(self.jobs) if job_key == "all" else [job_key]
        invalid_jobs = [key for key in target_jobs if key not in self.jobs]
        if invalid_jobs:
            raise ValueError(f"Unsupported automation job(s): {', '.join(invalid_jobs)}")

        for key in target_jobs:
            await self._run_job(key, triggered_by="manual")

        status = self.status()
        selected_jobs = [job for job in status["jobs"] if job["job_key"] in target_jobs]
        overall_status = "completed"
        if any(job["last_status"] in {"error", "degraded"} for job in selected_jobs):
            overall_status = "completed_with_errors"

        return {
            "triggered_at": datetime.utcnow().isoformat(),
            "job_key": job_key,
            "status": overall_status,
            "jobs": selected_jobs,
        }

    async def _job_loop(self, job_key: str) -> None:
        """Run a job immediately and then on a fixed interval until stopped."""
        interval_seconds = self.jobs[job_key].interval_seconds

        while not self._stop_event.is_set():
            await self._run_job(job_key, triggered_by="scheduler")
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=interval_seconds)
            except asyncio.TimeoutError:
                continue

    async def _run_job(self, job_key: str, triggered_by: str) -> Dict[str, Any]:
        """Execute a single automation job and update its status."""
        state = self.jobs[job_key]
        async with self._job_locks[job_key]:
            state.is_running = True
            state.total_runs += 1
            state.last_started_at = datetime.utcnow()
            state.last_finished_at = None
            state.last_duration_ms = None
            state.last_error = None
            state.last_status = "running"
            started = perf_counter()

            try:
                if job_key == "risk_sync":
                    summary = await self._run_risk_sync_job()
                elif job_key == "drift_monitor":
                    summary = await self._run_drift_monitor_job()
                else:  # pragma: no cover - protected by run_now validation
                    raise ValueError(f"Unknown automation job: {job_key}")

                state.last_summary = summary
                if summary.get("errors"):
                    state.last_status = "degraded"
                else:
                    state.last_status = "success"
                state.success_runs += 1
                return summary
            except Exception as exc:  # pragma: no cover - defensive scheduler guard
                logger.exception("Automation job %s failed (%s).", job_key, triggered_by)
                state.last_summary = {}
                state.last_status = "error"
                state.last_error = str(exc)
                state.failure_runs += 1
                return {"message": str(exc), "errors": [{"job_key": job_key, "error": str(exc)}]}
            finally:
                state.is_running = False
                state.last_finished_at = datetime.utcnow()
                state.last_duration_ms = int((perf_counter() - started) * 1000)

    async def _run_risk_sync_job(self) -> Dict[str, Any]:
        """Recalculate risk and automated alerts across all tenants."""
        tenants = await self._fetch_tenants()
        summary = {
            "tenants_processed": len(tenants),
            "tenants_succeeded": 0,
            "tenants_failed": 0,
            "processed_assets": 0,
            "assets_with_telemetry": 0,
            "warning_assets": 0,
            "critical_assets": 0,
            "alerts_created": 0,
            "alerts_updated": 0,
            "alerts_resolved": 0,
            "errors": [],
        }

        for tenant in tenants:
            try:
                result = await self._run_risk_sync_for_tenant(tenant["id"])
                summary["tenants_succeeded"] += 1
                summary["processed_assets"] += int(result.get("processed_assets", 0))
                summary["assets_with_telemetry"] += int(result.get("assets_with_telemetry", 0))
                summary["warning_assets"] += int(result.get("warning_assets", 0))
                summary["critical_assets"] += int(result.get("critical_assets", 0))
                summary["alerts_created"] += int(result.get("alerts_created", 0))
                summary["alerts_updated"] += int(result.get("alerts_updated", 0))
                summary["alerts_resolved"] += int(result.get("alerts_resolved", 0))
            except Exception as exc:  # pragma: no cover - defensive per-tenant guard
                logger.warning("Risk sync failed for tenant %s: %s", tenant["id"], exc)
                summary["tenants_failed"] += 1
                summary["errors"].append({"tenant_id": tenant["id"], "error": str(exc)})

        summary["message"] = (
            f"Processed {summary['tenants_processed']} tenants and synced "
            f"{summary['processed_assets']} assets. Created {summary['alerts_created']}, "
            f"updated {summary['alerts_updated']}, and resolved {summary['alerts_resolved']} alerts."
        )
        return summary

    async def _run_drift_monitor_job(self) -> Dict[str, Any]:
        """Run periodic tenant-wide drift checks and notify on new drift signals."""
        tenants = await self._fetch_tenants()
        summary = {
            "tenants_processed": len(tenants),
            "tenants_succeeded": 0,
            "tenants_failed": 0,
            "input_drift_tenants": 0,
            "prediction_drift_tenants": 0,
            "notifications_sent": 0,
            "errors": [],
        }

        for tenant in tenants:
            try:
                result = await self._run_drift_check_for_tenant(tenant["id"])
                summary["tenants_succeeded"] += 1
                if result["data_drift"]["drift_detected"]:
                    summary["input_drift_tenants"] += 1
                if result["prediction_drift"]["drift_detected"]:
                    summary["prediction_drift_tenants"] += 1
                summary["notifications_sent"] += int(result.get("notifications_sent", 0))
            except Exception as exc:  # pragma: no cover - defensive per-tenant guard
                logger.warning("Drift monitor failed for tenant %s: %s", tenant["id"], exc)
                summary["tenants_failed"] += 1
                summary["errors"].append({"tenant_id": tenant["id"], "error": str(exc)})

        summary["message"] = (
            f"Checked drift across {summary['tenants_processed']} tenants. "
            f"Detected input drift for {summary['input_drift_tenants']} and prediction drift "
            f"for {summary['prediction_drift_tenants']} tenants."
        )
        return summary

    async def _fetch_tenants(self) -> List[Dict[str, str]]:
        """Fetch all tenants that should participate in automation."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(Tenant.id, Tenant.name).order_by(Tenant.name.asc())
            )
            return [{"id": str(row.id), "name": row.name} for row in result.all()]

    async def _run_risk_sync_for_tenant(self, tenant_id: str) -> Dict[str, Any]:
        """Run risk sync in an isolated session for a single tenant."""
        async with self.session_factory() as session:
            try:
                result = await self.risk_alert_service.sync_for_assets(
                    session,
                    tenant_id=tenant_id,
                    hours=self.risk_lookback_hours,
                )
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise

    async def _run_drift_check_for_tenant(self, tenant_id: str) -> Dict[str, Any]:
        """Build rolling drift summaries for a tenant and notify when state changes."""
        async with self.session_factory() as session:
            metric_rows = await self._fetch_metric_rows(session, tenant_id)
            prediction_rows = await self._fetch_prediction_rows(session, tenant_id)
            asset_count = await self._count_assets(session, tenant_id)

        metric_frame = self._build_metric_frame(metric_rows)
        prediction_frame = self._build_prediction_frame(prediction_rows)

        data_drift = self._summarize_drift(
            kind="data",
            frame=metric_frame,
            insufficient_message="Need more recent metric windows before input drift can be assessed.",
        )
        prediction_drift = self._summarize_drift(
            kind="prediction",
            frame=prediction_frame,
            insufficient_message="Need more prediction history before output drift can be assessed.",
        )

        notifications_sent = 0
        snapshot_signature = {
            "data": tuple(sorted(data_drift["drifted_features"])),
            "prediction": tuple(sorted(prediction_drift["drifted_features"])),
        }
        previous_snapshot = self._tenant_drift_state.get(tenant_id)
        should_notify = (
            self.notify_on_drift
            and (data_drift["drift_detected"] or prediction_drift["drift_detected"])
            and snapshot_signature != previous_snapshot
        )
        if should_notify:
            await self.notification_orchestrator.notify_drift(
                tenant_id,
                {
                    "tenant_id": tenant_id,
                    "generated_at": datetime.utcnow().isoformat(),
                    "monitored_assets": asset_count,
                    "data_drift": data_drift,
                    "prediction_drift": prediction_drift,
                },
            )
            notifications_sent = 1

        self._tenant_drift_state[tenant_id] = snapshot_signature
        return {
            "tenant_id": tenant_id,
            "monitored_assets": asset_count,
            "data_drift": data_drift,
            "prediction_drift": prediction_drift,
            "notifications_sent": notifications_sent,
        }

    async def _count_assets(self, session, tenant_id: str) -> int:
        """Count assets for a tenant."""
        result = await session.execute(
            select(Asset.id).where(Asset.tenant_id == tenant_id)
        )
        return len(result.all())

    async def _fetch_metric_rows(self, session, tenant_id: str) -> List[Any]:
        """Fetch recent metric rows for a tenant."""
        result = await session.execute(
            select(Metric.asset_id, Metric.timestamp, Metric.metric_name, Metric.metric_value)
            .where(Metric.tenant_id == tenant_id)
            .order_by(Metric.timestamp.desc())
            .limit(self.metric_limit)
        )
        return result.all()

    async def _fetch_prediction_rows(self, session, tenant_id: str) -> List[Any]:
        """Fetch recent prediction rows for a tenant."""
        result = await session.execute(
            select(
                Prediction.asset_id,
                Prediction.timestamp,
                Prediction.anomaly_score,
                Prediction.rul_estimate,
            )
            .where(Prediction.tenant_id == tenant_id)
            .order_by(Prediction.timestamp.desc())
            .limit(self.prediction_limit)
        )
        return result.all()

    def _build_metric_frame(self, metric_rows: Sequence[Any]) -> pd.DataFrame:
        """Pivot tall metric rows into a wide feature matrix."""
        if not metric_rows:
            return pd.DataFrame()

        records = [
            {
                "asset_id": str(row.asset_id),
                "timestamp": row.timestamp,
                "metric_name": self.telemetry_normalizer.normalize_metric_name(row.metric_name),
                "metric_value": row.metric_value,
            }
            for row in metric_rows
        ]
        frame = pd.DataFrame(records)
        if frame.empty:
            return frame

        pivoted = (
            frame.pivot_table(
                index=["asset_id", "timestamp"],
                columns="metric_name",
                values="metric_value",
                aggfunc="mean",
            )
            .reset_index()
            .sort_values("timestamp")
            .reset_index(drop=True)
        )
        pivoted.columns.name = None
        return pivoted

    def _build_prediction_frame(self, prediction_rows: Sequence[Any]) -> pd.DataFrame:
        """Create a prediction matrix for rolling drift checks."""
        if not prediction_rows:
            return pd.DataFrame()

        frame = pd.DataFrame(
            [
                {
                    "asset_id": str(row.asset_id),
                    "timestamp": row.timestamp,
                    "anomaly_score": row.anomaly_score,
                    "rul_estimate": row.rul_estimate,
                }
                for row in prediction_rows
            ]
        )
        if frame.empty:
            return frame

        return frame.sort_values("timestamp").reset_index(drop=True)

    def _split_windows(
        self,
        frame: pd.DataFrame,
        max_rows: int = 240,
        min_window: int = 12,
    ):
        """Split a time-ordered frame into baseline and current windows."""
        if frame.empty:
            return None, None

        working = frame.copy()
        if "timestamp" in working.columns:
            working = working.sort_values("timestamp")

        working = working.tail(max_rows).reset_index(drop=True)
        numeric_cols = [
            column
            for column in working.select_dtypes(include=np.number).columns.tolist()
            if column != "timestamp"
        ]
        if not numeric_cols:
            return None, None

        numeric_frame = working[numeric_cols].dropna(how="all")
        if len(numeric_frame) < min_window * 2:
            return None, None

        current_window_size = max(min_window, min(48, len(numeric_frame) // 3))
        if len(numeric_frame) - current_window_size < min_window:
            current_window_size = len(numeric_frame) // 2

        reference_frame = numeric_frame.iloc[:-current_window_size]
        current_frame = numeric_frame.iloc[-current_window_size:]

        if len(reference_frame) < min_window or len(current_frame) < min_window:
            return None, None

        return reference_frame, current_frame

    def _summarize_drift(
        self,
        kind: str,
        frame: pd.DataFrame,
        insufficient_message: str,
    ) -> Dict[str, Any]:
        """Run a rolling drift check and normalize the response shape."""
        reference_frame, current_frame = self._split_windows(frame)
        if reference_frame is None or current_frame is None:
            return {
                "kind": kind,
                "status": "insufficient_data",
                "drift_detected": False,
                "drifted_features": [],
                "drifted_count": 0,
                "total_columns": 0,
                "share_of_drifted_columns": 0.0,
                "sample_size": 0,
                "message": insufficient_message,
            }

        report = DriftMonitor(reference_data=reference_frame).detect_drift(current_frame)
        if report.get("error"):
            return {
                "kind": kind,
                "status": "insufficient_data",
                "drift_detected": False,
                "drifted_features": [],
                "drifted_count": 0,
                "total_columns": 0,
                "share_of_drifted_columns": 0.0,
                "sample_size": len(current_frame),
                "message": report["error"],
            }

        summary = report.get("summary", {})
        drifted_features = list(report.get("drifted_columns", {}).keys())
        drift_detected = bool(report.get("drift_detected"))
        status = "drift_detected" if drift_detected else "healthy"

        if drift_detected:
            message = (
                f"Detected drift in {len(drifted_features)} of {summary.get('total_columns', 0)} "
                f"{'prediction signals' if kind == 'prediction' else 'input features'}."
            )
        else:
            message = "Latest window looks stable against the tenant's recent baseline."

        return {
            "kind": kind,
            "status": status,
            "drift_detected": drift_detected,
            "drifted_features": drifted_features,
            "drifted_count": summary.get("drifted_count", 0),
            "total_columns": summary.get("total_columns", 0),
            "share_of_drifted_columns": summary.get("share_of_drifted_columns", 0.0),
            "sample_size": len(current_frame),
            "message": message,
        }


_automation_scheduler_service: Optional[AutomationSchedulerService] = None


def get_automation_scheduler() -> AutomationSchedulerService:
    """Get the singleton automation scheduler."""
    global _automation_scheduler_service
    if _automation_scheduler_service is None:
        _automation_scheduler_service = AutomationSchedulerService()
    return _automation_scheduler_service
