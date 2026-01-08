"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
    Server,
    Plus,
    Search,
    X,
    ChevronRight
} from "lucide-react";
import Link from "next/link";
import { assetsApi } from "@/lib/api";

export default function AssetsPage() {
    const queryClient = useQueryClient();
    const [showCreate, setShowCreate] = useState(false);
    const [search, setSearch] = useState("");
    const [newAsset, setNewAsset] = useState({ name: "", type: "machine", location: "" });

    const { data: assets, isLoading } = useQuery({
        queryKey: ["assets"],
        queryFn: () => assetsApi.list({ limit: 100 }).then((res) => res.data),
    });

    const createMutation = useMutation({
        mutationFn: (data: { name: string; type: string; location?: string }) =>
            assetsApi.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["assets"] });
            setShowCreate(false);
            setNewAsset({ name: "", type: "machine", location: "" });
        },
    });

    const filteredAssets = assets?.filter((asset: any) =>
        asset.name.toLowerCase().includes(search.toLowerCase()) ||
        asset.type.toLowerCase().includes(search.toLowerCase())
    );

    return (
        <div className="space-y-6 animate-in">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold">Assets</h1>
                    <p className="text-muted-foreground mt-1">
                        Manage and monitor your equipment
                    </p>
                </div>
                <button
                    onClick={() => setShowCreate(true)}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg gradient-primary text-white font-medium hover:opacity-90 transition-opacity"
                >
                    <Plus className="w-5 h-5" />
                    Add Asset
                </button>
            </div>

            {/* Search */}
            <div className="relative max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <input
                    type="text"
                    placeholder="Search assets..."
                    className="w-full pl-10 pr-4 py-3 rounded-lg bg-card border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
            </div>

            {/* Asset Grid */}
            {isLoading ? (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="p-6 rounded-xl border border-border bg-card animate-pulse">
                            <div className="w-12 h-12 rounded-lg bg-muted mb-4" />
                            <div className="h-5 bg-muted rounded w-2/3 mb-2" />
                            <div className="h-4 bg-muted rounded w-1/3" />
                        </div>
                    ))}
                </div>
            ) : filteredAssets?.length === 0 ? (
                <div className="text-center py-16">
                    <Server className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No assets found</h3>
                    <p className="text-muted-foreground mb-4">
                        {search ? "Try a different search term" : "Create your first asset to get started"}
                    </p>
                    {!search && (
                        <button
                            onClick={() => setShowCreate(true)}
                            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg gradient-primary text-white font-medium"
                        >
                            <Plus className="w-5 h-5" />
                            Add Asset
                        </button>
                    )}
                </div>
            ) : (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {filteredAssets?.map((asset: any) => (
                        <Link
                            key={asset.id}
                            href={`/dashboard/assets/${asset.id}`}
                            className="group p-6 rounded-xl border border-border bg-card hover:border-primary/50 transition-all"
                        >
                            <div className="flex items-start justify-between mb-4">
                                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                                    <Server className="w-6 h-6 text-primary" />
                                </div>
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
                            <h3 className="text-lg font-semibold mb-1 group-hover:text-primary transition-colors">
                                {asset.name}
                            </h3>
                            <p className="text-sm text-muted-foreground mb-3">{asset.type}</p>
                            {asset.location && (
                                <p className="text-sm text-muted-foreground">📍 {asset.location}</p>
                            )}
                            <div className="flex items-center justify-between mt-4 pt-4 border-t border-border">
                                <div>
                                    {asset.health_score !== null && (
                                        <div className="flex items-center gap-2">
                                            <div className="w-16 h-2 rounded-full bg-muted overflow-hidden">
                                                <div
                                                    className={`h-full rounded-full ${asset.health_score >= 80
                                                            ? "bg-emerald-500"
                                                            : asset.health_score >= 50
                                                                ? "bg-amber-500"
                                                                : "bg-red-500"
                                                        }`}
                                                    style={{ width: `${asset.health_score}%` }}
                                                />
                                            </div>
                                            <span className="text-sm font-medium">{asset.health_score}%</span>
                                        </div>
                                    )}
                                </div>
                                <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
                            </div>
                        </Link>
                    ))}
                </div>
            )}

            {/* Create Modal */}
            {showCreate && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
                    <div className="w-full max-w-md bg-card border border-border rounded-2xl p-6">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-semibold">Add New Asset</h2>
                            <button
                                onClick={() => setShowCreate(false)}
                                className="p-2 rounded-lg hover:bg-accent transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        <form
                            onSubmit={(e) => {
                                e.preventDefault();
                                createMutation.mutate(newAsset);
                            }}
                            className="space-y-4"
                        >
                            <div>
                                <label className="block text-sm font-medium mb-2">Name</label>
                                <input
                                    type="text"
                                    required
                                    placeholder="e.g., Production Server 1"
                                    className="w-full px-4 py-3 rounded-lg bg-background border border-input focus:border-primary outline-none"
                                    value={newAsset.name}
                                    onChange={(e) => setNewAsset({ ...newAsset, name: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-2">Type</label>
                                <select
                                    className="w-full px-4 py-3 rounded-lg bg-background border border-input focus:border-primary outline-none"
                                    value={newAsset.type}
                                    onChange={(e) => setNewAsset({ ...newAsset, type: e.target.value })}
                                >
                                    <option value="machine">Machine</option>
                                    <option value="server">Server</option>
                                    <option value="turbine">Turbine</option>
                                    <option value="vehicle">Vehicle</option>
                                    <option value="sensor">Sensor</option>
                                    <option value="other">Other</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-2">Location (optional)</label>
                                <input
                                    type="text"
                                    placeholder="e.g., Building A, Floor 2"
                                    className="w-full px-4 py-3 rounded-lg bg-background border border-input focus:border-primary outline-none"
                                    value={newAsset.location}
                                    onChange={(e) => setNewAsset({ ...newAsset, location: e.target.value })}
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={createMutation.isPending}
                                className="w-full py-3 rounded-lg gradient-primary text-white font-medium hover:opacity-90 disabled:opacity-50"
                            >
                                {createMutation.isPending ? "Creating..." : "Create Asset"}
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
