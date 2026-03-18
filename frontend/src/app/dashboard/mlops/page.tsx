"use client";

import { useQuery } from "@tanstack/react-query";
import {
    Activity,
    AlertTriangle,
    Brain,
    CheckCircle,
    Database,
    RefreshCw,
} from "lucide-react";

import { mlHealthApi } from "@/lib/api";

type DriftSummary = {
    kind: "data" | "prediction";
    status: "healthy" | "drift_detected" | "insufficient_data";
    drift_detected: boolean;
    drifted_features: string[];
    drifted_count: number;
    total_columns: number;
    share_of_drifted_columns: number;
    sample_size: number;
    message: string;
};

type ModelHealth = {
    key: string;
    name: string;
    category: string;
    status: "production" | "monitoring" | "learning";
    last_activity_at: string | null;
    assets_covered: number;
    activity_24h: number;
    primary_metric_label: string;
    primary_metric_value: string;
    summary: string;
    drift_detected: boolean;
    drifted_features: string[];
};

type MLHealthSummary = {
    overview: {
        active_models: number;
        production_models: number;
        drift_detected_models: number;
        assets_covered: number;
        last_updated_at: string;
    };
    models: ModelHealth[];
    data_drift: DriftSummary;
    prediction_drift: DriftSummary;
    mlflow_tracking_uri?: string | null;
};

const statusStyles: Record<ModelHealth["status"], string> = {
    production: "bg-emerald-500/10 text-emerald-500",
    monitoring: "bg-amber-500/10 text-amber-500",
    learning: "bg-slate-500/10 text-slate-400",
};

const driftStyles: Record<DriftSummary["status"], string> = {
    healthy: "bg-emerald-500/10 text-emerald-500",
    drift_detected: "bg-amber-500/10 text-amber-500",
    insufficient_data: "bg-slate-500/10 text-slate-400",
};

function formatTimestamp(value?: string | null) {
    if (!value) {
        return "No recent activity";
    }
    return new Date(value).toLocaleString();
}

function formatDriftShare(share: number) {
    return `${Math.round(share * 100)}%`;
}

export default function MLOpsPage() {
    const { data, isLoading, isError, error, refetch, isRefetching } = useQuery<MLHealthSummary>({
        queryKey: ["ml-health-summary"],
        queryFn: () => mlHealthApi.getSummary().then((res) => res.data),
        refetchInterval: 60_000,
    });

    const overview = data?.overview;
    const models = data?.models ?? [];

    const statCards = [
        {
            title: "Active Models",
            value: overview?.active_models ?? 0,
            icon: Brain,
            color: "text-primary",
            bg: "bg-primary/10",
        },
        {
            title: "In Production",
            value: overview?.production_models ?? 0,
            icon: CheckCircle,
            color: "text-emerald-500",
            bg: "bg-emerald-500/10",
        },
        {
            title: "Drift Signals",
            value: overview?.drift_detected_models ?? 0,
            icon: AlertTriangle,
            color: "text-amber-500",
            bg: "bg-amber-500/10",
        },
        {
            title: "Assets Covered",
            value: overview?.assets_covered ?? 0,
            icon: Database,
            color: "text-blue-500",
            bg: "bg-blue-500/10",
        },
    ];

    return (
        <div className="space-y-6 animate-in">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                    <h1 className="text-3xl font-bold">ML Health</h1>
                    <p className="text-muted-foreground mt-1">
                        Live model activity, input drift, and prediction stability for your tenant.
                    </p>
                </div>
                <button
                    onClick={() => refetch()}
                    disabled={isRefetching}
                    className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium hover:border-primary/50 transition-colors disabled:opacity-60"
                >
                    <RefreshCw className={`w-4 h-4 ${isRefetching ? "animate-spin" : ""}`} />
                    Refresh
                </button>
            </div>

            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                {statCards.map((stat) => (
                    <div key={stat.title} className="rounded-xl border border-border bg-card p-4">
                        <div className={`mb-3 flex h-10 w-10 items-center justify-center rounded-lg ${stat.bg}`}>
                            <stat.icon className={`h-5 w-5 ${stat.color}`} />
                        </div>
                        <p className="text-2xl font-bold">{isLoading ? "—" : stat.value}</p>
                        <p className="text-sm text-muted-foreground">{stat.title}</p>
                    </div>
                ))}
            </div>

            {isError && (
                <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-5">
                    <p className="font-medium text-destructive">ML health data could not be loaded.</p>
                    <p className="mt-1 text-sm text-muted-foreground">
                        {error instanceof Error ? error.message : "Please try again after backend review."}
                    </p>
                </div>
            )}

            {data && (
                <>
                    <div className="grid gap-4 lg:grid-cols-2">
                        {[data.data_drift, data.prediction_drift].map((drift) => (
                            <div key={drift.kind} className="rounded-xl border border-border bg-card p-6">
                                <div className="flex items-start justify-between gap-4">
                                    <div>
                                        <p className="text-sm uppercase tracking-[0.2em] text-muted-foreground">
                                            {drift.kind === "data" ? "Input Drift" : "Prediction Drift"}
                                        </p>
                                        <h2 className="mt-2 text-lg font-semibold">
                                            {drift.drift_detected ? "Attention needed" : "Stable window"}
                                        </h2>
                                    </div>
                                    <span className={`rounded-full px-2 py-1 text-xs font-medium ${driftStyles[drift.status]}`}>
                                        {drift.status.replace("_", " ")}
                                    </span>
                                </div>
                                <p className="mt-4 text-sm text-muted-foreground">{drift.message}</p>
                                <div className="mt-5 grid grid-cols-3 gap-3">
                                    <div className="rounded-lg bg-background p-3">
                                        <p className="text-xs text-muted-foreground">Drifted</p>
                                        <p className="mt-1 text-lg font-semibold">{drift.drifted_count}</p>
                                    </div>
                                    <div className="rounded-lg bg-background p-3">
                                        <p className="text-xs text-muted-foreground">Columns</p>
                                        <p className="mt-1 text-lg font-semibold">{drift.total_columns}</p>
                                    </div>
                                    <div className="rounded-lg bg-background p-3">
                                        <p className="text-xs text-muted-foreground">Share</p>
                                        <p className="mt-1 text-lg font-semibold">{formatDriftShare(drift.share_of_drifted_columns)}</p>
                                    </div>
                                </div>
                                <div className="mt-4 flex flex-wrap gap-2">
                                    {drift.drifted_features.length > 0 ? (
                                        drift.drifted_features.map((feature) => (
                                            <span
                                                key={feature}
                                                className="rounded-full bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-500"
                                            >
                                                {feature}
                                            </span>
                                        ))
                                    ) : (
                                        <span className="text-sm text-muted-foreground">No drifted features in the latest window.</span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className="rounded-xl border border-border bg-card">
                        <div className="border-b border-border p-6">
                            <h2 className="text-lg font-semibold">Live Model Capabilities</h2>
                            <p className="mt-1 text-sm text-muted-foreground">
                                Updated from recent tenant metrics and prediction history.
                            </p>
                        </div>
                        <div className="divide-y divide-border">
                            {models.map((model) => (
                                <div key={model.key} className="p-6">
                                    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                                        <div className="flex items-start gap-4">
                                            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                                                {model.category === "Guardrail" ? (
                                                    <Activity className="h-6 w-6 text-primary" />
                                                ) : (
                                                    <Brain className="h-6 w-6 text-primary" />
                                                )}
                                            </div>
                                            <div>
                                                <div className="flex flex-wrap items-center gap-2">
                                                    <h3 className="font-semibold">{model.name}</h3>
                                                    <span className="rounded-full bg-accent px-2 py-1 text-xs font-medium text-muted-foreground">
                                                        {model.category}
                                                    </span>
                                                    <span className={`rounded-full px-2 py-1 text-xs font-medium ${statusStyles[model.status]}`}>
                                                        {model.status}
                                                    </span>
                                                    <span
                                                        className={`rounded-full px-2 py-1 text-xs font-medium ${
                                                            model.drift_detected
                                                                ? "bg-amber-500/10 text-amber-500"
                                                                : "bg-emerald-500/10 text-emerald-500"
                                                        }`}
                                                    >
                                                        {model.drift_detected ? "Drift signal" : "Healthy"}
                                                    </span>
                                                </div>
                                                <p className="mt-2 text-sm text-muted-foreground">{model.summary}</p>
                                                <p className="mt-2 text-sm text-muted-foreground">
                                                    Last activity: {formatTimestamp(model.last_activity_at)}
                                                </p>
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-3 gap-3 lg:min-w-[320px]">
                                            <div className="rounded-lg bg-background p-3">
                                                <p className="text-xs text-muted-foreground">Assets</p>
                                                <p className="mt-1 text-lg font-semibold">{model.assets_covered}</p>
                                            </div>
                                            <div className="rounded-lg bg-background p-3">
                                                <p className="text-xs text-muted-foreground">24h activity</p>
                                                <p className="mt-1 text-lg font-semibold">{model.activity_24h}</p>
                                            </div>
                                            <div className="rounded-lg bg-background p-3">
                                                <p className="text-xs text-muted-foreground">{model.primary_metric_label}</p>
                                                <p className="mt-1 text-lg font-semibold">{model.primary_metric_value}</p>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="mt-4 flex flex-wrap gap-2">
                                        {model.drifted_features.length > 0 ? (
                                            model.drifted_features.map((feature) => (
                                                <span
                                                    key={feature}
                                                    className="rounded-full bg-background px-3 py-1 text-xs font-medium text-muted-foreground"
                                                >
                                                    {feature}
                                                </span>
                                            ))
                                        ) : (
                                            <span className="text-sm text-muted-foreground">
                                                No drifted features attached to this capability right now.
                                            </span>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="rounded-xl border border-border bg-card p-6">
                        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                            <div className="flex items-center gap-3">
                                <Activity className="h-5 w-5 text-primary" />
                                <div>
                                    <h3 className="font-semibold">MLflow Tracking</h3>
                                    <p className="text-sm text-muted-foreground">
                                        Open experiment tracking and model artifacts from the configured backend.
                                    </p>
                                </div>
                            </div>
                            <a
                                href={data.mlflow_tracking_uri || "http://localhost:5000"}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center justify-center rounded-lg gradient-primary px-4 py-2 font-medium text-white hover:opacity-90 transition-opacity"
                            >
                                Open MLflow
                            </a>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
