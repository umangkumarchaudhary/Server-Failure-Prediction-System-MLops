"use client";

import { useQuery } from "@tanstack/react-query";
import {
    Activity,
    AlertTriangle,
    ArrowRight,
    Bell,
    Radar,
    Server,
    ShieldAlert,
    TrendingDown,
    TrendingUp,
} from "lucide-react";
import Link from "next/link";

import { alertsApi, dashboardApi, riskApi } from "@/lib/api";

type RiskAsset = {
    asset_id: string;
    asset_name: string;
    asset_type: string;
    risk_score: number;
    risk_level: "normal" | "warning" | "critical";
    confidence: number;
    forecast_window: string;
    summary: string;
    top_signals: string[];
    likely_causes: string[];
    change_correlation_score: number;
};

type ChangeEvent = {
    id: number;
    asset_id?: string | null;
    asset_name?: string | null;
    timestamp: string;
    change_type: string;
    title: string;
    summary?: string | null;
    source?: string | null;
    severity: string;
    version?: string | null;
    correlation_score: number;
};

type RiskOverview = {
    generated_at: string;
    monitored_assets: number;
    critical_assets: number;
    warning_assets: number;
    normal_assets: number;
    average_risk_score: number;
    highest_risk_score: number;
    summary: string;
    change_correlated_assets: number;
    assets: RiskAsset[];
    top_signals: { signal_key: string; label: string; count: number }[];
    recent_changes: ChangeEvent[];
};

function riskBadge(level: RiskAsset["risk_level"]) {
    if (level === "critical") {
        return "bg-red-500/10 text-red-500";
    }
    if (level === "warning") {
        return "bg-amber-500/10 text-amber-500";
    }
    return "bg-emerald-500/10 text-emerald-500";
}

export default function DashboardPage() {
    const { data: stats, isLoading: statsLoading } = useQuery({
        queryKey: ["dashboard-stats"],
        queryFn: () => dashboardApi.getStats().then((res) => res.data),
    });

    const { data: riskOverview, isLoading: riskLoading } = useQuery<RiskOverview>({
        queryKey: ["risk-overview"],
        queryFn: () => riskApi.getOverview({ limit: 5, hours: 72 }).then((res) => res.data),
        refetchInterval: 60_000,
    });

    const { data: alerts } = useQuery({
        queryKey: ["alerts-active"],
        queryFn: () => alertsApi.list({ status: "active", limit: 5 }).then((res) => res.data),
    });

    const statCards = [
        {
            title: "Total Assets",
            value: stats?.total_assets ?? 0,
            icon: Server,
            color: "text-primary",
            bg: "bg-primary/10",
        },
        {
            title: "Healthy",
            value: stats?.healthy_assets ?? 0,
            icon: TrendingUp,
            color: "text-emerald-500",
            bg: "bg-emerald-500/10",
        },
        {
            title: "Warning",
            value: stats?.warning_assets ?? 0,
            icon: AlertTriangle,
            color: "text-amber-500",
            bg: "bg-amber-500/10",
        },
        {
            title: "Critical",
            value: stats?.critical_assets ?? 0,
            icon: TrendingDown,
            color: "text-red-500",
            bg: "bg-red-500/10",
        },
        {
            title: "Active Alerts",
            value: stats?.active_alerts ?? 0,
            icon: Bell,
            color: "text-orange-500",
            bg: "bg-orange-500/10",
        },
        {
            title: "Anomalies (24h)",
            value: stats?.anomalies_24h ?? 0,
            icon: Activity,
            color: "text-purple-500",
            bg: "bg-purple-500/10",
        },
    ];

    return (
        <div className="space-y-8 animate-in">
            <div>
                <h1 className="text-3xl font-bold">Dashboard</h1>
                <p className="mt-1 text-muted-foreground">
                    Live fleet health, pre-failure risk, and active alerts.
                </p>
            </div>

            <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
                {statCards.map((stat) => (
                    <div
                        key={stat.title}
                        className="rounded-xl border border-border bg-card p-4 transition-colors hover:border-primary/50"
                    >
                        <div className={`mb-3 flex h-10 w-10 items-center justify-center rounded-lg ${stat.bg}`}>
                            <stat.icon className={`h-5 w-5 ${stat.color}`} />
                        </div>
                        <p className="text-2xl font-bold">{statsLoading ? "-" : stat.value}</p>
                        <p className="text-sm text-muted-foreground">{stat.title}</p>
                    </div>
                ))}
            </div>

            <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
                <div className="rounded-2xl border border-border bg-card p-6">
                    <div className="flex items-start justify-between gap-4">
                        <div>
                            <div className="flex items-center gap-2 text-sm uppercase tracking-[0.2em] text-muted-foreground">
                                <Radar className="h-4 w-4" />
                                Pre-Failure Outlook
                            </div>
                            <h2 className="mt-3 text-2xl font-semibold">
                                {riskLoading ? "Loading risk engine..." : riskOverview?.summary || "No risk signals yet"}
                            </h2>
                        </div>
                        <Link
                            href="/dashboard/mlops"
                            className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                        >
                            ML Health <ArrowRight className="h-4 w-4" />
                        </Link>
                    </div>

                    <div className="mt-6 grid gap-4 md:grid-cols-5">
                        <div className="rounded-xl bg-background p-4">
                            <p className="text-sm text-muted-foreground">Monitored Assets</p>
                            <p className="mt-2 text-2xl font-bold">{riskOverview?.monitored_assets ?? 0}</p>
                        </div>
                        <div className="rounded-xl bg-background p-4">
                            <p className="text-sm text-muted-foreground">Critical Risk</p>
                            <p className="mt-2 text-2xl font-bold text-red-500">{riskOverview?.critical_assets ?? 0}</p>
                        </div>
                        <div className="rounded-xl bg-background p-4">
                            <p className="text-sm text-muted-foreground">Watchlist</p>
                            <p className="mt-2 text-2xl font-bold text-amber-500">{riskOverview?.warning_assets ?? 0}</p>
                        </div>
                        <div className="rounded-xl bg-background p-4">
                            <p className="text-sm text-muted-foreground">Avg Risk Score</p>
                            <p className="mt-2 text-2xl font-bold">{riskOverview?.average_risk_score ?? 0}</p>
                        </div>
                        <div className="rounded-xl bg-background p-4">
                            <p className="text-sm text-muted-foreground">Change-Linked</p>
                            <p className="mt-2 text-2xl font-bold text-primary">{riskOverview?.change_correlated_assets ?? 0}</p>
                        </div>
                    </div>

                    <div className="mt-6">
                        <p className="text-sm font-medium text-muted-foreground">Most common risky signals</p>
                        <div className="mt-3 flex flex-wrap gap-2">
                            {riskOverview?.top_signals?.length ? (
                                riskOverview.top_signals.map((signal) => (
                                    <span
                                        key={signal.signal_key}
                                        className="rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary"
                                    >
                                        {signal.label} x{signal.count}
                                    </span>
                                ))
                            ) : (
                                <span className="text-sm text-muted-foreground">
                                    Start ingesting operational telemetry to populate risk signals.
                                </span>
                            )}
                        </div>
                    </div>

                    <div className="mt-6">
                        <p className="text-sm font-medium text-muted-foreground">Recent change activity</p>
                        <div className="mt-3 grid gap-3 md:grid-cols-2">
                            {riskOverview?.recent_changes?.length ? (
                                riskOverview.recent_changes.slice(0, 4).map((change) => (
                                    <div key={`${change.id}-${change.timestamp}`} className="rounded-xl bg-background p-4">
                                        <div className="flex items-start justify-between gap-3">
                                            <div>
                                                <p className="font-medium">{change.title}</p>
                                                <p className="text-sm text-muted-foreground">
                                                    {change.asset_name || "Tenant-wide"} | {new Date(change.timestamp).toLocaleString()}
                                                </p>
                                            </div>
                                            <span className="rounded-full bg-primary/10 px-2 py-1 text-xs font-medium text-primary">
                                                {change.change_type}
                                            </span>
                                        </div>
                                        {change.summary && (
                                            <p className="mt-2 text-sm text-muted-foreground">{change.summary}</p>
                                        )}
                                    </div>
                                ))
                            ) : (
                                <div className="rounded-xl border border-dashed border-border p-4 text-sm text-muted-foreground md:col-span-2">
                                    Start sending deploy, runtime, package, and config changes to build correlation history.
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                <div className="rounded-2xl border border-border bg-card p-6">
                    <div className="flex items-center gap-2">
                        <ShieldAlert className="h-5 w-5 text-primary" />
                        <h2 className="text-lg font-semibold">Assets At Risk</h2>
                    </div>
                    <div className="mt-4 space-y-3">
                        {riskOverview?.assets?.length ? (
                            riskOverview.assets.map((asset) => (
                                <Link
                                    key={asset.asset_id}
                                    href={`/dashboard/assets/${asset.asset_id}`}
                                    className="block rounded-xl border border-border p-4 transition-colors hover:border-primary/50"
                                >
                                    <div className="flex items-start justify-between gap-3">
                                        <div>
                                            <p className="font-medium">{asset.asset_name}</p>
                                            <p className="text-sm text-muted-foreground">
                                                {asset.asset_type} | {asset.forecast_window}
                                            </p>
                                        </div>
                                        <span className={`rounded-full px-2 py-1 text-xs font-medium ${riskBadge(asset.risk_level)}`}>
                                            {asset.risk_score}
                                        </span>
                                    </div>
                                    <p className="mt-3 text-sm text-muted-foreground">{asset.summary}</p>
                                    {asset.likely_causes?.[0] && (
                                        <p className="mt-2 text-sm text-primary">Likely cause: {asset.likely_causes[0]}</p>
                                    )}
                                    <div className="mt-3 flex flex-wrap gap-2">
                                        {asset.top_signals.slice(0, 2).map((signal) => (
                                            <span
                                                key={signal}
                                                className="rounded-full bg-background px-2 py-1 text-xs font-medium text-muted-foreground"
                                            >
                                                {signal}
                                            </span>
                                        ))}
                                    </div>
                                </Link>
                            ))
                        ) : (
                            <div className="rounded-xl border border-dashed border-border p-5 text-sm text-muted-foreground">
                                No assets are currently trending toward failure.
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <div className="grid gap-8 lg:grid-cols-2">
                <div className="rounded-xl border border-border bg-card">
                    <div className="flex items-center justify-between border-b border-border p-6">
                        <h2 className="text-lg font-semibold">Active Alerts</h2>
                        <Link
                            href="/dashboard/alerts"
                            className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                        >
                            View all <ArrowRight className="h-4 w-4" />
                        </Link>
                    </div>
                    <div className="divide-y divide-border">
                        {alerts?.length === 0 && (
                            <div className="p-6 text-center text-muted-foreground">
                                No active alerts. Your assets are healthy.
                            </div>
                        )}
                        {alerts?.map((alert: any) => (
                            <div key={alert.id} className="p-4 transition-colors hover:bg-accent/50">
                                <div className="flex items-start gap-3">
                                    <div
                                        className={`mt-2 h-2 w-2 rounded-full ${
                                            alert.severity === "critical"
                                                ? "bg-red-500"
                                                : alert.severity === "warning"
                                                    ? "bg-amber-500"
                                                    : "bg-blue-500"
                                        }`}
                                    />
                                    <div className="min-w-0 flex-1">
                                        <p className="truncate font-medium">{alert.message}</p>
                                        <p className="text-sm text-muted-foreground">
                                            {alert.asset_name} | {new Date(alert.triggered_at).toLocaleString()}
                                        </p>
                                        {alert.agent_suggestion && (
                                            <p className="mt-1 text-sm italic text-primary">{alert.agent_suggestion}</p>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="rounded-xl border border-border bg-card p-6">
                    <h2 className="text-lg font-semibold">What To Feed Next</h2>
                    <p className="mt-2 text-sm text-muted-foreground">
                        This early warning engine gets sharper as you ingest richer telemetry across infra, app, database, and change layers.
                    </p>
                    <div className="mt-5 grid gap-3">
                        {[
                            "Host signals: cpu_usage, memory_percent, disk_usage, io_wait, ntp_offset_ms",
                            "App signals: error_rate, p95_latency_ms, queue_depth, restart_count, event_loop_lag_ms",
                            "DB signals: db_latency_ms, slow_query_ms, connection_pool_usage",
                            "Change events: deploys, package bumps, config edits, feature flags, and runtime upgrades",
                        ].map((item) => (
                            <div key={item} className="rounded-lg bg-background p-3 text-sm text-muted-foreground">
                                {item}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
