"use client";

import { Brain, Activity, RefreshCw, CheckCircle, AlertTriangle } from "lucide-react";

export default function MLOpsPage() {
    // Mock data for demo
    const models = [
        {
            name: "Anomaly Detector v2.1",
            type: "Isolation Forest + Transformer",
            status: "production",
            lastTrained: "2026-01-08",
            accuracy: 0.94,
            drift: false,
        },
        {
            name: "RUL Forecaster v1.3",
            type: "LSTM",
            status: "production",
            lastTrained: "2026-01-07",
            accuracy: 0.89,
            drift: false,
        },
        {
            name: "Log Analyzer v1.0",
            type: "DistilBERT + HDBSCAN",
            status: "staging",
            lastTrained: "2026-01-06",
            accuracy: 0.82,
            drift: true,
        },
    ];

    return (
        <div className="space-y-6 animate-in">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold">ML Health</h1>
                <p className="text-muted-foreground mt-1">
                    Monitor model performance and data drift
                </p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl border border-border bg-card">
                    <p className="text-sm text-muted-foreground mb-1">Active Models</p>
                    <p className="text-2xl font-bold">3</p>
                </div>
                <div className="p-4 rounded-xl border border-border bg-card">
                    <p className="text-sm text-muted-foreground mb-1">In Production</p>
                    <p className="text-2xl font-bold">2</p>
                </div>
                <div className="p-4 rounded-xl border border-border bg-card">
                    <p className="text-sm text-muted-foreground mb-1">Drift Detected</p>
                    <p className="text-2xl font-bold text-amber-500">1</p>
                </div>
                <div className="p-4 rounded-xl border border-border bg-card">
                    <p className="text-sm text-muted-foreground mb-1">Avg. Accuracy</p>
                    <p className="text-2xl font-bold">88.3%</p>
                </div>
            </div>

            {/* Models */}
            <div className="rounded-xl border border-border bg-card">
                <div className="p-6 border-b border-border">
                    <h2 className="text-lg font-semibold">Deployed Models</h2>
                </div>
                <div className="divide-y divide-border">
                    {models.map((model) => (
                        <div key={model.name} className="p-6">
                            <div className="flex items-start justify-between">
                                <div className="flex items-start gap-4">
                                    <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                                        <Brain className="w-6 h-6 text-primary" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold">{model.name}</h3>
                                        <p className="text-sm text-muted-foreground">{model.type}</p>
                                        <p className="text-sm text-muted-foreground mt-1">
                                            Last trained: {model.lastTrained}
                                        </p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    {model.drift ? (
                                        <span className="flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-500">
                                            <AlertTriangle className="w-3 h-3" />
                                            Drift Detected
                                        </span>
                                    ) : (
                                        <span className="flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-500">
                                            <CheckCircle className="w-3 h-3" />
                                            Healthy
                                        </span>
                                    )}
                                    <span
                                        className={`px-2 py-1 rounded-full text-xs font-medium ${model.status === "production"
                                                ? "bg-blue-500/10 text-blue-500"
                                                : "bg-purple-500/10 text-purple-500"
                                            }`}
                                    >
                                        {model.status}
                                    </span>
                                </div>
                            </div>
                            <div className="mt-4 flex items-center gap-6">
                                <div>
                                    <p className="text-xs text-muted-foreground">Accuracy</p>
                                    <p className="font-semibold">{(model.accuracy * 100).toFixed(1)}%</p>
                                </div>
                                <div className="flex-1">
                                    <div className="h-2 rounded-full bg-muted overflow-hidden">
                                        <div
                                            className="h-full rounded-full bg-primary"
                                            style={{ width: `${model.accuracy * 100}%` }}
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* MLflow Link */}
            <div className="p-6 rounded-xl border border-border bg-card">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <Activity className="w-5 h-5 text-primary" />
                        <div>
                            <h3 className="font-semibold">MLflow Tracking</h3>
                            <p className="text-sm text-muted-foreground">
                                View detailed experiment logs and model registry
                            </p>
                        </div>
                    </div>
                    <a
                        href="http://localhost:5000"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-4 py-2 rounded-lg gradient-primary text-white font-medium hover:opacity-90 transition-opacity"
                    >
                        Open MLflow UI
                    </a>
                </div>
            </div>
        </div>
    );
}
