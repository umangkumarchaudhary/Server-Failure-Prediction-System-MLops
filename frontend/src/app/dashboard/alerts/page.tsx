"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertCircle, AlertTriangle, Bell, CheckCircle, Info, RefreshCw } from "lucide-react";

import { alertsApi, riskApi } from "@/lib/api";

export default function AlertsPage() {
    const queryClient = useQueryClient();

    const { data: alerts, isLoading } = useQuery({
        queryKey: ["alerts"],
        queryFn: () => alertsApi.list({ limit: 100 }).then((res) => res.data),
    });

    const updateMutation = useMutation({
        mutationFn: ({ id, status }: { id: string; status: string }) =>
            alertsApi.update(id, { status }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["alerts"] });
        },
    });

    const syncMutation = useMutation({
        mutationFn: () => riskApi.syncAlerts(),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["alerts"] });
            queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
            queryClient.invalidateQueries({ queryKey: ["risk-overview"] });
        },
    });

    const getSeverityIcon = (severity: string) => {
        switch (severity) {
            case "critical":
                return <AlertCircle className="w-5 h-5 text-red-500" />;
            case "warning":
                return <AlertTriangle className="w-5 h-5 text-amber-500" />;
            default:
                return <Info className="w-5 h-5 text-blue-500" />;
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case "resolved":
                return "bg-emerald-500/10 text-emerald-500";
            case "acknowledged":
                return "bg-blue-500/10 text-blue-500";
            default:
                return "bg-orange-500/10 text-orange-500";
        }
    };

    return (
        <div className="space-y-6 animate-in">
            <div>
                <h1 className="text-3xl font-bold">Alerts</h1>
                <p className="mt-1 text-muted-foreground">Monitor and manage system alerts</p>
                <div className="mt-4 flex flex-wrap items-center gap-3">
                    <button
                        onClick={() => syncMutation.mutate()}
                        disabled={syncMutation.isPending}
                        className="inline-flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 text-sm font-medium transition-colors hover:bg-accent disabled:cursor-not-allowed disabled:opacity-60"
                    >
                        <RefreshCw className={`h-4 w-4 ${syncMutation.isPending ? "animate-spin" : ""}`} />
                        Sync Risk Alerts
                    </button>
                    {syncMutation.data?.data?.message && (
                        <p className="text-sm text-muted-foreground">{syncMutation.data.data.message}</p>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
                <div className="rounded-xl border border-border bg-card p-4">
                    <div className="mb-2 flex items-center gap-2 text-orange-500">
                        <Bell className="w-5 h-5" />
                        <span className="font-medium">Active</span>
                    </div>
                    <p className="text-2xl font-bold">
                        {alerts?.filter((a: any) => a.status === "active").length ?? 0}
                    </p>
                </div>
                <div className="rounded-xl border border-border bg-card p-4">
                    <div className="mb-2 flex items-center gap-2 text-blue-500">
                        <CheckCircle className="w-5 h-5" />
                        <span className="font-medium">Acknowledged</span>
                    </div>
                    <p className="text-2xl font-bold">
                        {alerts?.filter((a: any) => a.status === "acknowledged").length ?? 0}
                    </p>
                </div>
                <div className="rounded-xl border border-border bg-card p-4">
                    <div className="mb-2 flex items-center gap-2 text-emerald-500">
                        <CheckCircle className="w-5 h-5" />
                        <span className="font-medium">Resolved</span>
                    </div>
                    <p className="text-2xl font-bold">
                        {alerts?.filter((a: any) => a.status === "resolved").length ?? 0}
                    </p>
                </div>
            </div>

            <div className="overflow-hidden rounded-xl border border-border bg-card">
                {isLoading ? (
                    <div className="space-y-4 p-6">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="h-20 animate-pulse rounded bg-muted" />
                        ))}
                    </div>
                ) : alerts?.length === 0 ? (
                    <div className="p-12 text-center">
                        <Bell className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
                        <h3 className="mb-2 text-lg font-semibold">No alerts</h3>
                        <p className="text-muted-foreground">Your system is running smoothly!</p>
                    </div>
                ) : (
                    <div className="divide-y divide-border">
                        {alerts?.map((alert: any) => (
                            <div key={alert.id} className="p-4 transition-colors hover:bg-accent/50">
                                <div className="flex items-start gap-4">
                                    {getSeverityIcon(alert.severity)}
                                    <div className="min-w-0 flex-1">
                                        <div className="flex items-start justify-between gap-4">
                                            <div>
                                                <p className="font-medium">{alert.message}</p>
                                                <p className="mt-1 text-sm text-muted-foreground">
                                                    {alert.asset_name} | {new Date(alert.triggered_at).toLocaleString()}
                                                </p>
                                            </div>
                                            <div className="flex shrink-0 items-center gap-2">
                                                {alert.source && (
                                                    <span className="rounded-full bg-primary/10 px-2 py-1 text-xs font-medium text-primary">
                                                        {alert.source}
                                                    </span>
                                                )}
                                                <span className={`rounded-full px-2 py-1 text-xs font-medium ${getStatusColor(alert.status)}`}>
                                                    {alert.status}
                                                </span>
                                            </div>
                                        </div>
                                        {alert.agent_suggestion && (
                                            <div className="mt-3 rounded-lg border border-primary/20 bg-primary/5 p-3">
                                                <p className="text-sm text-primary">
                                                    <strong>AI Suggestion:</strong> {alert.agent_suggestion}
                                                </p>
                                            </div>
                                        )}
                                        {alert.status === "active" && (
                                            <div className="mt-3 flex gap-2">
                                                <button
                                                    onClick={() => updateMutation.mutate({ id: alert.id, status: "acknowledged" })}
                                                    className="rounded-lg bg-blue-500/10 px-3 py-1 text-sm text-blue-500 transition-colors hover:bg-blue-500/20"
                                                >
                                                    Acknowledge
                                                </button>
                                                <button
                                                    onClick={() => updateMutation.mutate({ id: alert.id, status: "resolved" })}
                                                    className="rounded-lg bg-emerald-500/10 px-3 py-1 text-sm text-emerald-500 transition-colors hover:bg-emerald-500/20"
                                                >
                                                    Resolve
                                                </button>
                                            </div>
                                        )}
                                        {alert.status === "acknowledged" && (
                                            <div className="mt-3 flex gap-2">
                                                <button
                                                    onClick={() => updateMutation.mutate({ id: alert.id, status: "resolved" })}
                                                    className="rounded-lg bg-emerald-500/10 px-3 py-1 text-sm text-emerald-500 transition-colors hover:bg-emerald-500/20"
                                                >
                                                    Resolve
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
