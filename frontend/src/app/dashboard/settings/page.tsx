"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Key, Copy, Check, Settings } from "lucide-react";
import { authApi } from "@/lib/api";

export default function SettingsPage() {
    const [copied, setCopied] = useState(false);

    const { data: user } = useQuery({
        queryKey: ["me"],
        queryFn: () => authApi.getMe().then((res) => res.data),
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
                        Use your API key to ingest metrics and logs. The key was shown during signup.
                        If you need a new key, contact support.
                    </p>
                    <div className="p-4 rounded-lg bg-muted">
                        <p className="text-sm mb-2">Sample API Request:</p>
                        <pre className="text-sm font-mono overflow-x-auto p-3 rounded bg-background">
                            {`curl -X POST \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"data": [{"asset_id": "...", "timestamp": "...", "metric_name": "temperature", "metric_value": 42.5}]}' \\
  http://localhost:8000/api/v1/ingest/metrics`}
                        </pre>
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
