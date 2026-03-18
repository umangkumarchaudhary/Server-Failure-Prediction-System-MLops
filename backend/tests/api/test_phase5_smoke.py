"""Focused smoke tests for the Phase 5 background automation scheduler."""
import asyncio
import os
import sys

os.environ["DEBUG"] = "false"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.schemas import AutomationRunResponse, AutomationStatusResponse
from app.services.automation_scheduler import AutomationSchedulerService


class AutomationSchedulerStub(AutomationSchedulerService):
    """Small automation scheduler variant with deterministic fake job outputs."""

    def __init__(self):
        super().__init__(enabled=True, risk_sync_interval_seconds=1, drift_check_interval_seconds=1)
        self.risk_runs = 0
        self.drift_runs = 0

    async def _fetch_tenants(self):
        return [
            {"id": "tenant-1", "name": "Acme"},
            {"id": "tenant-2", "name": "Beta"},
        ]

    async def _run_risk_sync_for_tenant(self, tenant_id: str):
        self.risk_runs += 1
        return {
            "processed_assets": 2 if tenant_id == "tenant-1" else 1,
            "assets_with_telemetry": 2 if tenant_id == "tenant-1" else 1,
            "warning_assets": 1 if tenant_id == "tenant-1" else 0,
            "critical_assets": 0 if tenant_id == "tenant-1" else 1,
            "alerts_created": 1,
            "alerts_updated": 0,
            "alerts_resolved": 0,
        }

    async def _run_drift_check_for_tenant(self, tenant_id: str):
        self.drift_runs += 1
        if tenant_id == "tenant-1":
            return {
                "tenant_id": tenant_id,
                "monitored_assets": 2,
                "data_drift": {
                    "kind": "data",
                    "status": "drift_detected",
                    "drift_detected": True,
                    "drifted_features": ["cpu_pressure"],
                    "message": "Input drift detected.",
                },
                "prediction_drift": {
                    "kind": "prediction",
                    "status": "healthy",
                    "drift_detected": False,
                    "drifted_features": [],
                    "message": "Stable.",
                },
                "notifications_sent": 1,
            }
        return {
            "tenant_id": tenant_id,
            "monitored_assets": 1,
            "data_drift": {
                "kind": "data",
                "status": "healthy",
                "drift_detected": False,
                "drifted_features": [],
                "message": "Stable.",
            },
            "prediction_drift": {
                "kind": "prediction",
                "status": "healthy",
                "drift_detected": False,
                "drifted_features": [],
                "message": "Stable.",
            },
            "notifications_sent": 0,
        }


class TestPhase5Smoke:
    """Smoke coverage for background automation scheduling."""

    async def test_manual_run_updates_scheduler_status(self):
        service = AutomationSchedulerStub()

        result = await service.run_now("all")
        status = service.status()

        validated_run = AutomationRunResponse.model_validate(result)
        validated_status = AutomationStatusResponse.model_validate(status)

        assert validated_run.status == "completed"
        assert len(validated_run.jobs) == 2
        assert validated_status.running_jobs == 0
        assert service.risk_runs == 2
        assert service.drift_runs == 2

        risk_job = next(job for job in validated_status.jobs if job.job_key == "risk_sync")
        drift_job = next(job for job in validated_status.jobs if job.job_key == "drift_monitor")

        assert risk_job.last_status == "success"
        assert drift_job.last_status == "success"
        assert risk_job.last_summary["alerts_created"] == 2
        assert drift_job.last_summary["input_drift_tenants"] == 1
        assert drift_job.last_summary["notifications_sent"] == 1

    async def test_start_and_stop_runs_background_loops(self):
        service = AutomationSchedulerStub()
        service.jobs["risk_sync"].interval_seconds = 0.01
        service.jobs["drift_monitor"].interval_seconds = 0.01

        await service.start()
        await asyncio.sleep(0.05)
        await service.stop()

        status = service.status()

        assert service.risk_runs >= 2
        assert service.drift_runs >= 2
        assert status["running_jobs"] == 0
        assert all(not job["is_running"] for job in status["jobs"])


if __name__ == "__main__":
    smoke = TestPhase5Smoke()
    asyncio.run(smoke.test_manual_run_updates_scheduler_status())
    asyncio.run(smoke.test_start_and_stop_runs_background_loops())
