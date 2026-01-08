import Link from "next/link";
import {
    Activity,
    Shield,
    Zap,
    Brain,
    TrendingUp,
    Bell,
    ArrowRight,
    CheckCircle
} from "lucide-react";

export default function Home() {
    return (
        <main className="min-h-screen bg-background">
            {/* Navigation */}
            <nav className="fixed top-0 w-full z-50 bg-background/80 backdrop-blur-lg border-b border-border">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-16">
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center">
                                <Activity className="w-5 h-5 text-white" />
                            </div>
                            <span className="text-xl font-bold">PredictrAI</span>
                        </div>
                        <div className="flex items-center gap-4">
                            <Link
                                href="/login"
                                className="text-muted-foreground hover:text-foreground transition-colors"
                            >
                                Login
                            </Link>
                            <Link
                                href="/signup"
                                className="px-4 py-2 rounded-lg gradient-primary text-white font-medium hover:opacity-90 transition-opacity"
                            >
                                Get Started
                            </Link>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="pt-32 pb-20 px-4">
                <div className="max-w-7xl mx-auto text-center">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium mb-8">
                        <Zap className="w-4 h-4" />
                        2026-Ready AI Platform
                    </div>
                    <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6">
                        Predict Failures
                        <br />
                        <span className="bg-gradient-to-r from-primary to-blue-400 bg-clip-text text-transparent">
                            Before They Happen
                        </span>
                    </h1>
                    <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
                        Universal predictive maintenance SaaS with explainable AI,
                        smart copilot automation, and real-time anomaly detection for any industry.
                    </p>
                    <div className="flex flex-col sm:flex-row gap-4 justify-center">
                        <Link
                            href="/signup"
                            className="inline-flex items-center gap-2 px-8 py-4 rounded-xl gradient-primary text-white font-semibold text-lg hover:opacity-90 transition-opacity"
                        >
                            Start Free Trial
                            <ArrowRight className="w-5 h-5" />
                        </Link>
                        <Link
                            href="/demo"
                            className="inline-flex items-center gap-2 px-8 py-4 rounded-xl border border-border bg-card text-foreground font-semibold text-lg hover:bg-accent transition-colors"
                        >
                            View Demo
                        </Link>
                    </div>
                </div>
            </section>

            {/* Stats */}
            <section className="py-16 border-y border-border bg-card/50">
                <div className="max-w-7xl mx-auto px-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                        {[
                            { value: "99.2%", label: "Prediction Accuracy" },
                            { value: "45%", label: "Downtime Reduction" },
                            { value: "3.5x", label: "ROI Average" },
                            { value: "< 5min", label: "Setup Time" },
                        ].map((stat) => (
                            <div key={stat.label} className="text-center">
                                <div className="text-4xl font-bold text-primary mb-2">{stat.value}</div>
                                <div className="text-muted-foreground">{stat.label}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Features */}
            <section className="py-24 px-4">
                <div className="max-w-7xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className="text-4xl font-bold mb-4">2026 AI Differentiators</h2>
                        <p className="text-xl text-muted-foreground">
                            Not just anomaly scores — a complete AI reliability engineer
                        </p>
                    </div>
                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {[
                            {
                                icon: Brain,
                                title: "Explainable AI (XAI)",
                                description: "SHAP-powered insights showing exactly WHY an alert fired and which signals contributed.",
                                color: "gradient-primary",
                            },
                            {
                                icon: Zap,
                                title: "AI Maintenance Copilot",
                                description: "Autonomous agent that drafts incidents, suggests actions, and creates tickets automatically.",
                                color: "gradient-success",
                            },
                            {
                                icon: TrendingUp,
                                title: "RUL Forecasting",
                                description: "Transformer-based remaining useful life predictions with confidence intervals.",
                                color: "gradient-warning",
                            },
                            {
                                icon: Shield,
                                title: "Multi-Tenant Security",
                                description: "Enterprise-grade isolation with row-level security and per-tenant AI observability.",
                                color: "gradient-primary",
                            },
                            {
                                icon: Activity,
                                title: "Living MLOps",
                                description: "Automated drift detection, model monitoring, and self-healing retraining pipelines.",
                                color: "gradient-success",
                            },
                            {
                                icon: Bell,
                                title: "Smart Alerts",
                                description: "Intelligent deduplication with severity escalation and multi-channel delivery.",
                                color: "gradient-warning",
                            },
                        ].map((feature) => (
                            <div
                                key={feature.title}
                                className="p-6 rounded-2xl border border-border bg-card hover:border-primary/50 transition-colors group"
                            >
                                <div className={`w-12 h-12 rounded-xl ${feature.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                                    <feature.icon className="w-6 h-6 text-white" />
                                </div>
                                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                                <p className="text-muted-foreground">{feature.description}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Industries */}
            <section className="py-24 px-4 bg-card/50 border-y border-border">
                <div className="max-w-7xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className="text-4xl font-bold mb-4">Universal Across Industries</h2>
                        <p className="text-xl text-muted-foreground">
                            One platform, any asset type — from servers to turbines
                        </p>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {[
                            "Manufacturing",
                            "IT Infrastructure",
                            "Energy & Utilities",
                            "Logistics & Fleet",
                            "Healthcare Devices",
                            "Oil & Gas",
                            "Data Centers",
                            "Smart Buildings",
                        ].map((industry) => (
                            <div
                                key={industry}
                                className="flex items-center gap-3 p-4 rounded-xl border border-border bg-background hover:border-primary/50 transition-colors"
                            >
                                <CheckCircle className="w-5 h-5 text-primary shrink-0" />
                                <span className="font-medium">{industry}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA */}
            <section className="py-24 px-4">
                <div className="max-w-4xl mx-auto text-center">
                    <h2 className="text-4xl font-bold mb-6">
                        Ready to Predict the Future?
                    </h2>
                    <p className="text-xl text-muted-foreground mb-10">
                        Start ingesting data and get predictions in minutes, not months.
                    </p>
                    <Link
                        href="/signup"
                        className="inline-flex items-center gap-2 px-8 py-4 rounded-xl gradient-primary text-white font-semibold text-lg hover:opacity-90 transition-opacity"
                    >
                        Start Your Free Trial
                        <ArrowRight className="w-5 h-5" />
                    </Link>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-8 px-4 border-t border-border">
                <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
                    <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded gradient-primary flex items-center justify-center">
                            <Activity className="w-4 h-4 text-white" />
                        </div>
                        <span className="font-semibold">PredictrAI</span>
                    </div>
                    <p className="text-sm text-muted-foreground">
                        © 2026 PredictrAI. All rights reserved.
                    </p>
                </div>
            </footer>
        </main>
    );
}
