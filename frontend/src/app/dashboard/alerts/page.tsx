"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Bell, CheckCircle, AlertTriangle, AlertCircle, Info } from "lucide-react";
import { alertsApi } from "@/lib/api";

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
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold">Alerts</h1>
                <p className="text-muted-foreground mt-1">
                    Monitor and manage system alerts
                </p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4">
                <div className="p-4 rounded-xl border border-border bg-card">
                    <div className="flex items-center gap-2 text-orange-500 mb-2">
                        <Bell className="w-5 h-5" />
                        <span className="font-medium">Active</span>
                    </div>
                    <p className="text-2xl font-bold">
                        {alerts?.filter((a: any) => a.status === "active").length ?? 0}
                    </p>
                </div>
                <div className="p-4 rounded-xl border border-border bg-card">
                    <div className="flex items-center gap-2 text-blue-500 mb-2">
                        <CheckCircle className="w-5 h-5" />
                        <span className="font-medium">Acknowledged</span>
                    </div>
                    <p className="text-2xl font-bold">
                        {alerts?.filter((a: any) => a.status === "acknowledged").length ?? 0}
                    </p>
                </div>
                <div className="p-4 rounded-xl border border-border bg-card">
                    <div className="flex items-center gap-2 text-emerald-500 mb-2">
                        <CheckCircle className="w-5 h-5" />
                        <span className="font-medium">Resolved</span>
                    </div>
                    <p className="text-2xl font-bold">
                        {alerts?.filter((a: any) => a.status === "resolved").length ?? 0}
                    </p>
                </div>
            </div>

            {/* Alerts List */}
            <div className="rounded-xl border border-border bg-card overflow-hidden">
                {isLoading ? (
                    <div className="p-6 space-y-4">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="h-20 bg-muted rounded animate-pulse" />
                        ))}
                    </div>
                ) : alerts?.length === 0 ? (
                    <div className="p-12 text-center">
                        <Bell className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                        <h3 className="text-lg font-semibold mb-2">No alerts</h3>
                        <p className="text-muted-foreground">Your system is running smoothly!</p>
                    </div>
                ) : (
                    <div className="divide-y divide-border">
                        {alerts?.map((alert: any) => (
                            <div key={alert.id} className="p-4 hover:bg-accent/50 transition-colors">
                                <div className="flex items-start gap-4">
                                    {getSeverityIcon(alert.severity)}
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-start justify-between gap-4">
                                            <div>
                                                <p className="font-medium">{alert.message}</p>
                                                <p className="text-sm text-muted-foreground mt-1">
                                                    {alert.asset_name} • {new Date(alert.triggered_at).toLocaleString()}
                                                </p>
                                            </div>
                                            <span className={`px-2 py-1 rounded-full text-xs font-medium shrink-0 ${getStatusColor(alert.status)}`}>
                                                {alert.status}
                                            </span>
                                        </div>
                                        {alert.agent_suggestion && (
                                            <div className="mt-3 p-3 rounded-lg bg-primary/5 border border-primary/20">
                                                <p className="text-sm text-primary">
                                                    💡 <strong>AI Suggestion:</strong> {alert.agent_suggestion}
                                                </p>
                                            </div>
                                        )}
                                        {alert.status === "active" && (
                                            <div className="flex gap-2 mt-3">
                                                <button
                                                    onClick={() => updateMutation.mutate({ id: alert.id, status: "acknowledged" })}
                                                    className="px-3 py-1 text-sm rounded-lg bg-blue-500/10 text-blue-500 hover:bg-blue-500/20 transition-colors"
                                                >
                                                    Acknowledge
                                                </button>
                                                <button
                                                    onClick={() => updateMutation.mutate({ id: alert.id, status: "resolved" })}
                                                    className="px-3 py-1 text-sm rounded-lg bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 transition-colors"
                                                >
                                                    Resolve
                                                </button>
                                            </div>
                                        )}
                                        {alert.status === "acknowledged" && (
                                            <div className="flex gap-2 mt-3">
                                                <button
                                                    onClick={() => updateMutation.mutate({ id: alert.id, status: "resolved" })}
                                                    className="px-3 py-1 text-sm rounded-lg bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 transition-colors"
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
