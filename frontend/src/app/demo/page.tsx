"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
    Activity,
    Brain,
    AlertTriangle,
    TrendingUp,
    Shield,
    Zap,
    Bot,
    Bell,
    ChevronRight,
    Play,
    ArrowRight,
} from "lucide-react";

// Animated counter hook
function useCountUp(end: number, duration: number = 2000, start: number = 0) {
    const [count, setCount] = useState(start);
    const [isVisible, setIsVisible] = useState(false);
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) {
                    setIsVisible(true);
                }
            },
            { threshold: 0.3 }
        );

        if (ref.current) {
            observer.observe(ref.current);
        }

        return () => observer.disconnect();
    }, []);

    useEffect(() => {
        if (!isVisible) return;

        let startTime: number;
        const animate = (timestamp: number) => {
            if (!startTime) startTime = timestamp;
            const progress = Math.min((timestamp - startTime) / duration, 1);
            setCount(Math.floor(progress * (end - start) + start));
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        requestAnimationFrame(animate);
    }, [isVisible, end, duration, start]);

    return { count, ref };
}

// Animated line chart
function AnimatedLineChart({ data, color, delay = 0 }: { data: number[]; color: string; delay?: number }) {
    const [visible, setVisible] = useState(false);
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) {
                    setTimeout(() => setVisible(true), delay);
                }
            },
            { threshold: 0.3 }
        );
        if (ref.current) observer.observe(ref.current);
        return () => observer.disconnect();
    }, [delay]);

    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;

    const points = data
        .map((value, index) => {
            const x = (index / (data.length - 1)) * 100;
            const y = 100 - ((value - min) / range) * 80 - 10;
            return `${x},${y}`;
        })
        .join(" ");

    return (
        <div ref={ref} className="w-full h-32 relative">
            <svg
                viewBox="0 0 100 100"
                preserveAspectRatio="none"
                className="w-full h-full"
            >
                <defs>
                    <linearGradient id={`gradient-${color}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={color} stopOpacity="0.3" />
                        <stop offset="100%" stopColor={color} stopOpacity="0" />
                    </linearGradient>
                </defs>
                <polyline
                    points={points}
                    fill="none"
                    stroke={color}
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className={`transition-all duration-1000 ${visible ? "opacity-100" : "opacity-0"}`}
                    style={{
                        strokeDasharray: visible ? "none" : "500",
                        strokeDashoffset: visible ? "0" : "500",
                    }}
                />
                <polygon
                    points={`0,100 ${points} 100,100`}
                    fill={`url(#gradient-${color})`}
                    className={`transition-opacity duration-1000 ${visible ? "opacity-100" : "opacity-0"}`}
                />
            </svg>
        </div>
    );
}

// Animated pie chart
function AnimatedPieChart({ segments, delay = 0 }: { segments: { value: number; color: string; label: string }[]; delay?: number }) {
    const [visible, setVisible] = useState(false);
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) {
                    setTimeout(() => setVisible(true), delay);
                }
            },
            { threshold: 0.3 }
        );
        if (ref.current) observer.observe(ref.current);
        return () => observer.disconnect();
    }, [delay]);

    const total = segments.reduce((sum, s) => sum + s.value, 0);
    let currentAngle = 0;

    return (
        <div ref={ref} className="relative w-48 h-48 mx-auto">
            <svg viewBox="0 0 100 100" className="w-full h-full transform -rotate-90">
                {segments.map((segment, index) => {
                    const angle = (segment.value / total) * 360;
                    const startAngle = currentAngle;
                    currentAngle += angle;

                    const x1 = 50 + 40 * Math.cos((startAngle * Math.PI) / 180);
                    const y1 = 50 + 40 * Math.sin((startAngle * Math.PI) / 180);
                    const x2 = 50 + 40 * Math.cos(((startAngle + angle) * Math.PI) / 180);
                    const y2 = 50 + 40 * Math.sin(((startAngle + angle) * Math.PI) / 180);
                    const largeArc = angle > 180 ? 1 : 0;

                    return (
                        <path
                            key={index}
                            d={`M 50 50 L ${x1} ${y1} A 40 40 0 ${largeArc} 1 ${x2} ${y2} Z`}
                            fill={segment.color}
                            className={`transition-all duration-700 origin-center`}
                            style={{
                                transform: visible ? "scale(1)" : "scale(0)",
                                transitionDelay: `${index * 150}ms`,
                            }}
                        />
                    );
                })}
                <circle cx="50" cy="50" r="25" fill="var(--background)" />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl font-bold">{total}</span>
            </div>
        </div>
    );
}

// Animated bar chart
function AnimatedBarChart({ data, delay = 0 }: { data: { label: string; value: number; color: string }[]; delay?: number }) {
    const [visible, setVisible] = useState(false);
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) {
                    setTimeout(() => setVisible(true), delay);
                }
            },
            { threshold: 0.3 }
        );
        if (ref.current) observer.observe(ref.current);
        return () => observer.disconnect();
    }, [delay]);

    const max = Math.max(...data.map((d) => d.value));

    return (
        <div ref={ref} className="space-y-3">
            {data.map((item, index) => (
                <div key={index} className="space-y-1">
                    <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">{item.label}</span>
                        <span className="font-medium">{item.value}%</span>
                    </div>
                    <div className="h-3 bg-muted rounded-full overflow-hidden">
                        <div
                            className="h-full rounded-full transition-all duration-1000 ease-out"
                            style={{
                                width: visible ? `${(item.value / max) * 100}%` : "0%",
                                backgroundColor: item.color,
                                transitionDelay: `${index * 100}ms`,
                            }}
                        />
                    </div>
                </div>
            ))}
        </div>
    );
}

// Live data simulation
function useLiveData() {
    const [data, setData] = useState({
        anomalyScore: 0.23,
        rulHours: 847,
        healthScore: 94,
        activeAlerts: 3,
        metrics: Array.from({ length: 20 }, () => Math.random() * 30 + 60),
    });

    useEffect(() => {
        const interval = setInterval(() => {
            setData((prev) => ({
                anomalyScore: Math.max(0, Math.min(1, prev.anomalyScore + (Math.random() - 0.5) * 0.1)),
                rulHours: Math.max(0, prev.rulHours - Math.random() * 2),
                healthScore: Math.max(0, Math.min(100, prev.healthScore + (Math.random() - 0.5) * 2)),
                activeAlerts: Math.max(0, prev.activeAlerts + Math.floor(Math.random() * 3) - 1),
                metrics: [...prev.metrics.slice(1), Math.random() * 30 + 60],
            }));
        }, 2000);

        return () => clearInterval(interval);
    }, []);

    return data;
}

// Feature card with reveal animation
function FeatureCard({
    icon: Icon,
    title,
    description,
    delay,
}: {
    icon: any;
    title: string;
    description: string;
    delay: number;
}) {
    const [visible, setVisible] = useState(false);
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) {
                    setTimeout(() => setVisible(true), delay);
                }
            },
            { threshold: 0.2 }
        );
        if (ref.current) observer.observe(ref.current);
        return () => observer.disconnect();
    }, [delay]);

    return (
        <div
            ref={ref}
            className={`p-6 rounded-2xl bg-card border border-border hover:border-primary/50 transition-all duration-500 ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
                }`}
        >
            <div className="w-12 h-12 rounded-xl gradient-primary flex items-center justify-center mb-4">
                <Icon className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-xl font-semibold mb-2">{title}</h3>
            <p className="text-muted-foreground">{description}</p>
        </div>
    );
}

export default function DemoPage() {
    const liveData = useLiveData();
    const stats = [
        { label: "Assets Monitored", value: 12847, suffix: "+" },
        { label: "Anomalies Detected", value: 99.7, suffix: "%", decimals: 1 },
        { label: "Downtime Prevented", value: 4320, suffix: "hrs" },
        { label: "Cost Savings", value: 2.4, suffix: "M", prefix: "$" },
    ];

    const assetHealth = [
        { label: "Excellent", value: 68, color: "#22c55e" },
        { label: "Good", value: 22, color: "#3b82f6" },
        { label: "Warning", value: 8, color: "#f59e0b" },
        { label: "Critical", value: 2, color: "#ef4444" },
    ];

    const pieSegments = [
        { value: 68, color: "#22c55e", label: "Healthy" },
        { value: 22, color: "#3b82f6", label: "Good" },
        { value: 8, color: "#f59e0b", label: "Warning" },
        { value: 2, color: "#ef4444", label: "Critical" },
    ];

    return (
        <div className="min-h-screen bg-background">
            {/* Hero Section */}
            <section className="relative overflow-hidden py-20 px-4">
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-purple-500/5" />
                <div className="absolute inset-0">
                    {[...Array(20)].map((_, i) => (
                        <div
                            key={i}
                            className="absolute w-1 h-1 bg-primary/30 rounded-full animate-pulse"
                            style={{
                                left: `${Math.random() * 100}%`,
                                top: `${Math.random() * 100}%`,
                                animationDelay: `${Math.random() * 2}s`,
                            }}
                        />
                    ))}
                </div>

                <div className="max-w-6xl mx-auto text-center relative z-10">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm mb-8 animate-fade-in">
                        <Play className="w-4 h-4" />
                        Live Demo Experience
                    </div>

                    <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-foreground via-primary to-foreground bg-clip-text text-transparent animate-gradient">
                        SensorMind in Action
                    </h1>

                    <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-12">
                        Watch real-time predictive maintenance powered by advanced AI.
                        See anomaly detection, RUL forecasting, and intelligent alerts working together.
                    </p>

                    <div className="flex flex-wrap justify-center gap-4">
                        <Link
                            href="/signup"
                            className="px-8 py-4 rounded-xl gradient-primary text-white font-medium hover:opacity-90 transition-opacity flex items-center gap-2"
                        >
                            Start Free Trial <ArrowRight className="w-5 h-5" />
                        </Link>
                        <Link
                            href="/login"
                            className="px-8 py-4 rounded-xl border border-border hover:border-primary/50 transition-colors flex items-center gap-2"
                        >
                            Sign In
                        </Link>
                    </div>
                </div>
            </section>

            {/* Live Stats Section */}
            <section className="py-16 px-4 bg-card/50">
                <div className="max-w-6xl mx-auto">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                        {stats.map((stat, index) => {
                            const { count, ref } = useCountUp(stat.value, 2000 + index * 200);
                            return (
                                <div
                                    key={index}
                                    ref={ref}
                                    className="text-center p-6 rounded-2xl bg-background border border-border"
                                >
                                    <div className="text-4xl md:text-5xl font-bold gradient-text mb-2">
                                        {stat.prefix}
                                        {stat.decimals ? count.toFixed(stat.decimals) : count}
                                        {stat.suffix}
                                    </div>
                                    <div className="text-muted-foreground">{stat.label}</div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </section>

            {/* Live Dashboard Preview */}
            <section className="py-20 px-4">
                <div className="max-w-6xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className="text-4xl font-bold mb-4">Real-Time Monitoring</h2>
                        <p className="text-muted-foreground max-w-xl mx-auto">
                            Live data streaming from connected assets with instant anomaly detection
                        </p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-6 mb-8">
                        {/* Anomaly Score Card */}
                        <div className="p-6 rounded-2xl bg-card border border-border">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="font-medium text-muted-foreground">Anomaly Score</h3>
                                <Activity className="w-5 h-5 text-primary" />
                            </div>
                            <div className="text-4xl font-bold mb-2">
                                {(liveData.anomalyScore * 100).toFixed(1)}%
                            </div>
                            <div className={`text-sm ${liveData.anomalyScore > 0.5 ? "text-red-500" : "text-emerald-500"}`}>
                                {liveData.anomalyScore > 0.5 ? "⚠️ Elevated" : "✓ Normal"}
                            </div>
                            <AnimatedLineChart
                                data={liveData.metrics}
                                color={liveData.anomalyScore > 0.5 ? "#ef4444" : "#22c55e"}
                            />
                        </div>

                        {/* RUL Card */}
                        <div className="p-6 rounded-2xl bg-card border border-border">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="font-medium text-muted-foreground">Remaining Useful Life</h3>
                                <TrendingUp className="w-5 h-5 text-primary" />
                            </div>
                            <div className="text-4xl font-bold mb-2">
                                {Math.floor(liveData.rulHours)}h
                            </div>
                            <div className="text-sm text-emerald-500">✓ Within tolerance</div>
                            <div className="mt-4 h-4 bg-muted rounded-full overflow-hidden">
                                <div
                                    className="h-full gradient-primary transition-all duration-500"
                                    style={{ width: `${(liveData.rulHours / 1000) * 100}%` }}
                                />
                            </div>
                        </div>

                        {/* Health Score Card */}
                        <div className="p-6 rounded-2xl bg-card border border-border">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="font-medium text-muted-foreground">Health Score</h3>
                                <Shield className="w-5 h-5 text-primary" />
                            </div>
                            <div className="text-4xl font-bold mb-2">
                                {Math.round(liveData.healthScore)}%
                            </div>
                            <div className="text-sm text-emerald-500">✓ Excellent condition</div>
                            <div className="mt-4 relative w-32 h-32 mx-auto">
                                <svg viewBox="0 0 100 100" className="w-full h-full transform -rotate-90">
                                    <circle
                                        cx="50"
                                        cy="50"
                                        r="40"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="8"
                                        className="text-muted"
                                    />
                                    <circle
                                        cx="50"
                                        cy="50"
                                        r="40"
                                        fill="none"
                                        stroke="url(#health-gradient)"
                                        strokeWidth="8"
                                        strokeLinecap="round"
                                        strokeDasharray={`${liveData.healthScore * 2.51} 251`}
                                        className="transition-all duration-500"
                                    />
                                    <defs>
                                        <linearGradient id="health-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                            <stop offset="0%" stopColor="#8b5cf6" />
                                            <stop offset="100%" stopColor="#3b82f6" />
                                        </linearGradient>
                                    </defs>
                                </svg>
                            </div>
                        </div>
                    </div>

                    {/* Alert Feed */}
                    <div className="p-6 rounded-2xl bg-card border border-border">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-xl font-semibold">Live Alert Feed</h3>
                            <span className="px-3 py-1 rounded-full bg-red-500/10 text-red-500 text-sm">
                                {liveData.activeAlerts} Active
                            </span>
                        </div>
                        <div className="space-y-4">
                            {[
                                { severity: "warning", message: "Elevated vibration on Pump P-103", time: "2m ago", asset: "Pump P-103" },
                                { severity: "info", message: "Scheduled maintenance reminder", time: "15m ago", asset: "Compressor C-7" },
                                { severity: "critical", message: "Temperature threshold exceeded", time: "1h ago", asset: "Motor M-12" },
                            ].map((alert, index) => (
                                <div
                                    key={index}
                                    className={`p-4 rounded-xl border ${alert.severity === "critical"
                                        ? "border-red-500/30 bg-red-500/5"
                                        : alert.severity === "warning"
                                            ? "border-amber-500/30 bg-amber-500/5"
                                            : "border-blue-500/30 bg-blue-500/5"
                                        } animate-fade-in`}
                                    style={{ animationDelay: `${index * 100}ms` }}
                                >
                                    <div className="flex items-center gap-3">
                                        <AlertTriangle
                                            className={`w-5 h-5 ${alert.severity === "critical"
                                                ? "text-red-500"
                                                : alert.severity === "warning"
                                                    ? "text-amber-500"
                                                    : "text-blue-500"
                                                }`}
                                        />
                                        <div className="flex-1">
                                            <p className="font-medium">{alert.message}</p>
                                            <p className="text-sm text-muted-foreground">{alert.asset} • {alert.time}</p>
                                        </div>
                                        <ChevronRight className="w-5 h-5 text-muted-foreground" />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            {/* Asset Health Distribution */}
            <section className="py-20 px-4 bg-card/50">
                <div className="max-w-6xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className="text-4xl font-bold mb-4">Asset Health Overview</h2>
                        <p className="text-muted-foreground max-w-xl mx-auto">
                            Real-time health distribution across your entire asset fleet
                        </p>
                    </div>

                    <div className="grid md:grid-cols-2 gap-12 items-center">
                        <div>
                            <AnimatedPieChart segments={pieSegments} delay={200} />
                            <div className="flex flex-wrap justify-center gap-4 mt-8">
                                {pieSegments.map((segment, index) => (
                                    <div key={index} className="flex items-center gap-2">
                                        <div
                                            className="w-3 h-3 rounded-full"
                                            style={{ backgroundColor: segment.color }}
                                        />
                                        <span className="text-sm text-muted-foreground">{segment.label}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div>
                            <AnimatedBarChart data={assetHealth} delay={400} />
                        </div>
                    </div>
                </div>
            </section>

            {/* AI Copilot Demo */}
            <section className="py-20 px-4">
                <div className="max-w-6xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className="text-4xl font-bold mb-4">AI Maintenance Copilot</h2>
                        <p className="text-muted-foreground max-w-xl mx-auto">
                            Intelligent assistant that observes, reasons, and acts on your behalf
                        </p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-6">
                        <FeatureCard
                            icon={Brain}
                            title="Observe"
                            description="Continuously monitors anomalies, drift events, and RUL predictions across all assets"
                            delay={0}
                        />
                        <FeatureCard
                            icon={Zap}
                            title="Reason"
                            description="Uses LLMs to analyze patterns, draft incident descriptions, and determine priority"
                            delay={200}
                        />
                        <FeatureCard
                            icon={Bot}
                            title="Act"
                            description="Creates tickets, sends notifications, and suggests maintenance actions automatically"
                            delay={400}
                        />
                    </div>

                    {/* Chat Demo */}
                    <div className="mt-12 p-6 rounded-2xl bg-card border border-border max-w-2xl mx-auto">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="w-10 h-10 rounded-full gradient-primary flex items-center justify-center">
                                <Bot className="w-5 h-5 text-white" />
                            </div>
                            <div>
                                <h3 className="font-semibold">AI Copilot</h3>
                                <p className="text-xs text-emerald-500">● Online</p>
                            </div>
                        </div>
                        <div className="space-y-4">
                            <div className="p-4 rounded-xl bg-muted max-w-[80%]">
                                <p className="text-sm">
                                    I detected an anomaly on Pump P-103. Vibration levels are 40% above normal.
                                    Based on similar historical incidents, this could indicate bearing wear.
                                </p>
                            </div>
                            <div className="p-4 rounded-xl bg-muted max-w-[80%]">
                                <p className="text-sm font-medium mb-2">Suggested Actions:</p>
                                <ul className="text-sm space-y-1">
                                    <li>• Schedule bearing inspection within 48 hours</li>
                                    <li>• Reduce operating load by 20%</li>
                                    <li>• Order replacement parts (SKF 6205-2RS)</li>
                                </ul>
                            </div>
                            <div className="p-4 rounded-xl gradient-primary text-white max-w-[80%] ml-auto">
                                <p className="text-sm">Create a maintenance ticket for this issue</p>
                            </div>
                            <div className="p-4 rounded-xl bg-muted max-w-[80%]">
                                <p className="text-sm">
                                    ✓ Created ticket MAINT-4521 in Jira. Assigned to John Smith with high priority.
                                    Notification sent to maintenance team.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Features Grid */}
            <section className="py-20 px-4 bg-card/50">
                <div className="max-w-6xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className="text-4xl font-bold mb-4">Complete Platform Features</h2>
                        <p className="text-muted-foreground max-w-xl mx-auto">
                            Everything you need for intelligent predictive maintenance
                        </p>
                    </div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                        <FeatureCard
                            icon={Activity}
                            title="Anomaly Detection"
                            description="Isolation Forest with SHAP explainability for transparent AI decisions"
                            delay={0}
                        />
                        <FeatureCard
                            icon={TrendingUp}
                            title="RUL Forecasting"
                            description="LSTM neural networks with confidence intervals for accurate predictions"
                            delay={100}
                        />
                        <FeatureCard
                            icon={Brain}
                            title="Log Analysis"
                            description="NLP-powered clustering to find patterns in log messages"
                            delay={200}
                        />
                        <FeatureCard
                            icon={Shield}
                            title="Drift Detection"
                            description="Automated monitoring for data and concept drift with retraining triggers"
                            delay={300}
                        />
                        <FeatureCard
                            icon={Bell}
                            title="Smart Notifications"
                            description="Multi-channel alerts via Email, Slack, Teams, and Webhooks"
                            delay={400}
                        />
                        <FeatureCard
                            icon={Zap}
                            title="MLOps Dashboard"
                            description="MLflow integration for experiment tracking and model versioning"
                            delay={500}
                        />
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-20 px-4">
                <div className="max-w-4xl mx-auto text-center">
                    <h2 className="text-4xl md:text-5xl font-bold mb-6">
                        Ready to Transform Your Maintenance?
                    </h2>
                    <p className="text-xl text-muted-foreground mb-12">
                        Join thousands of companies using SensorMind to prevent downtime and reduce costs
                    </p>
                    <div className="flex flex-wrap justify-center gap-4">
                        <Link
                            href="/signup"
                            className="px-8 py-4 rounded-xl gradient-primary text-white font-medium hover:opacity-90 transition-opacity flex items-center gap-2 text-lg"
                        >
                            Start Free Trial <ArrowRight className="w-5 h-5" />
                        </Link>
                    </div>
                </div>
            </section>

            <footer className="py-12 px-4 border-t border-border">
                <div className="max-w-6xl mx-auto text-center text-muted-foreground">
                    <p>© 2026 SensorMind. AI-Powered Predictive Maintenance Platform.</p>
                </div>
            </footer>

            <style jsx global>{`
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes gradient {
          0%, 100% {
            background-position: 0% 50%;
          }
          50% {
            background-position: 100% 50%;
          }
        }

        .animate-fade-in {
          animation: fade-in 0.6s ease-out forwards;
        }

        .animate-gradient {
          background-size: 200% 200%;
          animation: gradient 4s ease infinite;
        }

        .gradient-text {
          background: linear-gradient(135deg, #8b5cf6, #3b82f6);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .gradient-primary {
          background: linear-gradient(135deg, #8b5cf6, #3b82f6);
        }
      `}</style>
        </div>
    );
}
