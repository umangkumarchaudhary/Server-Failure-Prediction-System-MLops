# 🧠 SensorMind

**AI-Powered Predictive Maintenance Platform**

Prevent equipment failures before they happen with intelligent anomaly detection, RUL forecasting, and an autonomous AI maintenance agent.

---

## ✨ Key Features

| Feature | Technology |
|---------|------------|
| **Anomaly Detection** | Isolation Forest + SHAP Explainability |
| **RUL Forecasting** | LSTM Neural Network with Confidence Intervals |
| **Log Analysis** | HDBSCAN + Sentence Transformers |
| **AI Copilot Agent** | Observe-Reason-Act with LLM (OpenAI/Ollama) |
| **Drift Detection** | Evidently for Data & Concept Drift |
| **MLOps** | MLflow Experiment Tracking |
| **Notifications** | Slack, Teams, Email, Webhooks |
| **Ticket Integration** | Jira, ServiceNow |

---

## 🛠️ Tech Stack

### ML/AI
- Isolation Forest, LSTM (PyTorch), HDBSCAN
- SHAP, Evidently, MLflow
- AI Agent with LLM integration

### Backend
- FastAPI, SQLAlchemy (Async), PostgreSQL
- Multi-tenant SaaS architecture
- JWT Auth, API Key ingestion

### Frontend
- Next.js 14, TypeScript, TailwindCSS
- Real-time dashboards, Animated demo

### Deployment
- Render (Backend), Netlify (Frontend), Supabase (DB)
- Docker, Alembic migrations

---

## 🚀 Quick Start

```bash
# Start infrastructure
docker-compose up -d

# Backend
cd backend
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

**Access:**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- MLflow: http://localhost:5000

---

## 📁 Project Structure

```
sensormind/
├── backend/          # FastAPI backend
│   ├── app/          # API endpoints, models, schemas
│   ├── alembic/      # Database migrations
│   └── tests/        # Test suite
├── ml/               # ML models & agent
│   ├── models/       # Anomaly, RUL, Log analyzers
│   ├── agent/        # AI Copilot
│   ├── pipelines/    # Training & inference
│   └── services/     # MLService orchestration
├── frontend/         # Next.js frontend
└── docker-compose.yml
```

---

## 📊 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /auth/signup` | Register tenant + user |
| `POST /ingest/metrics` | Stream sensor data |
| `GET /predictions/asset/{id}` | Get predictions |
| `POST /copilot/chat` | Chat with AI agent |
| `GET /dashboard/stats` | Dashboard data |

---

## 🌐 Live Demo

- **Demo Page**: Experience all features with live animations
- **API Docs**: Interactive Swagger documentation
- **GitHub**: Full source code

---

## 📜 License

MIT License - Build amazing things!

---

**Built with ❤️ for the ML community**
