# PredictrAI - Getting Started Guide

## Quick Start

### 1. Start Infrastructure
```bash
# Start PostgreSQL, Redis, MLflow
docker-compose up -d
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -e ".[dev]"

# Run migrations
alembic upgrade head

# Start backend
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start frontend
npm run dev
```

### 4. Access
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs
- **MLflow UI**: http://localhost:5000

---

## Running Tests

```bash
cd backend

# Run all unit tests (no DB required)
pytest -m unit

# Run ML tests
pytest -m ml

# Run agent tests
pytest -m agent

# Run with coverage
pytest --cov=app --cov=ml --cov-report=html
```

---

## Environment Variables

Create `.env` in `backend/`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://predictr:predictr123@localhost:5432/predictr

# Security
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Optional: OpenAI for AI Copilot
OPENAI_API_KEY=sk-...

# Optional: Email
SENDGRID_API_KEY=SG...
SENDGRID_FROM_EMAIL=alerts@yourcompany.com

# Optional: Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# Optional: Jira
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=...
```

---

## Project Structure

```
predictAI/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/  # REST endpoints
│   │   ├── core/              # Config, security
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── services/          # Email, webhooks
│   ├── alembic/               # Database migrations
│   └── tests/                 # Test suite
├── ml/
│   ├── models/                # ML models
│   ├── agent/                 # AI Copilot
│   ├── pipelines/             # Training/inference
│   └── services/              # ML orchestration
├── frontend/
│   └── src/
│       ├── app/               # Next.js pages
│       ├── components/        # React components
│       └── lib/               # API client
└── docker-compose.yml
```
