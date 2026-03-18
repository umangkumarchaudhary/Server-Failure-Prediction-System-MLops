"""Automated alert sync for pre-failure risk assessments."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional, Sequence, Tuple

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Alert, Asset, ChangeEvent, Metric, Prediction
from app.services.change_intelligence import get_change_intelligence
from app.services.notification_orchestrator import get_notification_orchestrator
from app.services.risk_engine import get_risk_engine


RISK_ALERT_SOURCE = "risk-engine"
logger = logging.getLogger(__name__)


class RiskAlertService:
    """Create, update, and resolve alerts from the live risk engine."""

    async def sync_for_assets(
        self,
        db: AsyncSession,
        tenant_id: str,
        asset_ids: Optional[Sequence[str]] = None,
        hours: int = 72,
    ) -> Dict[str, object]:
        """Synchronize pre-failure alerts for the requested tenant scope."""
        assets_query = select(Asset).where(Asset.tenant_id == tenant_id)
        if asset_ids:
            assets_query = assets_query.where(Asset.id.in_(list(asset_ids)))

        assets_result = await db.execute(assets_query.order_by(Asset.name.asc()))
        assets = list(assets_result.scalars().all())
        if not assets:
            return {
                "generated_at": datetime.utcnow().isoformat(),
                "processed_assets": 0,
                "assets_with_telemetry": 0,
                "warning_assets": 0,
                "critical_assets": 0,
                "alerts_created": 0,
                "alerts_updated": 0,
                "alerts_resolved": 0,
                "message": "No assets matched the requested scope.",
            }

        scoped_asset_ids = [str(asset.id) for asset in assets]
        metrics_by_asset = await self._fetch_metrics(db, tenant_id, scoped_asset_ids, hours)
        predictions_by_asset = await self._fetch_predictions(db, tenant_id, scoped_asset_ids, hours)
        global_changes, changes_by_asset = await self._fetch_changes(db, tenant_id, scoped_asset_ids, hours)
        alerts_by_asset = await self._fetch_open_alerts(db, tenant_id, scoped_asset_ids)

        asset_name_lookup = {str(asset.id): asset.name for asset in assets}
        change_intelligence = get_change_intelligence()
        risk_engine = get_risk_engine()
        alerts_created = 0
        alerts_updated = 0
        alerts_resolved = 0
        assets_with_telemetry = 0
        warning_assets = 0
        critical_assets = 0

        for asset in assets:
            asset_key = str(asset.id)
            metric_points = metrics_by_asset.get(asset_key, [])
            prediction_points = predictions_by_asset.get(asset_key, [])
            has_telemetry = bool(metric_points or prediction_points)
            if has_telemetry:
                assets_with_telemetry += 1

            assessment = risk_engine.assess_asset(
                asset_id=asset_key,
                asset_name=asset.name,
                asset_type=asset.type,
                metric_points=metric_points,
                prediction_points=prediction_points,
            )
            assessment = change_intelligence.enrich_asset_assessment(
                assessment,
                [*changes_by_asset.get(asset_key, []), *global_changes],
                asset_name_lookup=asset_name_lookup,
            )

            if has_telemetry:
                asset.risk_level = assessment["risk_level"]
                asset.health_score = round(max(0.0, 100.0 - float(assessment["risk_score"])), 1)

            if assessment["risk_level"] == "warning":
                warning_assets += 1
            elif assessment["risk_level"] == "critical":
                critical_assets += 1

            open_alerts = alerts_by_asset.get(asset_key, [])
            primary_alert = open_alerts[0] if open_alerts else None
            duplicate_alerts = open_alerts[1:]

            for duplicate in duplicate_alerts:
                duplicate.status = "resolved"
                alerts_resolved += 1

            if not has_telemetry:
                continue

            if assessment["risk_level"] == "normal":
                if primary_alert is not None:
                    primary_alert.status = "resolved"
                    primary_alert.agent_suggestion = "Recent telemetry moved back into a healthy range."
                    alerts_resolved += 1
                    await db.flush()
                    await self._notify_resolved_alert(
                        tenant_id,
                        asset,
                        primary_alert,
                        assessment,
                    )
                continue

            severity = "critical" if assessment["risk_level"] == "critical" else "warning"
            message = self._build_message(asset.name, assessment)
            suggestion = (
                self._build_suggestion(assessment)
            )

            if primary_alert is None:
                alert = Alert(
                    tenant_id=tenant_id,
                    asset_id=asset_key,
                    severity=severity,
                    message=message,
                    agent_suggestion=suggestion,
                    channel=RISK_ALERT_SOURCE,
                    status="active",
                    triggered_at=datetime.utcnow(),
                )
                db.add(alert)
                alerts_created += 1
                await db.flush()
                await self._notify_created_alert(
                    tenant_id,
                    asset,
                    alert,
                    assessment,
                    escalated_to_critical=severity == "critical",
                )
                continue

            changed = False
            previous_severity = primary_alert.severity
            if primary_alert.severity != severity:
                primary_alert.severity = severity
                changed = True
            if primary_alert.message != message:
                primary_alert.message = message
                changed = True
            if primary_alert.agent_suggestion != suggestion:
                primary_alert.agent_suggestion = suggestion
                changed = True
            if primary_alert.channel != RISK_ALERT_SOURCE:
                primary_alert.channel = RISK_ALERT_SOURCE
                changed = True
            if previous_severity != "critical" and severity == "critical" and primary_alert.status == "acknowledged":
                primary_alert.status = "active"
                changed = True

            if changed:
                primary_alert.triggered_at = datetime.utcnow()
                alerts_updated += 1
                await db.flush()
                await self._notify_created_alert(
                    tenant_id,
                    asset,
                    primary_alert,
                    assessment,
                    escalated_to_critical=previous_severity != "critical" and severity == "critical",
                )

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "processed_assets": len(assets),
            "assets_with_telemetry": assets_with_telemetry,
            "warning_assets": warning_assets,
            "critical_assets": critical_assets,
            "alerts_created": alerts_created,
            "alerts_updated": alerts_updated,
            "alerts_resolved": alerts_resolved,
            "message": self._build_summary_message(
                len(assets),
                assets_with_telemetry,
                critical_assets,
                warning_assets,
                alerts_created,
                alerts_updated,
                alerts_resolved,
            ),
        }

    async def _fetch_metrics(
        self,
        db: AsyncSession,
        tenant_id: str,
        asset_ids: Sequence[str],
        hours: int,
    ) -> Dict[str, List[Dict[str, object]]]:
        since = datetime.utcnow() - timedelta(hours=hours)
        result = await db.execute(
            select(Metric.asset_id, Metric.timestamp, Metric.metric_name, Metric.metric_value)
            .where(
                Metric.tenant_id == tenant_id,
                Metric.asset_id.in_(list(asset_ids)),
                Metric.timestamp >= since,
            )
            .order_by(Metric.timestamp.asc())
        )

        rows: Dict[str, List[Dict[str, object]]] = defaultdict(list)
        for row in result.all():
            rows[str(row.asset_id)].append(
                {
                    "asset_id": str(row.asset_id),
                    "timestamp": row.timestamp,
                    "metric_name": row.metric_name,
                    "metric_value": row.metric_value,
                }
            )
        return rows

    async def _fetch_predictions(
        self,
        db: AsyncSession,
        tenant_id: str,
        asset_ids: Sequence[str],
        hours: int,
    ) -> Dict[str, List[Dict[str, object]]]:
        since = datetime.utcnow() - timedelta(hours=hours)
        result = await db.execute(
            select(
                Prediction.asset_id,
                Prediction.timestamp,
                Prediction.anomaly_score,
                Prediction.rul_estimate,
            )
            .where(
                Prediction.tenant_id == tenant_id,
                Prediction.asset_id.in_(list(asset_ids)),
                Prediction.timestamp >= since,
            )
            .order_by(Prediction.timestamp.asc())
        )

        rows: Dict[str, List[Dict[str, object]]] = defaultdict(list)
        for row in result.all():
            rows[str(row.asset_id)].append(
                {
                    "asset_id": str(row.asset_id),
                    "timestamp": row.timestamp,
                    "anomaly_score": row.anomaly_score,
                    "rul_estimate": row.rul_estimate,
                }
            )
        return rows

    async def _fetch_open_alerts(
        self,
        db: AsyncSession,
        tenant_id: str,
        asset_ids: Sequence[str],
    ) -> Dict[str, List[Alert]]:
        result = await db.execute(
            select(Alert)
            .where(
                Alert.tenant_id == tenant_id,
                Alert.asset_id.in_(list(asset_ids)),
                Alert.channel == RISK_ALERT_SOURCE,
                Alert.status.in_(("active", "acknowledged")),
            )
            .order_by(Alert.triggered_at.desc())
        )

        rows: Dict[str, List[Alert]] = defaultdict(list)
        for alert in result.scalars().all():
            rows[str(alert.asset_id)].append(alert)
        return rows

    async def _fetch_changes(
        self,
        db: AsyncSession,
        tenant_id: str,
        asset_ids: Sequence[str],
        hours: int,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
        since = datetime.utcnow() - timedelta(hours=hours)
        query = (
            select(ChangeEvent)
            .where(
                ChangeEvent.tenant_id == tenant_id,
                ChangeEvent.timestamp >= since,
                or_(
                    ChangeEvent.asset_id.is_(None),
                    ChangeEvent.asset_id.in_(list(asset_ids)),
                ),
            )
            .order_by(ChangeEvent.timestamp.desc())
        )
        result = await db.execute(query)
        global_changes: List[Dict[str, Any]] = []
        scoped_changes: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for event in result.scalars().all():
            payload = {
                "id": event.id,
                "asset_id": str(event.asset_id) if event.asset_id else None,
                "timestamp": event.timestamp,
                "change_type": event.change_type,
                "title": event.title,
                "summary": event.summary,
                "source": event.source,
                "severity": event.severity,
                "version": event.version,
                "extra_data": event.extra_data,
            }
            if event.asset_id is None:
                global_changes.append(payload)
            else:
                scoped_changes[str(event.asset_id)].append(payload)

        return global_changes, scoped_changes

    def _build_message(self, asset_name: str, assessment: Dict[str, object]) -> str:
        message = (
            f"Early warning: {asset_name} may fail within {assessment['forecast_window']} "
            f"(risk score {assessment['risk_score']})."
        )
        likely_causes = assessment.get("likely_causes") or []
        if likely_causes:
            message += f" Likely related change: {likely_causes[0]}."
        return message

    def _build_suggestion(self, assessment: Dict[str, Any]) -> str:
        recommendations = assessment.get("recommended_actions") or []
        likely_causes = assessment.get("likely_causes") or []
        lead = recommendations[0] if recommendations else assessment.get("summary", "Review the latest risk signals.")
        if likely_causes:
            return f"{lead} Check {likely_causes[0]} first."
        return str(lead)

    def _build_summary_message(
        self,
        processed_assets: int,
        assets_with_telemetry: int,
        critical_assets: int,
        warning_assets: int,
        alerts_created: int,
        alerts_updated: int,
        alerts_resolved: int,
    ) -> str:
        return (
            f"Assessed {processed_assets} assets, found telemetry for {assets_with_telemetry}, "
            f"and now track {critical_assets} critical plus {warning_assets} warning assets. "
            f"Alert sync created {alerts_created}, updated {alerts_updated}, and resolved {alerts_resolved} alerts."
        )

    async def _notify_created_alert(
        self,
        tenant_id: str,
        asset: Asset,
        alert: Alert,
        assessment: Dict[str, Any],
        escalated_to_critical: bool,
    ) -> None:
        payload = self._notification_payload(asset, alert, assessment)
        orchestrator = get_notification_orchestrator()
        try:
            await orchestrator.notify_alert(tenant_id, payload)
            if escalated_to_critical:
                await orchestrator.notify_asset_critical(
                    tenant_id,
                    str(asset.id),
                    payload,
                )
        except Exception as exc:  # pragma: no cover - defensive guard around outbound I/O
            logger.warning("Failed to send risk alert notifications: %s", exc)

    async def _notify_resolved_alert(
        self,
        tenant_id: str,
        asset: Asset,
        alert: Alert,
        assessment: Dict[str, Any],
    ) -> None:
        payload = self._notification_payload(asset, alert, assessment)
        orchestrator = get_notification_orchestrator()
        try:
            await orchestrator.notify_alert_resolved(tenant_id, payload)
        except Exception as exc:  # pragma: no cover - defensive guard around outbound I/O
            logger.warning("Failed to send risk alert resolution notifications: %s", exc)

    def _notification_payload(
        self,
        asset: Asset,
        alert: Alert,
        assessment: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "id": alert.id,
            "asset_id": str(asset.id),
            "asset_name": asset.name,
            "severity": alert.severity,
            "status": alert.status,
            "message": alert.message,
            "agent_suggestion": alert.agent_suggestion,
            "forecast_window": assessment.get("forecast_window"),
            "risk_score": assessment.get("risk_score"),
            "risk_level": assessment.get("risk_level"),
            "likely_causes": assessment.get("likely_causes", []),
            "recent_changes": assessment.get("recent_changes", []),
        }


_risk_alert_service: Optional[RiskAlertService] = None


def get_risk_alert_service() -> RiskAlertService:
    """Get the singleton risk alert service."""
    global _risk_alert_service
    if _risk_alert_service is None:
        _risk_alert_service = RiskAlertService()
    return _risk_alert_service
