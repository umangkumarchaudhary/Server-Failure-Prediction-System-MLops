# PredictrAI

**Universal Predictive Maintenance SaaS** - A 2026-ready AI platform for anomaly detection, failure prediction, and intelligent maintenance automation.

![Status](https://img.shields.io/badge/status-in%20development-yellow)
![License](https://img.shields.io/badge/license-MIT-blue)

## Features

- 🔍 **Explainable Anomaly Detection** - SHAP-powered insights, not black boxes
- 🤖 **AI Maintenance Copilot** - Automated incident drafting and ticket creation
- 📈 **RUL Forecasting** - Predict remaining useful life with transformers
- 📝 **Log Analysis** - NLP-based error clustering and root-cause extraction
- 🏢 **Multi-Tenant** - Secure data isolation for any industry
- 🔄 **Living MLOps** - Drift detection and auto-retraining

## Quick Start

```bash
# Clone the repo
git clone <repo-url>
cd predictAI

# Start with Docker
docker-compose up -d

# Or run manually:

# Backend
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend  
cd frontend
npm install
npm run dev
```

## Documentation

- [Implementation Plan](./implementation_plan.md) - Architecture & design
- [Task Tracker](./task.md) - Development progress
- [Help Reference](./helpreference.md) - 2026 AI trends guide

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js, TypeScript, shadcn/ui, Tailwind |
| Backend | FastAPI, Python 3.11+ |
| Database | PostgreSQL |
| ML | PyTorch, Transformers, scikit-learn, SHAP |
| MLOps | MLflow, Evidently |

## License

MIT
