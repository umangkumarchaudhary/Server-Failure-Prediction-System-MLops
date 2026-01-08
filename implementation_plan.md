# PredictrAI - Universal Predictive Maintenance SaaS

A multi-tenant AI platform that acts as an **"AI reliability engineer"** - not just charts and scores.

---

## Vision

Build a 2026-ready predictive maintenance platform that any company can plug into and immediately get:
- **Explainable anomaly scores** with SHAP-based feature contributions
- **AI Copilot** that drafts incidents, suggests actions, and creates tickets
- **Remaining Useful Life (RUL)** predictions using transformer models
- **NLP-powered log analysis** with root-cause extraction

---

## 2026 AI Differentiators

| Traditional PdM | PredictrAI 2026 |
|-----------------|-----------------|
| Black-box anomaly scores | **XAI**: SHAP contributions + similar incidents |
| Static dashboards | **AI Copilot**: Observe-Reason-Act automation |
| Basic thresholding | **Hybrid**: ML + physics rules + domain constraints |
| Train-once models | **Living MLOps**: Drift detection + auto-retrain |
| Single-tenant | **Multi-tenant AI observability** |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 14+, TypeScript, shadcn/ui, Tailwind, Recharts |
| **Backend** | FastAPI, Python 3.11+, async SQLAlchemy |
| **Database** | PostgreSQL with row-level security |
| **ML** | Transformers, scikit-learn, PyTorch, SHAP |
| **MLOps** | MLflow, Evidently |
| **Infra** | Docker Compose (dev), cloud-ready |

---

## Project Structure

```
predictAI/
├── frontend/                # Next.js application
│   └── src/
│       ├── app/             # App router pages
│       ├── components/      # UI components
│       └── lib/             # Utilities
├── backend/                 # FastAPI application
│   └── app/
│       ├── api/v1/          # REST endpoints
│       ├── core/            # Config, security, DB
│       ├── models/          # SQLAlchemy models
│       ├── services/        # Business logic
│       └── agents/          # AI Copilot
├── ml/                      # ML pipeline
│   ├── models/              # Anomaly, RUL, NLP
│   ├── explainability/      # SHAP integration
│   ├── pipelines/           # Training, inference
│   └── drift/               # Evidently
├── docker-compose.yml
└── README.md
```

---

## Core Components

### 1. ML Models

| Model | Purpose | Approach |
|-------|---------|----------|
| **Anomaly Detector** | Real-time anomaly scoring | Temporal Transformer + Isolation Forest hybrid |
| **RUL Forecaster** | Remaining useful life | LSTM/Transformer sequence model |
| **Log Analyzer** | Error clustering + root cause | DistilBERT embeddings + HDBSCAN |

### 2. Explainability Layer (XAI)

Every prediction includes:
- **Top features**: SHAP values showing which metrics contributed most
- **Similar incidents**: Historical cases that looked similar
- **Correlated logs**: Log clusters that appeared near the anomaly

### 3. AI Maintenance Copilot

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│ OBSERVE  │───▶│  REASON  │───▶│   ACT    │
└──────────┘    └──────────┘    └──────────┘
     │                                │
     │   Metrics, Logs, Drift         │  Alert, Ticket, Suggest
     └────────────────────────────────┘
```

**Capabilities:**
- Monitors anomalies, drift events, log patterns
- Drafts incident descriptions with context
- Suggests actions: "Reduce load on Asset X, schedule inspection"
- Creates tickets via webhooks (Jira/ServiceNow)

---

## Database Schema

```sql
-- Core multi-tenant tables
tenants(id, name, plan, api_key, created_at)
users(id, tenant_id, email, password_hash, role)
assets(id, tenant_id, name, type, tags, location, metadata)
metrics(id, tenant_id, asset_id, timestamp, metric_name, metric_value)
logs(id, tenant_id, asset_id, timestamp, raw_text, cluster_id)
predictions(id, tenant_id, asset_id, timestamp, anomaly_score, 
            risk_level, rul_estimate, explanation_json)
alerts(id, tenant_id, asset_id, severity, message, agent_suggestion, status)
incidents(id, tenant_id, asset_id, description, resolution, feedback)
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/signup` | Register tenant + user |
| POST | `/api/v1/auth/login` | JWT login |
| GET/POST | `/api/v1/assets` | Asset CRUD |
| POST | `/api/v1/ingest/metrics` | Stream metrics (API key auth) |
| POST | `/api/v1/ingest/logs` | Stream logs (API key auth) |
| POST | `/api/v1/ingest/csv` | CSV upload with mapping |
| GET | `/api/v1/predictions/{asset_id}` | Get predictions + XAI |
| GET | `/api/v1/predictions/{id}/explain` | Full explainability |
| GET | `/api/v1/alerts` | Alert list |
| POST | `/api/v1/agent/chat` | Copilot conversation |
| GET | `/api/v1/mlops/drift` | Drift metrics |

---

## Frontend Pages

| Route | Features |
|-------|----------|
| `/` | Landing page |
| `/login`, `/signup` | Authentication |
| `/dashboard` | KPI cards, anomaly trends, AI copilot widget |
| `/dashboard/assets` | Asset grid with health badges |
| `/dashboard/assets/[id]` | Metrics chart, XAI panel, logs |
| `/dashboard/copilot` | Full AI assistant chat |
| `/dashboard/alerts` | Alert table with suggestions |
| `/dashboard/mlops` | Model health, drift charts |

---

## Development Phases

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **1. Foundation** | Week 1-2 | Project setup, DB, Auth |
| **2. Core** | Week 3-4 | Assets, Ingestion, Basic UI |
| **3. ML** | Week 5-6 | Anomaly + RUL + XAI |
| **4. Agent** | Week 7-8 | AI Copilot |
| **5. Polish** | Week 9-10 | MLOps, Drift, Testing |

---

## Testing Strategy

### Unit & Integration
- Ingestion: handles missing fields, duplicates, timestamps
- Feature engineering: window computations, aggregations
- Model inference: stable outputs, shape/type checks

### ML-Specific
- Drift detection: simulated distribution shifts
- Performance regression: compare model versions

### Multi-Tenant
- Tenant isolation: data never leaks between tenants
- Rate limits: per-tenant quotas enforced

### Agent & XAI
- Agent logic: no alert spam, proper escalation
- XAI correctness: top features match ground truth

---

## Getting Started

```bash
# Start infrastructure
docker-compose up -d

# Backend
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

---

## References

- [helpreference.md](./helpreference.md) - 2026 AI trends guide
- [task.md](./task.md) - Development checklist
