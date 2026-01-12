<p align="center">
  <h1 align="center">🧠 SensorMind</h1>
  <p align="center"><strong>AI-Powered Predictive Maintenance Platform</strong></p>
  <p align="center">
    <em>Predict equipment failures before they happen • Reduce downtime by 45%</em>
  </p>
</p>

<p align="center">
  <a href="#-live-demo">Live Demo</a> •
  <a href="#-features">Features</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-api-reference">API</a>
</p>

---

## 🌐 Live Demo

| Service | URL |
|---------|-----|
| **API Documentation** | [Swagger UI](https://server-failure-prediction-system-mlops.onrender.com/docs) |
| **Health Check** | [/health](https://server-failure-prediction-system-mlops.onrender.com/health) |
| **Frontend** | [SensorMind App](https://sensormind.netlify.app) |

---

## 🎯 Problem Statement

Industrial equipment failures cause **$50B+ annually** in unplanned downtime. Traditional maintenance approaches are:
- **Reactive**: Fix after failure (costly, dangerous)
- **Preventive**: Fixed schedules (wasteful, misses failures)

**SensorMind** enables **Predictive Maintenance** — detecting failures *before* they happen using AI/ML.

---

## ✨ Features

### 🔮 Anomaly Detection
- **Isolation Forest** algorithm for unsupervised anomaly detection
- **SHAP Explainability** — understand *why* alerts triggered
- Real-time streaming support

### 📈 RUL Forecasting
- **LSTM Neural Network** for Remaining Useful Life prediction
- Confidence intervals for uncertainty quantification
- Multi-asset parallel inference

### 🤖 AI Maintenance Copilot
```
┌─────────┐    ┌─────────┐    ┌─────────┐
│ OBSERVE │───▶│ REASON  │───▶│   ACT   │
└─────────┘    └─────────┘    └─────────┘
  Anomalies      LLM Analysis    Create tickets
  Predictions    Root cause      Send alerts
  Drift events   Prioritize      Suggest actions
```
- Autonomous agent with **Observe-Reason-Act** loop
- Auto-drafts incidents with root cause analysis
- Integrates with **Jira**, **ServiceNow**
- Sends alerts via **Slack**, **Teams**, **Email**, **Webhooks**

### 📊 MLOps Pipeline
- **MLflow** experiment tracking
- **Evidently** for data & concept drift detection
- Automated retraining triggers
- Model versioning & registry

### 🏢 Multi-Tenant SaaS
- Complete tenant isolation
- API key authentication for ingestion
- JWT authentication for dashboard
- Role-based access control

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SENSORMIND PLATFORM                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐     ┌─────────────────────────────────────────────┐   │
│  │   FRONTEND  │     │              BACKEND (FastAPI)              │   │
│  │   Next.js   │────▶│  ┌─────────────────────────────────────┐   │   │
│  │  Dashboard  │     │  │           API Gateway               │   │   │
│  └─────────────┘     │  │  Auth • Assets • Ingest • Alerts    │   │   │
│                      │  └─────────────────────────────────────┘   │   │
│  ┌─────────────┐     │                    │                        │   │
│  │  SENSORS /  │     │  ┌─────────────────▼─────────────────┐     │   │
│  │   DEVICES   │────▶│  │         ML PIPELINE               │     │   │
│  │  (Metrics)  │     │  │  ┌───────────┐  ┌──────────────┐  │     │   │
│  └─────────────┘     │  │  │ Anomaly   │  │     RUL      │  │     │   │
│                      │  │  │ Detector  │  │  Forecaster  │  │     │   │
│                      │  │  │(Isolation │  │   (LSTM)     │  │     │   │
│                      │  │  │  Forest)  │  │              │  │     │   │
│                      │  │  └─────┬─────┘  └──────┬───────┘  │     │   │
│                      │  │        │               │          │     │   │
│                      │  │        └───────┬───────┘          │     │   │
│                      │  │                ▼                  │     │   │
│                      │  │  ┌─────────────────────────────┐  │     │   │
│                      │  │  │      LOG ANALYZER           │  │     │   │
│                      │  │  │  (HDBSCAN + Transformers)   │  │     │   │
│                      │  │  └─────────────────────────────┘  │     │   │
│                      │  └─────────────────┬─────────────────┘     │   │
│                      │                    │                        │   │
│                      │  ┌─────────────────▼─────────────────┐     │   │
│                      │  │         AI COPILOT AGENT          │     │   │
│                      │  │   ┌─────────┐ ┌───────┐ ┌─────┐   │     │   │
│                      │  │   │ Observe │▶│Reason │▶│ Act │   │     │   │
│                      │  │   └─────────┘ └───────┘ └─────┘   │     │   │
│                      │  │        │         │         │       │     │   │
│                      │  │        ▼         ▼         ▼       │     │   │
│                      │  │   Events     LLM/RAG    Tickets    │     │   │
│                      │  │              Analysis   Alerts     │     │   │
│                      │  └─────────────────────────────────────┘   │   │
│                      └─────────────────────────────────────────────┘   │
│                                          │                              │
│                      ┌───────────────────┼───────────────────┐         │
│                      ▼                   ▼                   ▼         │
│              ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │
│              │  PostgreSQL  │   │    Redis     │   │   MLflow     │   │
│              │   (Neon)     │   │   (Cache)    │   │  (Tracking)  │   │
│              └──────────────┘   └──────────────┘   └──────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow

```
Sensors/Logs                    ML Models                      Actions
    │                              │                              │
    ▼                              ▼                              ▼
┌────────┐    ┌─────────┐    ┌──────────┐    ┌─────────┐    ┌─────────┐
│ Ingest │───▶│  Store  │───▶│ Predict  │───▶│ Analyze │───▶│ Notify  │
│  API   │    │   DB    │    │ Anomaly  │    │   AI    │    │ Slack/  │
│        │    │         │    │  + RUL   │    │ Copilot │    │  Jira   │
└────────┘    └─────────┘    └──────────┘    └─────────┘    └─────────┘
    │                              │                              │
    └──────── Metrics ────────────┴──── Predictions ──────────────┘
                              + SHAP Explanations
```

---

## 🛠️ Tech Stack

### Machine Learning
| Component | Technology | Purpose |
|-----------|------------|---------|
| Anomaly Detection | Isolation Forest + SHAP | Unsupervised anomaly detection with explainability |
| RUL Forecasting | LSTM (PyTorch) | Sequence-based remaining life prediction |
| Log Analysis | HDBSCAN + Sentence Transformers | Clustering similar log patterns |
| Drift Detection | Evidently | Data & concept drift monitoring |
| Experiment Tracking | MLflow | Model versioning, metrics, artifacts |

### Backend
| Component | Technology | Purpose |
|-----------|------------|---------|
| API Framework | FastAPI | Async REST API with OpenAPI docs |
| Database | PostgreSQL + SQLAlchemy | Async ORM with multi-tenancy |
| Migrations | Alembic | Database schema management |
| Auth | JWT + API Keys | Secure authentication |
| Cache | Redis | Session & result caching |

### Frontend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | Next.js 14 | React with App Router |
| Styling | TailwindCSS | Utility-first CSS |
| State | React Query | Server state management |
| Charts | Custom SVG | Animated visualizations |

### Infrastructure
| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend Hosting | Render | Container deployment |
| Frontend Hosting | Netlify | Static/SSR hosting |
| Database | Neon | Serverless PostgreSQL |
| Monitoring | UptimeRobot | Health monitoring |

---

## 📁 Project Structure

```
sensormind/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── api/v1/endpoints/   # REST endpoints
│   │   │   ├── auth.py         # Authentication
│   │   │   ├── assets.py       # Asset CRUD
│   │   │   ├── ingest.py       # Data ingestion
│   │   │   ├── predictions.py  # ML predictions
│   │   │   ├── alerts.py       # Alert management
│   │   │   ├── copilot.py      # AI agent chat
│   │   │   └── ml.py           # ML operations
│   │   ├── core/               # Config, DB, Security
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas
│   │   └── services/           # Business logic
│   ├── alembic/                # Database migrations
│   └── tests/                  # Pytest suite
│
├── ml/                         # ML Pipeline
│   ├── models/
│   │   ├── anomaly_detector.py # Isolation Forest + SHAP
│   │   ├── rul_forecaster.py   # LSTM model
│   │   └── log_analyzer.py     # HDBSCAN clustering
│   ├── agent/
│   │   ├── copilot.py          # Observe-Reason-Act agent
│   │   ├── llm_provider.py     # OpenAI/Ollama integration
│   │   └── ticket_provider.py  # Jira/ServiceNow
│   ├── pipelines/
│   │   ├── training_pipeline.py
│   │   ├── inference_pipeline.py
│   │   └── drift_detection.py
│   └── services/
│       └── ml_service.py       # MLflow orchestration
│
├── frontend/                   # Next.js Frontend
│   └── src/
│       ├── app/
│       │   ├── page.tsx        # Landing page
│       │   ├── demo/           # Interactive demo
│       │   ├── dashboard/      # Main dashboard
│       │   ├── login/          # Auth pages
│       │   └── signup/
│       ├── components/         # Reusable components
│       └── lib/                # API client
│
├── docker-compose.yml          # Local development
├── Dockerfile                  # Production build
├── render.yaml                 # Render deployment
└── netlify.toml                # Netlify deployment
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker (optional, for database)

### 1. Clone & Setup

```bash
git clone https://github.com/umangkumarchaudhary/Server-Failure-Prediction-System-MLops.git
cd Server-Failure-Prediction-System-MLops
```

### 2. Start Infrastructure

```bash
docker-compose up -d  # PostgreSQL + Redis + MLflow
```

### 3. Backend

```bash
cd backend
pip install -e ".[dev]"
alembic upgrade head   # Run migrations
uvicorn app.main:app --reload
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 5. Access

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API Docs | http://localhost:8000/docs |
| MLflow UI | http://localhost:5000 |

---

## 📡 API Reference

### Authentication

```bash
# Signup (returns API key for ingestion)
curl -X POST /api/v1/auth/signup \
  -d '{"email": "user@company.com", "password": "...", "company_name": "Acme Corp"}'

# Login (returns JWT for dashboard)
curl -X POST /api/v1/auth/login \
  -d '{"email": "user@company.com", "password": "..."}'
```

### Data Ingestion

```bash
# Send metrics (use API key)
curl -X POST /api/v1/ingest/metrics \
  -H "X-API-Key: your-api-key" \
  -d '{
    "asset_id": "pump-001",
    "metrics": [
      {"timestamp": "2026-01-12T10:00:00Z", "metric_name": "temperature", "metric_value": 85.2},
      {"timestamp": "2026-01-12T10:00:00Z", "metric_name": "vibration", "metric_value": 2.3}
    ]
  }'
```

### AI Copilot

```bash
# Chat with AI agent
curl -X POST /api/v1/copilot/chat \
  -H "Authorization: Bearer your-jwt" \
  -d '{"message": "What is the status of pump-001?"}'
```

### Full API documentation at `/docs`

---

## 📊 ML Models Deep Dive

### Anomaly Detector

```python
# Isolation Forest with SHAP Explainability
from ml.models.anomaly_detector import AnomalyDetector

detector = AnomalyDetector(contamination=0.05)
detector.fit(training_data)

# Get predictions with explanations
result = detector.predict(new_data)
# Returns: {
#   "anomaly_score": 0.87,
#   "is_anomaly": True,
#   "shap_values": {"temperature": 0.4, "vibration": 0.3, ...}
# }
```

### RUL Forecaster

```python
# LSTM with Confidence Intervals
from ml.models.rul_forecaster import RULForecaster

forecaster = RULForecaster(hidden_size=64, num_layers=2)
forecaster.fit(X_train, y_train, epochs=50)

# Predict remaining useful life
rul, confidence = forecaster.predict_with_confidence(sensor_data)
# Returns: 847 hours ± 42 hours (95% CI)
```

---

## 🧪 Testing

```bash
cd backend

# Run all tests
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest -m unit        # Unit tests only
pytest -m integration # Integration tests
pytest -m ml          # ML model tests
```

---

## 🌍 Deployment

### One-Click Deploy

| Platform | Deploy |
|----------|--------|
| Render (Backend) | Connect GitHub → Set env vars |
| Netlify (Frontend) | Import repo → Set `NEXT_PUBLIC_API_URL` |
| Neon (Database) | Create project → Copy connection string |

### Environment Variables

```env
# Backend
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key
CORS_ORIGINS=https://your-frontend.netlify.app
OPENAI_API_KEY=sk-...  # Optional, for AI Copilot

# Frontend
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com/api/v1
```

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| API Response Time | < 100ms (p95) |
| Anomaly Detection | 1000+ samples/sec |
| RUL Inference | 50ms per asset |
| Concurrent Users | 100+ (free tier) |

---

## 🗺️ Roadmap

- [x] Core ML models (Anomaly, RUL, Log Analysis)
- [x] AI Copilot with Observe-Reason-Act
- [x] Multi-tenant SaaS architecture
- [x] Real-time alerting (Slack, Email, Webhooks)
- [x] XAI with SHAP explanations
- [x] Drift detection & retraining triggers
- [x] MCP (Model Context Protocol) Server
- [ ] GPU-accelerated inference
- [ ] Kubernetes deployment
- [ ] Mobile app
- [ ] Edge deployment

---

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

<p align="center">
  <strong>Built with ❤️ for the ML community</strong>
</p>

<p align="center">
  <a href="https://server-failure-prediction-system-mlops.onrender.com/docs">API Docs</a> •
  <a href="https://sensormind.netlify.app">Live Demo</a> •
  <a href="https://github.com/umangkumarchaudhary/Server-Failure-Prediction-System-MLops">GitHub</a>
</p>
