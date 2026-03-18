"use client";

import { useQuery } from "@tanstack/react-query";
import {
    Activity,
    AlertTriangle,
    ArrowLeft,
    Brain,
    Clock,
    MapPin,
    Server,
    ShieldAlert,
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { assetsApi, predictionsApi, riskApi } from "@/lib/api";

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

export default function AssetDetailPage() {
    const params = useParams();
    const assetId = params.id as string;

    const { data: asset, isLoading: assetLoading } = useQuery({
        queryKey: ["asset", assetId],
        queryFn: () => assetsApi.get(assetId).then((res) => res.data),
    });

    const { data: predictions } = useQuery({
        queryKey: ["predictions", assetId],
        queryFn: () => predictionsApi.getForAsset(assetId, 50).then((res) => res.data),
    });

    const { data: risk } = useQuery({
        queryKey: ["asset-risk", assetId],
        queryFn: () => riskApi.getAsset(assetId, { hours: 72 }).then((res) => res.data),
    });

    const chartData =
        predictions
            ?.map((prediction: any, index: number) => ({
                time: new Date(prediction.timestamp).toLocaleTimeString(),
                anomalyScore: prediction.anomaly_score || 0,
                rul: prediction.rul_estimate || 100 - index * 2,
            }))
            .reverse() || [];

    if (assetLoading) {
        return (
            <div className="space-y-6 animate-pulse">
                <div className="h-8 w-48 rounded bg-muted" />
                <div className="h-64 rounded-xl bg-muted" />
            </div>
        );
    }

    const displayRiskLevel = risk?.risk_level || asset?.risk_level;

    return (
        <div className="space-y-6 animate-in">
            <Link
                href="/dashboard/assets"
                className="inline-flex items-center gap-2 text-muted-foreground transition-colors hover:text-foreground"
            >
                <ArrowLeft className="h-4 w-4" />
                Back to Assets
            </Link>

            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div className="flex items-start gap-4">
                    <div className="flex h-16 w-16 items-center justify-center rounded-xl bg-primary/10">
                        <Server className="h-8 w-8 text-primary" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold">{asset?.name}</h1>
                        <div className="mt-2 flex items-center gap-4 text-muted-foreground">
                            <span className="flex items-center gap-1">
                                <Activity className="h-4 w-4" />
                                {asset?.type}
                            </span>
                            {asset?.location && (
                                <span className="flex items-center gap-1">
                                    <MapPin className="h-4 w-4" />
                                    {asset.location}
                                </span>
                            )}
                        </div>
                    </div>
                </div>
                <span
                    className={`rounded-full px-4 py-2 text-sm font-medium ${
                        displayRiskLevel === "critical"
                            ? "bg-red-500/10 text-red-500"
                            : displayRiskLevel === "warning"
                                ? "bg-amber-500/10 text-amber-500"
                                : "bg-emerald-500/10 text-emerald-500"
                    }`}
                >
                    {displayRiskLevel?.toUpperCase()}
                </span>
            </div>

            <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
                <div className="rounded-xl border border-border bg-card p-4">
                    <p className="mb-1 text-sm text-muted-foreground">Health Score</p>
                    <p className="text-2xl font-bold">{asset?.health_score ?? "-"}%</p>
                </div>
                <div className="rounded-xl border border-border bg-card p-4">
                    <p className="mb-1 text-sm text-muted-foreground">Risk Score</p>
                    <p className="text-2xl font-bold">{risk?.risk_score ?? "-"}</p>
                </div>
                <div className="rounded-xl border border-border bg-card p-4">
                    <p className="mb-1 text-sm text-muted-foreground">Latest Anomaly</p>
                    <p className="text-2xl font-bold">{predictions?.[0]?.anomaly_score?.toFixed(2) ?? "-"}</p>
                </div>
                <div className="rounded-xl border border-border bg-card p-4">
                    <p className="mb-1 text-sm text-muted-foreground">Failure Window</p>
                    <p className="text-2xl font-bold">{risk?.forecast_window ?? "-"}</p>
                </div>
                <div className="rounded-xl border border-border bg-card p-4">
                    <p className="mb-1 text-sm text-muted-foreground">Change Link</p>
                    <p className="text-2xl font-bold text-primary">
                        {risk?.change_correlation_score ? `${Math.round(risk.change_correlation_score * 100)}%` : "0%"}
                    </p>
                </div>
            </div>

            <div className="rounded-xl border border-border bg-card p-6">
                <div className="flex items-start justify-between gap-4">
                    <div className="flex items-center gap-2">
                        <ShieldAlert className="h-5 w-5 text-primary" />
                        <h3 className="text-lg font-semibold">Pre-Failure Assessment</h3>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Clock className="h-4 w-4" />
                        Confidence {risk?.confidence ? `${Math.round(risk.confidence * 100)}%` : "-"}
                    </div>
                </div>
                <p className="mt-3 text-sm text-muted-foreground">
                    {risk?.summary || "Waiting for enough telemetry to estimate pre-failure risk."}
                </p>

                <div className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-4">
                    <div className="rounded-xl bg-background p-4">
                        <p className="mb-1 text-sm text-muted-foreground">Forecast Window</p>
                        <p className="text-xl font-bold">{risk?.forecast_window ?? "-"}</p>
                    </div>
                    <div className="rounded-xl bg-background p-4">
                        <p className="mb-1 text-sm text-muted-foreground">Top Signal Count</p>
                        <p className="text-xl font-bold">{risk?.indicators?.length ?? 0}</p>
                    </div>
                    <div className="rounded-xl bg-background p-4">
                        <p className="mb-1 text-sm text-muted-foreground">Last Metric</p>
                        <p className="text-sm font-medium">
                            {risk?.last_metric_at ? new Date(risk.last_metric_at).toLocaleString() : "No data"}
                        </p>
                    </div>
                    <div className="rounded-xl bg-background p-4">
                        <p className="mb-1 text-sm text-muted-foreground">Last Prediction</p>
                        <p className="text-sm font-medium">
                            {risk?.last_prediction_at ? new Date(risk.last_prediction_at).toLocaleString() : "No data"}
                        </p>
                    </div>
                </div>

                <div className="mt-5 grid gap-4 xl:grid-cols-3">
                    <div className="rounded-xl bg-background p-4">
                        <p className="mb-3 text-sm font-medium">Top indicators</p>
                        {risk?.indicators?.length ? (
                            <div className="space-y-3">
                                {risk.indicators.slice(0, 4).map((indicator: any) => (
                                    <div
                                        key={`${indicator.signal_key}-${indicator.metric_name}`}
                                        className="flex items-start justify-between gap-3"
                                    >
                                        <div>
                                            <p className="font-medium">{indicator.label}</p>
                                            <p className="text-sm text-muted-foreground">{indicator.reason}</p>
                                        </div>
                                        <span
                                            className={`rounded-full px-2 py-1 text-xs font-medium ${
                                                indicator.severity === "critical"
                                                    ? "bg-red-500/10 text-red-500"
                                                    : "bg-amber-500/10 text-amber-500"
                                            }`}
                                        >
                                            +{indicator.contribution}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="text-sm text-muted-foreground">No elevated indicators in the latest telemetry window.</p>
                        )}
                    </div>

                    <div className="rounded-xl bg-background p-4">
                        <p className="mb-3 text-sm font-medium">Recommended actions</p>
                        {risk?.recommended_actions?.length ? (
                            <div className="space-y-3">
                                {risk.recommended_actions.map((action: string) => (
                                    <div key={action} className="flex items-start gap-2">
                                        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" />
                                        <p className="text-sm text-muted-foreground">{action}</p>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="text-sm text-muted-foreground">
                                Keep feeding host, app, database, and change telemetry to unlock actionable guidance.
                            </p>
                        )}
                    </div>

                    <div className="rounded-xl bg-background p-4">
                        <p className="mb-3 text-sm font-medium">Likely change causes</p>
                        {risk?.likely_causes?.length ? (
                            <div className="space-y-3">
                                {risk.likely_causes.map((cause: string) => (
                                    <div key={cause} className="rounded-lg border border-primary/10 bg-primary/5 p-3 text-sm text-primary">
                                        {cause}
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="text-sm text-muted-foreground">
                                No recent deploy, package, runtime, or config event is strongly linked yet.
                            </p>
                        )}
                    </div>
                </div>
            </div>

            <div className="rounded-xl border border-border bg-card p-6">
                <h3 className="mb-4 text-lg font-semibold">Recent Changes</h3>
                {risk?.recent_changes?.length ? (
                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                        {risk.recent_changes.map((change: ChangeEvent) => (
                            <div key={`${change.id}-${change.timestamp}`} className="rounded-xl bg-background p-4">
                                <div className="flex items-start justify-between gap-3">
                                    <div>
                                        <p className="font-medium">{change.title}</p>
                                        <p className="text-sm text-muted-foreground">
                                            {new Date(change.timestamp).toLocaleString()}
                                        </p>
                                    </div>
                                    <span className="rounded-full bg-primary/10 px-2 py-1 text-xs font-medium text-primary">
                                        {change.change_type}
                                    </span>
                                </div>
                                {change.summary && (
                                    <p className="mt-2 text-sm text-muted-foreground">{change.summary}</p>
                                )}
                                <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
                                    <span>{change.source || "Unknown source"}</span>
                                    <span>{Math.round(change.correlation_score * 100)}% match</span>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-muted-foreground">
                        No recent change events were recorded for this asset or tenant-wide scope.
                    </p>
                )}
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
                <div className="rounded-xl border border-border bg-card p-6">
                    <h3 className="mb-4 text-lg font-semibold">Anomaly Score Over Time</h3>
                    {chartData.length > 0 ? (
                        <ResponsiveContainer width="100%" height={200}>
                            <AreaChart data={chartData}>
                                <defs>
                                    <linearGradient id="anomalyGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <XAxis dataKey="time" tick={{ fontSize: 12 }} />
                                <YAxis domain={[0, 1]} tick={{ fontSize: 12 }} />
                                <Tooltip />
                                <Area
                                    type="monotone"
                                    dataKey="anomalyScore"
                                    stroke="#ef4444"
                                    fill="url(#anomalyGradient)"
                                    strokeWidth={2}
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="flex h-48 items-center justify-center text-muted-foreground">
                            No prediction data yet
                        </div>
                    )}
                </div>

                <div className="rounded-xl border border-border bg-card p-6">
                    <h3 className="mb-4 text-lg font-semibold">Remaining Useful Life</h3>
                    {chartData.length > 0 ? (
                        <ResponsiveContainer width="100%" height={200}>
                            <AreaChart data={chartData}>
                                <defs>
                                    <linearGradient id="rulGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <XAxis dataKey="time" tick={{ fontSize: 12 }} />
                                <YAxis tick={{ fontSize: 12 }} />
                                <Tooltip />
                                <Area
                                    type="monotone"
                                    dataKey="rul"
                                    stroke="#10b981"
                                    fill="url(#rulGradient)"
                                    strokeWidth={2}
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="flex h-48 items-center justify-center text-muted-foreground">
                            No prediction data yet
                        </div>
                    )}
                </div>
            </div>

            <div className="rounded-xl border border-border bg-card p-6">
                <div className="mb-4 flex items-center gap-2">
                    <Brain className="h-5 w-5 text-primary" />
                    <h3 className="text-lg font-semibold">Explainability (XAI)</h3>
                </div>
                {predictions?.[0]?.explanation_json ? (
                    <div className="space-y-4">
                        <div>
                            <h4 className="mb-2 font-medium">Top Contributing Features</h4>
                            <div className="space-y-2">
                                {predictions[0].explanation_json.top_features?.map((feature: any, index: number) => (
                                    <div key={index} className="flex items-center justify-between">
                                        <span className="text-muted-foreground">
                                            {feature.name || feature.feature || "Unknown feature"}
                                        </span>
                                        <span className="font-medium">{feature.contribution?.toFixed(3)}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                ) : (
                    <p className="text-muted-foreground">
                        Run predictions to see explainability insights with SHAP feature contributions.
                    </p>
                )}
            </div>

            <div className="rounded-xl border border-border bg-card p-6">
                <h3 className="mb-4 text-lg font-semibold">Recent Predictions</h3>
                {predictions?.length === 0 ? (
                    <p className="text-muted-foreground">No predictions yet. Ingest data to generate predictions.</p>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-border">
                                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Time</th>
                                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Anomaly Score</th>
                                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Risk Level</th>
                                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">RUL</th>
                                </tr>
                            </thead>
                            <tbody>
                                {predictions.slice(0, 10).map((prediction: any) => (
                                    <tr key={prediction.id} className="border-b border-border last:border-0">
                                        <td className="px-4 py-3 text-sm">{new Date(prediction.timestamp).toLocaleString()}</td>
                                        <td className="px-4 py-3 font-mono text-sm">
                                            {prediction.anomaly_score?.toFixed(4) ?? "-"}
                                        </td>
                                        <td className="px-4 py-3">
                                            <span
                                                className={`rounded-full px-2 py-1 text-xs font-medium ${
                                                    prediction.risk_level === "critical"
                                                        ? "bg-red-500/10 text-red-500"
                                                        : prediction.risk_level === "warning"
                                                            ? "bg-amber-500/10 text-amber-500"
                                                            : "bg-emerald-500/10 text-emerald-500"
                                                }`}
                                            >
                                                {prediction.risk_level}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-sm">
                                            {prediction.rul_estimate ? `${prediction.rul_estimate}h` : "-"}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}
