"use client";

import { useQuery } from "@tanstack/react-query";
import {
    Server,
    AlertTriangle,
    Bell,
    Activity,
    TrendingUp,
    TrendingDown,
    ArrowRight
} from "lucide-react";
import Link from "next/link";
import { dashboardApi, assetsApi, alertsApi } from "@/lib/api";

export default function DashboardPage() {
    const { data: stats, isLoading: statsLoading } = useQuery({
        queryKey: ["dashboard-stats"],
        queryFn: () => dashboardApi.getStats().then((res) => res.data),
    });

    const { data: assets } = useQuery({
        queryKey: ["assets-recent"],
        queryFn: () => assetsApi.list({ limit: 5 }).then((res) => res.data),
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
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold">Dashboard</h1>
                <p className="text-muted-foreground mt-1">
                    Overview of your asset health and predictions
                </p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                {statCards.map((stat) => (
                    <div
                        key={stat.title}
                        className="p-4 rounded-xl border border-border bg-card hover:border-primary/50 transition-colors"
                    >
                        <div className={`w-10 h-10 rounded-lg ${stat.bg} flex items-center justify-center mb-3`}>
                            <stat.icon className={`w-5 h-5 ${stat.color}`} />
                        </div>
                        <p className="text-2xl font-bold">{statsLoading ? "—" : stat.value}</p>
                        <p className="text-sm text-muted-foreground">{stat.title}</p>
                    </div>
                ))}
            </div>

            {/* Two column layout */}
            <div className="grid lg:grid-cols-2 gap-8">
                {/* Recent Assets */}
                <div className="rounded-xl border border-border bg-card">
                    <div className="flex items-center justify-between p-6 border-b border-border">
                        <h2 className="text-lg font-semibold">Recent Assets</h2>
                        <Link
                            href="/dashboard/assets"
                            className="text-sm text-primary hover:underline flex items-center gap-1"
                        >
                            View all <ArrowRight className="w-4 h-4" />
                        </Link>
                    </div>
                    <div className="divide-y divide-border">
                        {assets?.length === 0 && (
                            <div className="p-6 text-center text-muted-foreground">
                                No assets yet. Create your first asset to get started.
                            </div>
                        )}
                        {assets?.map((asset: any) => (
                            <Link
                                key={asset.id}
                                href={`/dashboard/assets/${asset.id}`}
                                className="flex items-center justify-between p-4 hover:bg-accent/50 transition-colors"
                            >
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                                        <Server className="w-5 h-5 text-primary" />
                                    </div>
                                    <div>
                                        <p className="font-medium">{asset.name}</p>
                                        <p className="text-sm text-muted-foreground">{asset.type}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span
                                        className={`px-2 py-1 rounded-full text-xs font-medium ${asset.risk_level === "critical"
                                                ? "bg-red-500/10 text-red-500"
                                                : asset.risk_level === "warning"
                                                    ? "bg-amber-500/10 text-amber-500"
                                                    : "bg-emerald-500/10 text-emerald-500"
                                            }`}
                                    >
                                        {asset.risk_level}
                                    </span>
                                </div>
                            </Link>
                        ))}
                    </div>
                </div>

                {/* Active Alerts */}
                <div className="rounded-xl border border-border bg-card">
                    <div className="flex items-center justify-between p-6 border-b border-border">
                        <h2 className="text-lg font-semibold">Active Alerts</h2>
                        <Link
                            href="/dashboard/alerts"
                            className="text-sm text-primary hover:underline flex items-center gap-1"
                        >
                            View all <ArrowRight className="w-4 h-4" />
                        </Link>
                    </div>
                    <div className="divide-y divide-border">
                        {alerts?.length === 0 && (
                            <div className="p-6 text-center text-muted-foreground">
                                No active alerts. Your assets are healthy!
                            </div>
                        )}
                        {alerts?.map((alert: any) => (
                            <div
                                key={alert.id}
                                className="p-4 hover:bg-accent/50 transition-colors"
                            >
                                <div className="flex items-start gap-3">
                                    <div
                                        className={`w-2 h-2 rounded-full mt-2 ${alert.severity === "critical"
                                                ? "bg-red-500"
                                                : alert.severity === "warning"
                                                    ? "bg-amber-500"
                                                    : "bg-blue-500"
                                            }`}
                                    />
                                    <div className="flex-1 min-w-0">
                                        <p className="font-medium truncate">{alert.message}</p>
                                        <p className="text-sm text-muted-foreground">
                                            {alert.asset_name} • {new Date(alert.triggered_at).toLocaleString()}
                                        </p>
                                        {alert.agent_suggestion && (
                                            <p className="text-sm text-primary mt-1 italic">
                                                💡 {alert.agent_suggestion}
                                            </p>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
