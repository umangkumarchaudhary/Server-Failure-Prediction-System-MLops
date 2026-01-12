"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
    Brain,
    Zap,
    Activity,
    Shield,
    TrendingUp,
    Bell,
    ArrowRight,
    Database,
    Cpu,
    Network,
    Sparkles,
    ChevronRight,
    Play,
} from "lucide-react";

// Neural Network Background Component
const NeuralBackground = () => {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        let animationId: number;
        let nodes: { x: number; y: number; vx: number; vy: number; radius: number }[] = [];

        const resize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            initNodes();
        };

        const initNodes = () => {
            nodes = [];
            const nodeCount = Math.floor((canvas.width * canvas.height) / 15000);
            for (let i = 0; i < nodeCount; i++) {
                nodes.push({
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height,
                    vx: (Math.random() - 0.5) * 0.5,
                    vy: (Math.random() - 0.5) * 0.5,
                    radius: Math.random() * 2 + 1,
                });
            }
        };

        const animate = () => {
            ctx.fillStyle = "rgba(0, 0, 0, 0.05)";
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Draw connections
            ctx.strokeStyle = "rgba(139, 92, 246, 0.15)";
            ctx.lineWidth = 0.5;
            for (let i = 0; i < nodes.length; i++) {
                for (let j = i + 1; j < nodes.length; j++) {
                    const dx = nodes[i].x - nodes[j].x;
                    const dy = nodes[i].y - nodes[j].y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < 150) {
                        ctx.beginPath();
                        ctx.moveTo(nodes[i].x, nodes[i].y);
                        ctx.lineTo(nodes[j].x, nodes[j].y);
                        ctx.globalAlpha = 1 - dist / 150;
                        ctx.stroke();
                    }
                }
            }

            // Draw and update nodes
            ctx.globalAlpha = 1;
            nodes.forEach((node) => {
                node.x += node.vx;
                node.y += node.vy;

                if (node.x < 0 || node.x > canvas.width) node.vx *= -1;
                if (node.y < 0 || node.y > canvas.height) node.vy *= -1;

                ctx.beginPath();
                ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
                ctx.fillStyle = "rgba(139, 92, 246, 0.8)";
                ctx.fill();
            });

            animationId = requestAnimationFrame(animate);
        };

        resize();
        animate();
        window.addEventListener("resize", resize);

        return () => {
            cancelAnimationFrame(animationId);
            window.removeEventListener("resize", resize);
        };
    }, []);

    return (
        <canvas
            ref={canvasRef}
            className="fixed inset-0 pointer-events-none z-0"
            style={{ background: "linear-gradient(135deg, #0a0a0a 0%, #1a0a2e 50%, #0a0a0a 100%)" }}
        />
    );
};

// Animated Counter Component
const AnimatedCounter = ({ end, suffix = "", duration = 2000 }: { end: number; suffix?: string; duration?: number }) => {
    const [count, setCount] = useState(0);
    const [isVisible, setIsVisible] = useState(false);
    const ref = useRef<HTMLSpanElement>(null);

    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting && !isVisible) {
                    setIsVisible(true);
                }
            },
            { threshold: 0.1 }
        );

        if (ref.current) observer.observe(ref.current);
        return () => observer.disconnect();
    }, [isVisible]);

    useEffect(() => {
        if (!isVisible) return;
        let startTime: number;
        const animate = (timestamp: number) => {
            if (!startTime) startTime = timestamp;
            const progress = Math.min((timestamp - startTime) / duration, 1);
            setCount(Math.floor(progress * end));
            if (progress < 1) requestAnimationFrame(animate);
        };
        requestAnimationFrame(animate);
    }, [isVisible, end, duration]);

    return <span ref={ref}>{count}{suffix}</span>;
};

// Data Flow Animation Component
const DataFlowVisualization = () => {
    return (
        <div className="relative w-full max-w-4xl mx-auto h-64 md:h-80">
            {/* Flow Nodes */}
            <div className="absolute left-0 top-1/2 -translate-y-1/2 flex flex-col gap-2 items-center">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-lg shadow-emerald-500/30">
                    <Database className="w-8 h-8 text-white" />
                </div>
                <span className="text-xs font-medium text-emerald-400">DATA</span>
            </div>

            <div className="absolute left-1/4 top-1/2 -translate-y-1/2 flex flex-col gap-2 items-center">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center shadow-lg shadow-blue-500/30 animate-pulse">
                    <Cpu className="w-8 h-8 text-white" />
                </div>
                <span className="text-xs font-medium text-blue-400">PROCESS</span>
            </div>

            <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col gap-2 items-center">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg shadow-violet-500/40 ring-4 ring-violet-500/20">
                    <Brain className="w-10 h-10 text-white" />
                </div>
                <span className="text-xs font-medium text-violet-400">ML MODEL</span>
            </div>

            <div className="absolute right-1/4 top-1/2 -translate-y-1/2 flex flex-col gap-2 items-center">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shadow-lg shadow-amber-500/30 animate-pulse">
                    <Sparkles className="w-8 h-8 text-white" />
                </div>
                <span className="text-xs font-medium text-amber-400">PREDICT</span>
            </div>

            <div className="absolute right-0 top-1/2 -translate-y-1/2 flex flex-col gap-2 items-center">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-rose-500 to-pink-600 flex items-center justify-center shadow-lg shadow-rose-500/30">
                    <Bell className="w-8 h-8 text-white" />
                </div>
                <span className="text-xs font-medium text-rose-400">ACTION</span>
            </div>

            {/* Animated Connection Lines */}
            <svg className="absolute inset-0 w-full h-full" style={{ zIndex: -1 }}>
                <defs>
                    <linearGradient id="flowGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#10b981" />
                        <stop offset="25%" stopColor="#3b82f6" />
                        <stop offset="50%" stopColor="#8b5cf6" />
                        <stop offset="75%" stopColor="#f59e0b" />
                        <stop offset="100%" stopColor="#f43f5e" />
                    </linearGradient>
                </defs>
                <path
                    d="M 40 128 Q 120 128 160 128 Q 200 128 240 128 Q 280 128 320 128 Q 360 128 400 128 Q 440 128 480 128 Q 520 128 560 128"
                    stroke="url(#flowGradient)"
                    strokeWidth="3"
                    fill="none"
                    strokeLinecap="round"
                    className="animate-pulse"
                    style={{ filter: "drop-shadow(0 0 8px rgba(139, 92, 246, 0.5))" }}
                />
            </svg>
        </div>
    );
};

export default function Home() {
    return (
        <main className="min-h-screen bg-black text-white overflow-hidden">
            <NeuralBackground />

            {/* Navigation */}
            <nav className="fixed top-0 w-full z-50 bg-black/50 backdrop-blur-xl border-b border-white/10">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-16">
                        <div className="flex items-center gap-3">
                            <div className="relative">
                                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
                                    <Brain className="w-6 h-6 text-white" />
                                </div>
                                <div className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 rounded-full animate-pulse" />
                            </div>
                            <span className="text-xl font-bold bg-gradient-to-r from-white via-violet-200 to-violet-400 bg-clip-text text-transparent">
                                SensorMind
                            </span>
                        </div>
                        <div className="flex items-center gap-4">
                            <Link href="/demo" className="text-white/60 hover:text-white transition-colors hidden sm:block">
                                Demo
                            </Link>
                            <Link href="/login" className="text-white/60 hover:text-white transition-colors">
                                Login
                            </Link>
                            <Link
                                href="/signup"
                                className="px-4 py-2 rounded-lg bg-gradient-to-r from-violet-600 to-purple-600 text-white font-medium hover:from-violet-500 hover:to-purple-500 transition-all shadow-lg shadow-violet-500/25"
                            >
                                Get Started
                            </Link>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="relative pt-32 pb-20 px-4 z-10">
                <div className="max-w-7xl mx-auto text-center">
                    {/* Badge */}
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-300 text-sm font-medium mb-8 backdrop-blur-sm">
                        <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                        AI-Powered Predictive Maintenance
                    </div>

                    {/* Main Title */}
                    <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold tracking-tight mb-6">
                        <span className="block text-white/90">Where</span>
                        <span className="block bg-gradient-to-r from-violet-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                            Data Meets Mind
                        </span>
                    </h1>

                    <p className="text-xl md:text-2xl text-white/50 max-w-3xl mx-auto mb-12 leading-relaxed">
                        Transform raw sensor data into predictive intelligence.
                        <br className="hidden md:block" />
                        <span className="text-white/70">Detect failures before they happen.</span>
                    </p>

                    {/* CTA Buttons */}
                    <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
                        <Link
                            href="/signup"
                            className="group inline-flex items-center gap-3 px-8 py-4 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 text-white font-semibold text-lg hover:from-violet-500 hover:to-purple-500 transition-all shadow-2xl shadow-violet-500/30"
                        >
                            Start Predicting
                            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                        </Link>
                        <Link
                            href="/demo"
                            className="group inline-flex items-center gap-3 px-8 py-4 rounded-xl border border-white/20 bg-white/5 text-white font-semibold text-lg hover:bg-white/10 backdrop-blur-sm transition-all"
                        >
                            <Play className="w-5 h-5" />
                            Watch Demo
                        </Link>
                    </div>

                    {/* Data Flow Visualization */}
                    <DataFlowVisualization />
                </div>
            </section>

            {/* Stats Section */}
            <section className="relative py-16 z-10 border-y border-white/10 bg-black/50 backdrop-blur-xl">
                <div className="max-w-7xl mx-auto px-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                        {[
                            { value: 99, suffix: ".2%", label: "Prediction Accuracy", color: "text-emerald-400" },
                            { value: 45, suffix: "%", label: "Downtime Reduced", color: "text-blue-400" },
                            { value: 3, suffix: ".5x", label: "ROI Average", color: "text-violet-400" },
                            { value: 5, suffix: "min", label: "Setup Time", color: "text-amber-400" },
                        ].map((stat) => (
                            <div key={stat.label} className="text-center">
                                <div className={`text-4xl md:text-5xl font-bold ${stat.color} mb-2`}>
                                    <AnimatedCounter end={stat.value} suffix={stat.suffix} />
                                </div>
                                <div className="text-white/50 text-sm">{stat.label}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* How It Works */}
            <section className="relative py-24 px-4 z-10">
                <div className="max-w-7xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className="text-4xl md:text-5xl font-bold mb-4">
                            <span className="text-white">The </span>
                            <span className="bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
                                Intelligence Loop
                            </span>
                        </h2>
                        <p className="text-xl text-white/50">From raw data to actionable insights in milliseconds</p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-8">
                        {[
                            {
                                step: "01",
                                icon: Database,
                                title: "Ingest",
                                description: "Stream sensor data, logs, and metrics from any source via REST API or webhooks.",
                                gradient: "from-emerald-500 to-teal-600",
                            },
                            {
                                step: "02",
                                icon: Brain,
                                title: "Analyze",
                                description: "ML models detect anomalies, predict RUL, and identify patterns with explainable AI.",
                                gradient: "from-violet-500 to-purple-600",
                            },
                            {
                                step: "03",
                                icon: Zap,
                                title: "Act",
                                description: "AI Copilot auto-creates tickets, sends alerts, and suggests maintenance actions.",
                                gradient: "from-amber-500 to-orange-600",
                            },
                        ].map((item) => (
                            <div key={item.step} className="relative group">
                                <div className="absolute -inset-0.5 bg-gradient-to-r from-violet-500 to-purple-500 rounded-2xl opacity-0 group-hover:opacity-100 blur transition-opacity" />
                                <div className="relative p-8 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm h-full">
                                    <div className="text-6xl font-bold text-white/10 absolute top-4 right-4">{item.step}</div>
                                    <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${item.gradient} flex items-center justify-center mb-6 shadow-lg`}>
                                        <item.icon className="w-7 h-7 text-white" />
                                    </div>
                                    <h3 className="text-2xl font-bold text-white mb-3">{item.title}</h3>
                                    <p className="text-white/50 leading-relaxed">{item.description}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Features Grid */}
            <section className="relative py-24 px-4 z-10 bg-gradient-to-b from-transparent via-violet-950/20 to-transparent">
                <div className="max-w-7xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className="text-4xl md:text-5xl font-bold mb-4 text-white">
                            Built for the Future
                        </h2>
                        <p className="text-xl text-white/50">Enterprise-grade AI with cutting-edge capabilities</p>
                    </div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {[
                            {
                                icon: Brain,
                                title: "Explainable AI (XAI)",
                                description: "SHAP-powered insights show exactly WHY alerts fire.",
                                tag: "SHAP",
                            },
                            {
                                icon: Network,
                                title: "MCP Integration",
                                description: "Model Context Protocol for AI assistant connectivity.",
                                tag: "NEW",
                            },
                            {
                                icon: TrendingUp,
                                title: "RUL Forecasting",
                                description: "LSTM predictions with confidence intervals.",
                                tag: "ML",
                            },
                            {
                                icon: Shield,
                                title: "Multi-Tenant",
                                description: "Complete data isolation with row-level security.",
                                tag: "SECURE",
                            },
                            {
                                icon: Activity,
                                title: "Drift Detection",
                                description: "Evidently-powered monitoring with auto-retraining.",
                                tag: "MLOPS",
                            },
                            {
                                icon: Bell,
                                title: "Smart Alerts",
                                description: "Slack, Email, Jira, ServiceNow integrations.",
                                tag: "NOTIFY",
                            },
                        ].map((feature) => (
                            <div
                                key={feature.title}
                                className="group p-6 rounded-2xl bg-white/5 border border-white/10 hover:border-violet-500/50 transition-all backdrop-blur-sm"
                            >
                                <div className="flex items-start justify-between mb-4">
                                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500/20 to-purple-500/20 flex items-center justify-center group-hover:from-violet-500 group-hover:to-purple-500 transition-all">
                                        <feature.icon className="w-6 h-6 text-violet-400 group-hover:text-white transition-colors" />
                                    </div>
                                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-violet-500/10 text-violet-400 border border-violet-500/20">
                                        {feature.tag}
                                    </span>
                                </div>
                                <h3 className="text-xl font-semibold text-white mb-2">{feature.title}</h3>
                                <p className="text-white/50">{feature.description}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="relative py-24 px-4 z-10">
                <div className="max-w-4xl mx-auto">
                    <div className="relative p-12 rounded-3xl bg-gradient-to-br from-violet-600/20 to-purple-600/20 border border-violet-500/30 backdrop-blur-xl overflow-hidden">
                        {/* Glow Effect */}
                        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-96 bg-violet-500/30 rounded-full blur-3xl" />

                        <div className="relative text-center">
                            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
                                Ready to Predict the Future?
                            </h2>
                            <p className="text-xl text-white/60 mb-8">
                                Start ingesting data and get predictions in minutes.
                            </p>
                            <Link
                                href="/signup"
                                className="group inline-flex items-center gap-3 px-10 py-5 rounded-xl bg-white text-black font-semibold text-lg hover:bg-white/90 transition-all shadow-2xl"
                            >
                                Start Your Free Trial
                                <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                            </Link>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="relative py-8 px-4 z-10 border-t border-white/10">
                <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
                            <Brain className="w-5 h-5 text-white" />
                        </div>
                        <span className="font-semibold text-white">SensorMind</span>
                    </div>
                    <p className="text-sm text-white/40">
                        © 2026 SensorMind. All rights reserved.
                    </p>
                </div>
            </footer>
        </main>
    );
}
