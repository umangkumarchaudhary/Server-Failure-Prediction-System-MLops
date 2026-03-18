"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Key, Copy, Check } from "lucide-react";
import { authApi, telemetryApi } from "@/lib/api";

export default function SettingsPage() {
    const [copied, setCopied] = useState(false);

    const { data: user } = useQuery({
        queryKey: ["me"],
        queryFn: () => authApi.getMe().then((res) => res.data),
    });
    const { data: adapterCatalog } = useQuery({
        queryKey: ["telemetry-adapters"],
        queryFn: () => telemetryApi.getAdapters().then((res) => res.data),
    });

    const handleCopy = (text: string) => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="space-y-6 animate-in">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold">Settings</h1>
                <p className="text-muted-foreground mt-1">
                    Manage your account and API access
                </p>
            </div>

            {/* Account Info */}
            <div className="rounded-xl border border-border bg-card">
                <div className="p-6 border-b border-border">
                    <h2 className="text-lg font-semibold">Account Information</h2>
                </div>
                <div className="p-6 space-y-4">
                    <div>
                        <label className="text-sm text-muted-foreground">Email</label>
                        <p className="font-medium">{user?.email}</p>
                    </div>
                    <div>
                        <label className="text-sm text-muted-foreground">Name</label>
                        <p className="font-medium">{user?.name || "Not set"}</p>
                    </div>
                    <div>
                        <label className="text-sm text-muted-foreground">Organization</label>
                        <p className="font-medium">{user?.tenant_name}</p>
                    </div>
                    <div>
                        <label className="text-sm text-muted-foreground">Role</label>
                        <p className="font-medium capitalize">{user?.role}</p>
                    </div>
                </div>
            </div>

            {/* API Keys */}
            <div className="rounded-xl border border-border bg-card">
                <div className="p-6 border-b border-border">
                    <div className="flex items-center gap-2">
                        <Key className="w-5 h-5 text-primary" />
                        <h2 className="text-lg font-semibold">API Access</h2>
                    </div>
                </div>
                <div className="p-6">
                    <p className="text-muted-foreground mb-4">
                        Use your API key to ingest telemetry, logs, and change events. The key was shown during signup.
                        If you need a new key, contact support.
                    </p>
                    <div className="p-4 rounded-lg bg-muted">
                        <p className="text-sm mb-2">Collector-Friendly API Request:</p>
                        <pre className="text-sm font-mono overflow-x-auto p-3 rounded bg-background">
                            {`curl -X POST \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"data": [{"asset_id": "payments-api-1", "timestamp": "2026-03-17T10:00:00Z", "adapter_type": "host", "samples": [{"name": "system.cpu.utilization", "value": 0.91, "unit": "ratio"}]}]}' \\
  http://localhost:8000/api/v1/ingest/telemetry`}
                        </pre>
                    </div>
                    <div className="mt-6 grid gap-4 md:grid-cols-2">
                        {adapterCatalog?.adapters?.map((adapter: {
                            adapter_type: string;
                            label: string;
                            description: string;
                            recommended_metrics: string[];
                            sample_payload: Record<string, unknown>;
                        }) => {
                            const sample = JSON.stringify(
                                { data: [adapter.sample_payload] },
                                null,
                                2
                            );
                            return (
                                <div key={adapter.adapter_type} className="rounded-xl border border-border bg-background p-5">
                                    <div className="flex items-start justify-between gap-4 mb-3">
                                        <div>
                                            <h3 className="font-semibold">{adapter.label}</h3>
                                            <p className="text-sm text-muted-foreground mt-1">
                                                {adapter.description}
                                            </p>
                                        </div>
                                        <button
                                            type="button"
                                            onClick={() => handleCopy(sample)}
                                            className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm hover:border-primary/50"
                                        >
                                            {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                                            Copy
                                        </button>
                                    </div>
                                    <p className="text-xs uppercase tracking-wide text-muted-foreground mb-2">
                                        Recommended metrics
                                    </p>
                                    <div className="flex flex-wrap gap-2 mb-4">
                                        {adapter.recommended_metrics.map((metric) => (
                                            <span
                                                key={metric}
                                                className="rounded-full bg-muted px-2.5 py-1 text-xs font-medium"
                                            >
                                                {metric}
                                            </span>
                                        ))}
                                    </div>
                                    <pre className="text-xs font-mono overflow-x-auto p-3 rounded bg-muted">
                                        {sample}
                                    </pre>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>

            {/* Notifications */}
            <div className="rounded-xl border border-border bg-card">
                <div className="p-6 border-b border-border">
                    <h2 className="text-lg font-semibold">Notification Preferences</h2>
                </div>
                <div className="p-6 space-y-4">
                    <label className="flex items-center justify-between cursor-pointer">
                        <div>
                            <p className="font-medium">Email Alerts</p>
                            <p className="text-sm text-muted-foreground">
                                Receive email notifications for critical alerts
                            </p>
                        </div>
                        <input type="checkbox" defaultChecked className="w-5 h-5 rounded" />
                    </label>
                    <label className="flex items-center justify-between cursor-pointer">
                        <div>
                            <p className="font-medium">Daily Digest</p>
                            <p className="text-sm text-muted-foreground">
                                Receive a daily summary of asset health
                            </p>
                        </div>
                        <input type="checkbox" className="w-5 h-5 rounded" />
                    </label>
                </div>
            </div>
        </div>
    );
}
