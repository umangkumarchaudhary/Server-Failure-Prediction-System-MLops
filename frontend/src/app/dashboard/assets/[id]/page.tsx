"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
    ArrowLeft,
    Server,
    Activity,
    AlertTriangle,
    Clock,
    MapPin,
    Brain
} from "lucide-react";
import { assetsApi, predictionsApi } from "@/lib/api";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Area, AreaChart } from "recharts";

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

    // Mock chart data (in real app, this would come from metrics API)
    const chartData = predictions?.map((p: any, i: number) => ({
        time: new Date(p.timestamp).toLocaleTimeString(),
        anomalyScore: p.anomaly_score || 0,
        rul: p.rul_estimate || 100 - i * 2,
    })).reverse() || [];

    if (assetLoading) {
        return (
            <div className="animate-pulse space-y-6">
                <div className="h-8 bg-muted rounded w-48" />
                <div className="h-64 bg-muted rounded-xl" />
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-in">
            {/* Back link */}
            <Link
                href="/dashboard/assets"
                className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
            >
                <ArrowLeft className="w-4 h-4" />
                Back to Assets
            </Link>

            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                <div className="flex items-start gap-4">
                    <div className="w-16 h-16 rounded-xl bg-primary/10 flex items-center justify-center">
                        <Server className="w-8 h-8 text-primary" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold">{asset?.name}</h1>
                        <div className="flex items-center gap-4 mt-2 text-muted-foreground">
                            <span className="flex items-center gap-1">
                                <Activity className="w-4 h-4" />
                                {asset?.type}
                            </span>
                            {asset?.location && (
                                <span className="flex items-center gap-1">
                                    <MapPin className="w-4 h-4" />
                                    {asset.location}
                                </span>
                            )}
                        </div>
                    </div>
                </div>
                <span
                    className={`px-4 py-2 rounded-full text-sm font-medium ${asset?.risk_level === "critical"
                            ? "bg-red-500/10 text-red-500"
                            : asset?.risk_level === "warning"
                                ? "bg-amber-500/10 text-amber-500"
                                : "bg-emerald-500/10 text-emerald-500"
                        }`}
                >
                    {asset?.risk_level?.toUpperCase()}
                </span>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl border border-border bg-card">
                    <p className="text-sm text-muted-foreground mb-1">Health Score</p>
                    <p className="text-2xl font-bold">{asset?.health_score ?? "—"}%</p>
                </div>
                <div className="p-4 rounded-xl border border-border bg-card">
                    <p className="text-sm text-muted-foreground mb-1">Latest Anomaly</p>
                    <p className="text-2xl font-bold">
                        {predictions?.[0]?.anomaly_score?.toFixed(2) ?? "—"}
                    </p>
                </div>
                <div className="p-4 rounded-xl border border-border bg-card">
                    <p className="text-sm text-muted-foreground mb-1">RUL Estimate</p>
                    <p className="text-2xl font-bold">
                        {predictions?.[0]?.rul_estimate ? `${predictions[0].rul_estimate}h` : "—"}
                    </p>
                </div>
                <div className="p-4 rounded-xl border border-border bg-card">
                    <p className="text-sm text-muted-foreground mb-1">Predictions</p>
                    <p className="text-2xl font-bold">{predictions?.length ?? 0}</p>
                </div>
            </div>

            {/* Charts */}
            <div className="grid lg:grid-cols-2 gap-6">
                {/* Anomaly Score Chart */}
                <div className="p-6 rounded-xl border border-border bg-card">
                    <h3 className="text-lg font-semibold mb-4">Anomaly Score Over Time</h3>
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
                        <div className="h-48 flex items-center justify-center text-muted-foreground">
                            No prediction data yet
                        </div>
                    )}
                </div>

                {/* RUL Chart */}
                <div className="p-6 rounded-xl border border-border bg-card">
                    <h3 className="text-lg font-semibold mb-4">Remaining Useful Life</h3>
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
                        <div className="h-48 flex items-center justify-center text-muted-foreground">
                            No prediction data yet
                        </div>
                    )}
                </div>
            </div>

            {/* XAI Panel */}
            <div className="p-6 rounded-xl border border-border bg-card">
                <div className="flex items-center gap-2 mb-4">
                    <Brain className="w-5 h-5 text-primary" />
                    <h3 className="text-lg font-semibold">Explainability (XAI)</h3>
                </div>
                {predictions?.[0]?.explanation_json ? (
                    <div className="space-y-4">
                        <div>
                            <h4 className="font-medium mb-2">Top Contributing Features</h4>
                            <div className="space-y-2">
                                {predictions[0].explanation_json.top_features?.map((f: any, i: number) => (
                                    <div key={i} className="flex items-center justify-between">
                                        <span className="text-muted-foreground">{f.name}</span>
                                        <span className="font-medium">{f.contribution?.toFixed(3)}</span>
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

            {/* Recent Predictions */}
            <div className="p-6 rounded-xl border border-border bg-card">
                <h3 className="text-lg font-semibold mb-4">Recent Predictions</h3>
                {predictions?.length === 0 ? (
                    <p className="text-muted-foreground">No predictions yet. Ingest data to generate predictions.</p>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-border">
                                    <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Time</th>
                                    <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Anomaly Score</th>
                                    <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Risk Level</th>
                                    <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">RUL</th>
                                </tr>
                            </thead>
                            <tbody>
                                {predictions?.slice(0, 10).map((p: any) => (
                                    <tr key={p.id} className="border-b border-border last:border-0">
                                        <td className="py-3 px-4 text-sm">
                                            {new Date(p.timestamp).toLocaleString()}
                                        </td>
                                        <td className="py-3 px-4 text-sm font-mono">
                                            {p.anomaly_score?.toFixed(4) ?? "—"}
                                        </td>
                                        <td className="py-3 px-4">
                                            <span
                                                className={`px-2 py-1 rounded-full text-xs font-medium ${p.risk_level === "critical"
                                                        ? "bg-red-500/10 text-red-500"
                                                        : p.risk_level === "warning"
                                                            ? "bg-amber-500/10 text-amber-500"
                                                            : "bg-emerald-500/10 text-emerald-500"
                                                    }`}
                                            >
                                                {p.risk_level}
                                            </span>
                                        </td>
                                        <td className="py-3 px-4 text-sm">
                                            {p.rul_estimate ? `${p.rul_estimate}h` : "—"}
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
