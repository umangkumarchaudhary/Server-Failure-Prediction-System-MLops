# PredictrAI - Client Demo Guide

Complete guide for showcasing PredictrAI to potential clients.

---

## Table of Contents

1. [Pre-Demo Setup](#pre-demo-setup)
2. [Demo Scenarios](#demo-scenarios)
3. [Step-by-Step Walkthrough](#step-by-step-walkthrough)
4. [Talking Points](#talking-points)
5. [Sample Data Script](#sample-data-script)
6. [Visual Demo Flow](#visual-demo-flow)

---

## Pre-Demo Setup

### 1. Start the System

```bash
# Terminal 1: Start infrastructure
docker-compose up -d

# Terminal 2: Start backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Terminal 3: Start frontend
cd frontend
npm install
npm run dev
```

### 2. Verify Everything is Running

- ✅ Frontend: http://localhost:3000
- ✅ Backend API: http://localhost:8000/docs
- ✅ MLflow: http://localhost:5000
- ✅ Database: PostgreSQL on port 5432

### 3. Create Demo Account

```bash
# Use API or UI to create a demo tenant
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@client.com",
    "password": "demo123",
    "company_name": "Demo Company"
  }'
```

### 4. Load Sample Data

Run the sample data script (see below) to populate the demo.

---

## Demo Scenarios

### Scenario 1: Website Server Downtime Prediction (Most Impressive)

**Story:** "Let's imagine we're monitoring an e-commerce website server. PredictrAI predicts it will crash in 2 hours due to a memory leak, giving the team time to fix it before downtime occurs."

**What to Show:**
1. Server asset with normal metrics
2. Memory starts increasing (anomaly detected)
3. AI explains WHY (memory leak)
4. AI predicts WHEN (2-4 hours)
5. AI suggests HOW to fix (restart server, check code)
6. Alert created and ticket generated

### Scenario 2: Manufacturing Equipment Failure

**Story:** "A manufacturing company monitors their production line equipment. PredictrAI detects abnormal vibration patterns and predicts the machine will fail in 48 hours."

**What to Show:**
1. Machine asset with vibration sensors
2. Anomaly in vibration metrics
3. RUL prediction (48 hours remaining)
4. Maintenance scheduling suggestion
5. Historical similar incidents

### Scenario 3: Database Connection Exhaustion

**Story:** "A website's database connection pool is approaching exhaustion. PredictrAI detects this early and alerts the team before the site goes down."

**What to Show:**
1. Database connections increasing
2. Response time degrading
3. Anomaly score rising
4. AI explains: "DB connections at 98% of max"
5. Suggested action: "Increase connection pool size"
6. Alert and ticket created

---

## Step-by-Step Walkthrough

### Part 1: Introduction (5 minutes)

**Opening:**
> "PredictrAI is an AI-powered predictive maintenance platform. Instead of reacting to failures after they happen, we predict them hours or days in advance, giving your team time to prevent downtime."

**Key Points:**
- Traditional monitoring: Alerts after failure
- PredictrAI: Predicts failure BEFORE it happens
- Works for any asset type (servers, machines, vehicles, etc.)
- No database needed on client side - fully managed SaaS

**Show:**
- Landing page (http://localhost:3000)
- Walk through features

---

### Part 2: Dashboard Overview (3 minutes)

**Navigate to:** `/dashboard`

**What to Highlight:**
- Total assets, healthy/warning/critical counts
- Active alerts
- Anomalies detected in last 24h
- Recent assets with health scores

**Say:**
> "This is your command center. You see all assets at a glance, with health scores and risk levels. Green means healthy, yellow means warning, red means critical."

**Show:**
- Stats cards
- Recent assets list
- Active alerts panel

---

### Part 3: Asset Management (3 minutes)

**Navigate to:** `/dashboard/assets`

**What to Show:**
1. **Asset List:**
   - Multiple assets (servers, machines, etc.)
   - Health scores
   - Risk levels (normal/warning/critical)

2. **Create New Asset:**
   - Click "Add Asset"
   - Fill in: Name, Type, Location
   - Show asset creation

3. **Asset Detail:**
   - Click on an asset
   - Show metrics charts
   - Show health score
   - Show recent predictions

**Say:**
> "Assets can be anything - servers, manufacturing equipment, vehicles. Each asset gets a health score and risk level that updates in real-time."

---

### Part 4: Real-Time Anomaly Detection (8 minutes) - **KEY DEMO**

**This is the most impressive part!**

#### Step 1: Show Normal Metrics

**Navigate to:** `/dashboard/assets/{asset_id}`

**Show:**
- Metrics chart showing normal values:
  - CPU: 40-50%
  - Memory: 60-70%
  - Response Time: 100-300ms
  - Error Rate: 0.1-0.5%

**Say:**
> "This is a normal, healthy server. The AI has learned what normal looks like for this specific asset."

#### Step 2: Simulate Anomaly

**Use the API to inject anomaly data:**

```bash
# Send metrics showing memory leak
curl -X POST http://localhost:8000/api/v1/ingest/metrics \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {
        "asset_id": "ASSET_ID",
        "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
        "metric_name": "memory_usage",
        "metric_value": 92.5
      },
      {
        "asset_id": "ASSET_ID",
        "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
        "metric_name": "cpu_usage",
        "metric_value": 87.3
      },
      {
        "asset_id": "ASSET_ID",
        "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
        "metric_name": "response_time_ms",
        "metric_value": 1250.0
      }
    ]
  }'
```

**Refresh the page** to show updated metrics.

**Say:**
> "Now watch what happens when we simulate a problem. The server's memory usage is spiking to 92%, CPU is at 87%, and response time has increased to 1.2 seconds. This is a memory leak scenario."

#### Step 3: Show Anomaly Detection

**Navigate to:** Predictions section or alerts

**Show:**
- Anomaly Score: 0.87 (CRITICAL)
- Risk Level: Critical
- Prediction timestamp

**Say:**
> "PredictrAI has detected an anomaly with a score of 0.87 - that's critical. It's not just detecting the problem, it's explaining WHY."

#### Step 4: Show Explainability (SHAP)

**Show:**
- Top Contributing Factors:
  1. Memory Usage (92%) → +0.35 contribution
  2. CPU Usage (87%) → +0.28 contribution
  3. Response Time (1250ms) → +0.18 contribution

**Say:**
> "This is the explainability feature. Instead of a black box, you see exactly which metrics contributed to the alert. Memory usage is the biggest culprit, suggesting a memory leak."

#### Step 5: Show Prediction (RUL)

**Show:**
- RUL Estimate: "2-4 hours until server crash"
- Confidence: 85%
- Based on similar historical incidents

**Say:**
> "Most importantly, PredictrAI predicts when the failure will happen. Based on similar patterns in the past, it estimates the server will crash in 2-4 hours if nothing is done. This gives your team time to fix it proactively."

#### Step 6: Show AI Copilot Suggestion

**Navigate to:** Alerts or Copilot section

**Show:**
- Alert with AI suggestion:
  - "Memory leak detected - memory usage at 92% and increasing"
  - Suggested Actions:
    1. Restart application server to clear memory
    2. Check application code for memory leaks
    3. Monitor memory usage closely
    4. Consider increasing server memory

**Say:**
> "The AI Copilot doesn't just alert you - it suggests specific actions. Here it's recommending to restart the server and check for memory leaks. It can even create tickets automatically."

#### Step 7: Show Ticket Creation

**Navigate to:** Alerts section

**Show:**
- Ticket created in Jira/ServiceNow (if configured)
- Ticket includes:
  - Full incident description
  - Root cause analysis
  - Suggested actions
  - Timeline prediction

**Say:**
> "PredictrAI automatically creates tickets in your ticketing system with all the context. Your engineers get a complete picture immediately, not just an alert."

---

### Part 5: AI Copilot Chat (5 minutes)

**Navigate to:** `/dashboard/copilot` or Copilot widget

**Demonstrate:**
1. Ask: "What anomalies did we detect today?"
   - Shows recent anomalies with explanations

2. Ask: "What's the health of web-server-01?"
   - Shows asset health, risk level, recent predictions

3. Ask: "What should I do about the memory leak alert?"
   - Shows detailed suggestions and steps

4. Ask: "Show me similar incidents"
   - Shows historical incidents with similar patterns

**Say:**
> "The AI Copilot is like having a reliability engineer on your team 24/7. You can ask it anything about your assets, and it provides context-aware answers."

---

### Part 6: Log Analysis (5 minutes)

**Navigate to:** Asset detail → Logs section

**Show:**
- Log messages
- Clustered errors (similar errors grouped)
- Root cause suggestions
- Correlation with anomalies

**Say:**
> "PredictrAI also analyzes your logs using NLP. It clusters similar errors together, so instead of seeing thousands of log messages, you see patterns. It correlates logs with anomalies to help identify root causes."

**Show:**
- Error clusters
- Top error patterns
- Correlation: "These errors appeared right before the anomaly"

---

### Part 7: MLOps Dashboard (3 minutes)

**Navigate to:** `/dashboard/mlops`

**Show:**
- Model performance metrics
- Drift detection
- Training history
- Model versioning

**Say:**
> "This is the MLOps dashboard. PredictrAI continuously monitors model performance and automatically retrains when data patterns change. This ensures predictions stay accurate as your systems evolve."

**Show:**
- Drift detected notification
- Auto-retraining status
- Model performance trends

---

### Part 8: Integration (3 minutes)

**Show:**
- API documentation (http://localhost:8000/docs)
- Webhook configuration
- Integration options

**Say:**
> "Integration is simple. Companies send metrics via REST API - no database needed. You can use existing monitoring tools like Prometheus, Datadog, or custom scripts. PredictrAI also sends webhooks to trigger your automation systems."

**Show:**
- API endpoints
- Sample curl commands
- Webhook configuration

---

## Talking Points

### Opening Hook

> "Imagine if you could predict when your website will crash 2 hours before it happens. Or know that a production machine will fail in 48 hours, so you can schedule maintenance proactively. That's what PredictrAI does."

### Key Differentiators

1. **Predictive vs Reactive**
   > "Traditional monitoring tells you something is wrong NOW. PredictrAI tells you something will go wrong in 2-4 hours, giving you time to prevent it."

2. **Explainable AI**
   > "It's not a black box. When PredictrAI detects an anomaly, it shows you exactly which metrics caused it and why. You see the reasoning, not just a score."

3. **AI Copilot**
   > "It's like having a reliability engineer on your team. It doesn't just alert you - it drafts incidents, suggests actions, and creates tickets automatically."

4. **Multi-Industry**
   > "Works for any asset type - websites, manufacturing equipment, vehicles, data centers. One platform, any industry."

5. **No Infrastructure Needed**
   > "Fully managed SaaS. Companies just send data via API - no database, no infrastructure, no maintenance."

### Objections Handling

**"We already have monitoring (Datadog/New Relic)"**
> "That's great! PredictrAI works alongside your existing tools. You can send data from Datadog to PredictrAI for AI-powered predictions, while keeping your existing monitoring."

**"How accurate are the predictions?"**
> "The AI learns from your specific data and patterns. After collecting data for a few weeks, predictions are typically 85-95% accurate. And it explains WHY it made each prediction, so you can verify."

**"What if the AI is wrong?"**
> "That's why we show explainability - you can see the reasoning. If an alert is incorrect, you can provide feedback, and the model learns from it. Also, it only suggests actions - you decide what to do."

**"How long does it take to set up?"**
> "Literally minutes. You get an API key, send metrics via REST API, and the system starts learning. After 1-2 weeks of data collection, models train automatically and predictions begin."

**"Do we need data scientists?"**
> "No! The AI handles everything automatically. Companies just send metrics and receive predictions. No ML expertise needed."

---

## Sample Data Script

Create a file `demo_data_loader.py`:

```python
"""
Demo Data Loader - Populates PredictrAI with sample data for demos
"""
import requests
import time
from datetime import datetime, timedelta
import random

API_BASE = "http://localhost:8000/api/v1"
API_KEY = "YOUR_API_KEY"  # Get from signup/login

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def create_demo_assets():
    """Create demo assets."""
    assets = [
        {"name": "Web Server 01", "type": "server", "location": "Data Center A"},
        {"name": "Web Server 02", "type": "server", "location": "Data Center A"},
        {"name": "Production Line Machine A", "type": "machine", "location": "Factory Floor"},
        {"name": "Database Server", "type": "server", "location": "Data Center B"},
        {"name": "Load Balancer", "type": "server", "location": "Data Center A"},
    ]
    
    asset_ids = []
    for asset in assets:
        response = requests.post(
            f"{API_BASE}/assets",
            headers=headers,
            json=asset
        )
        if response.status_code == 200:
            asset_ids.append(response.json()["id"])
            print(f"Created asset: {asset['name']}")
    
    return asset_ids

def send_normal_metrics(asset_id, hours=24):
    """Send normal metrics for an asset."""
    base_time = datetime.utcnow() - timedelta(hours=hours)
    
    for i in range(hours * 6):  # Every 10 minutes
        timestamp = base_time + timedelta(minutes=i * 10)
        
        metrics = [
            {
                "asset_id": asset_id,
                "timestamp": timestamp.isoformat() + "Z",
                "metric_name": "cpu_usage",
                "metric_value": random.uniform(40, 55)  # Normal: 40-55%
            },
            {
                "asset_id": asset_id,
                "timestamp": timestamp.isoformat() + "Z",
                "metric_name": "memory_usage",
                "metric_value": random.uniform(60, 75)  # Normal: 60-75%
            },
            {
                "asset_id": asset_id,
                "timestamp": timestamp.isoformat() + "Z",
                "metric_name": "response_time_ms",
                "metric_value": random.uniform(100, 300)  # Normal: 100-300ms
            },
            {
                "asset_id": asset_id,
                "timestamp": timestamp.isoformat() + "Z",
                "metric_name": "error_rate",
                "metric_value": random.uniform(0.1, 0.5)  # Normal: 0.1-0.5%
            },
            {
                "asset_id": asset_id,
                "timestamp": timestamp.isoformat() + "Z",
                "metric_name": "request_rate",
                "metric_value": random.uniform(8000, 12000)  # Normal: 8k-12k/min
            },
        ]
        
        response = requests.post(
            f"{API_BASE}/ingest/metrics",
            headers=headers,
            json={"data": metrics}
        )
        
        if response.status_code == 200:
            print(f"Sent metrics for {asset_id} at {timestamp}")
        
        time.sleep(0.1)  # Rate limiting

def send_anomaly_metrics(asset_id, start_hours_ago=2):
    """Send metrics showing an anomaly (memory leak)."""
    base_time = datetime.utcnow() - timedelta(hours=start_hours_ago)
    
    # Simulate memory leak - memory increases over time
    for i in range(12):  # Last 2 hours, every 10 minutes
        timestamp = base_time + timedelta(minutes=i * 10)
        progress = i / 12  # 0 to 1
        
        # Memory starts at 70%, increases to 92%
        memory = 70 + (progress * 22)
        # CPU follows memory
        cpu = 50 + (progress * 37)
        # Response time degrades
        response_time = 200 + (progress * 1050)
        # Error rate increases
        error_rate = 0.3 + (progress * 4.7)
        
        metrics = [
            {
                "asset_id": asset_id,
                "timestamp": timestamp.isoformat() + "Z",
                "metric_name": "memory_usage",
                "metric_value": round(memory, 2)
            },
            {
                "asset_id": asset_id,
                "timestamp": timestamp.isoformat() + "Z",
                "metric_name": "cpu_usage",
                "metric_value": round(cpu, 2)
            },
            {
                "asset_id": asset_id,
                "timestamp": timestamp.isoformat() + "Z",
                "metric_name": "response_time_ms",
                "metric_value": round(response_time, 2)
            },
            {
                "asset_id": asset_id,
                "timestamp": timestamp.isoformat() + "Z",
                "metric_name": "error_rate",
                "metric_value": round(error_rate, 2)
            },
        ]
        
        response = requests.post(
            f"{API_BASE}/ingest/metrics",
            headers=headers,
            json={"data": metrics}
        )
        
        if response.status_code == 200:
            print(f"Sent anomaly metrics for {asset_id} at {timestamp} (Memory: {memory:.1f}%)")
        
        time.sleep(0.1)

def send_logs(asset_id, num_logs=50):
    """Send sample logs."""
    log_samples = [
        "INFO Application started successfully",
        "INFO Database connection established",
        "WARNING High CPU usage detected: 75%",
        "ERROR Failed to connect to external API",
        "ERROR Database connection timeout",
        "INFO User login successful",
        "WARNING Memory usage above 80%",
        "ERROR OutOfMemoryError in cache module",
        "INFO Scheduled task completed",
        "ERROR 500 Internal Server Error on /api/users",
    ]
    
    base_time = datetime.utcnow() - timedelta(hours=24)
    
    for i in range(num_logs):
        timestamp = base_time + timedelta(minutes=i * 30)
        log_message = random.choice(log_samples)
        
        log_data = {
            "data": [{
                "asset_id": asset_id,
                "timestamp": timestamp.isoformat() + "Z",
                "raw_text": f"{timestamp.isoformat()} {log_message}"
            }]
        }
        
        response = requests.post(
            f"{API_BASE}/ingest/logs",
            headers=headers,
            json=log_data
        )
        
        if response.status_code == 200:
            print(f"Sent log for {asset_id}: {log_message}")

def main():
    """Main function to load demo data."""
    print("🚀 Loading demo data for PredictrAI...")
    
    # Step 1: Create assets
    print("\n1. Creating demo assets...")
    asset_ids = create_demo_assets()
    
    if not asset_ids:
        print("❌ Failed to create assets. Check API key and connection.")
        return
    
    # Step 2: Send normal metrics (historical data)
    print("\n2. Sending normal metrics (historical data)...")
    for asset_id in asset_ids[:3]:  # First 3 assets
        send_normal_metrics(asset_id, hours=48)
    
    # Step 3: Send anomaly metrics (for demo asset)
    print("\n3. Sending anomaly metrics (memory leak simulation)...")
    if asset_ids:
        send_anomaly_metrics(asset_ids[0])  # First asset has anomaly
    
    # Step 4: Send logs
    print("\n4. Sending sample logs...")
    for asset_id in asset_ids[:3]:
        send_logs(asset_id, num_logs=30)
    
    print("\n✅ Demo data loaded successfully!")
    print(f"\n📊 Demo Asset ID: {asset_ids[0]}")
    print(f"🌐 View dashboard: http://localhost:3000/dashboard/assets/{asset_ids[0]}")

if __name__ == "__main__":
    main()
```

**Usage:**
```bash
# Get API key from signup/login first
python demo_data_loader.py
```

---

## Visual Demo Flow

### Recommended Demo Sequence (30 minutes)

1. **Landing Page** (2 min)
   - Show features
   - Explain value proposition

2. **Dashboard** (3 min)
   - Overview of assets
   - Health scores

3. **Asset Management** (3 min)
   - Create asset
   - View asset details

4. **Anomaly Detection** (10 min) ⭐ **MAIN DEMO**
   - Normal metrics
   - Inject anomaly
   - Show detection
   - Show explainability
   - Show prediction
   - Show suggestions

5. **AI Copilot** (5 min)
   - Chat interface
   - Ask questions

6. **Log Analysis** (3 min)
   - Error clustering
   - Root cause correlation

7. **MLOps** (2 min)
   - Model monitoring
   - Auto-retraining

8. **Integration** (2 min)
   - API documentation
   - Webhooks

---

## Quick Demo Script (15-minute version)

If short on time:

1. Show dashboard (1 min)
2. Show normal asset (1 min)
3. Inject anomaly + show detection (5 min) ⭐
4. Show AI Copilot suggestions (3 min)
5. Show explainability (3 min)
6. Q&A (2 min)

---

## Tips for Successful Demo

1. **Prepare Sample Data:** Load demo data before the meeting
2. **Test Everything:** Verify all features work before demo
3. **Have Backup:** Prepare screenshots/videos if live demo fails
4. **Focus on Value:** Emphasize business impact, not just technology
5. **Tell a Story:** Use real-world scenarios (website crash, machine failure)
6. **Be Interactive:** Ask client about their pain points during demo
7. **Handle Questions:** Prepare answers for common objections

---

## Post-Demo Follow-Up

**Send:**
- Demo recording (if recorded)
- Presentation slides
- API documentation link
- Case studies
- Pricing information

**Next Steps:**
- Schedule technical deep-dive
- Provide trial access
- Discuss integration timeline

---

## Troubleshooting

**Issue: Demo data not showing**
- Check API key is correct
- Verify backend is running
- Check database connection

**Issue: Anomaly not detected**
- Ensure enough historical data (100+ points)
- Verify model is trained
- Check anomaly threshold settings

**Issue: Frontend not loading**
- Check if frontend is running on port 3000
- Clear browser cache
- Check console for errors

---

Good luck with your demo! 🚀

