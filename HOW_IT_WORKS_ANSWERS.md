# How PredictrAI Works: Complete Answers

## Question 1: Does It Fix Issues Automatically or Just Suggest?

### Answer: **It SUGGESTS Solutions and Automates NOTIFICATIONS, but Does NOT Fix Issues Automatically**

PredictrAI is an **intelligent alerting and suggestion system**, not an automated fixer. Here's what it DOES and DOESN'T do:

---

### ✅ What PredictrAI DOES (Automatically):

#### 1. **Detects Anomalies** (Automatically)
- Continuously monitors your metrics
- Identifies anomalies using AI
- Calculates risk scores and predictions

#### 2. **Creates Alerts** (Automatically)
- Creates alert records in the system
- Generates incident reports
- Stores prediction results

#### 3. **Sends Notifications** (Automatically)
- Sends email alerts to engineers
- Sends Slack/Teams messages
- Sends SMS for critical issues
- Creates tickets in Jira/ServiceNow (if integrated)

#### 4. **Suggests Actions** (Automatically)
- AI Copilot generates specific suggestions:
  - "Check for memory leaks in application code"
  - "Restart application server to clear memory"
  - "Increase database connection pool size"
  - "Schedule maintenance within 2 hours"
  - "Scale horizontally to handle load"

#### 5. **Creates Tickets** (Automatically, if configured)
- Creates tickets in external systems (Jira, ServiceNow)
- Includes full incident description
- Includes AI-generated root cause analysis
- Includes suggested actions

---

### ❌ What PredictrAI DOES NOT Do (No Automatic Fixes):

#### 1. **Does NOT Restart Servers**
- ❌ Cannot restart your servers automatically
- ❌ Cannot reboot systems
- ❌ Cannot restart applications

#### 2. **Does NOT Fix Code**
- ❌ Cannot fix memory leaks in code
- ❌ Cannot patch bugs
- ❌ Cannot update applications

#### 3. **Does NOT Change Infrastructure**
- ❌ Cannot scale up/down servers automatically
- ❌ Cannot change database configurations
- ❌ Cannot modify infrastructure settings

#### 4. **Does NOT Deploy Fixes**
- ❌ Cannot deploy code changes
- ❌ Cannot update configurations
- ❌ Cannot run maintenance scripts

---

### Why No Automatic Fixes?

**Safety First:**
- Automatic fixes can cause more problems
- Need human verification for critical systems
- Compliance and audit requirements
- Different companies have different procedures

**But You CAN Build Automation:**
- PredictrAI can trigger webhooks to your automation systems
- You can connect it to Ansible, Terraform, Kubernetes, etc.
- Example: Webhook → Your automation → Restart server

---

### Example: Memory Leak Scenario

**What PredictrAI Does:**
1. ✅ Detects: "Memory usage at 92%, increasing at 2% per hour"
2. ✅ Predicts: "Server crash likely in 2-4 hours"
3. ✅ Creates Alert: "Critical memory pressure detected"
4. ✅ Suggests: "Restart application server, check for memory leaks"
5. ✅ Creates Ticket: Jira ticket with full details
6. ✅ Notifies: Email + Slack to on-call engineer

**What Engineer Does:**
1. Receives alert
2. Reviews AI suggestion
3. **Manually** restarts server (or uses their automation)
4. **Manually** investigates memory leak in code
5. **Manually** fixes the leak and deploys

---

### Action Types Available:

From the code, PredictrAI can automatically:

```python
ActionType.CREATE_INCIDENT      # ✅ Records incident
ActionType.CREATE_TICKET         # ✅ Creates ticket (Jira/ServiceNow)
ActionType.SEND_NOTIFICATION     # ✅ Sends email/Slack/SMS
ActionType.SUGGEST_ACTION        # ✅ Records suggestion
ActionType.SCHEDULE_MAINTENANCE  # ✅ Schedules maintenance (creates record)
ActionType.ESCALATE              # ✅ Escalates to management
```

**Note:** These are all **information/communication** actions, not **fixing** actions.

---

## Question 2: Do Companies Need Their Own Database?

### Answer: **NO! Companies Do NOT Need Any Database**

PredictrAI is a **fully managed SaaS** - companies just send data via API, and PredictrAI handles everything.

---

### How It Works:

#### 1. **Companies Send Data (No Database Needed)**
```python
# Company just sends metrics via API (no database on their side)
POST /api/v1/ingest/metrics
{
  "data": [
    {
      "asset_id": "web-server-01",
      "metric_name": "cpu_usage",
      "metric_value": 85.5,
      "timestamp": "2026-01-15T10:00:00Z"
    }
  ]
}
```

#### 2. **PredictrAI Stores Everything (In Our Database)**
- PredictrAI has its own PostgreSQL database
- All metrics, logs, predictions stored in PredictrAI's database
- Companies don't need to set up anything

#### 3. **Multi-Tenant Architecture**
- Each company (tenant) gets isolated data
- All stored in PredictrAI's central database
- Row-level security ensures data isolation
- Companies cannot see each other's data

---

### What Companies Need:

#### ✅ Required:
- **API Access:** Just send HTTP requests (REST API)
- **API Key:** For authentication (PredictrAI provides this)
- **Monitoring Tools:** To collect metrics (Prometheus, Datadog, custom scripts, etc.)

#### ❌ NOT Required:
- ❌ **No Database:** Companies don't need PostgreSQL, MySQL, etc.
- ❌ **No Infrastructure:** Companies don't need servers for PredictrAI
- ❌ **No Installation:** Just API calls
- ❌ **No Maintenance:** PredictrAI handles everything

---

### Example Setup (Company Side):

**Option 1: Simple Script**
```python
# predictr-sender.py (runs every 60 seconds)
import psutil
import requests

metrics = [
    {"metric_name": "cpu_usage", "metric_value": psutil.cpu_percent()},
    {"metric_name": "memory_usage", "metric_value": psutil.virtual_memory().percent},
]

requests.post(
    'https://api.predictrai.com/api/v1/ingest/metrics',
    headers={'X-API-Key': 'your-api-key'},
    json={'data': metrics}
)
```

**Option 2: Use Existing Monitoring**
- Prometheus → PredictrAI (via exporter)
- Datadog → PredictrAI (via API)
- New Relic → PredictrAI (via webhook)

**Option 3: Cloud Agents**
- Deploy lightweight agent on servers
- Agent collects metrics and sends to PredictrAI
- No database needed on company side

---

### PredictrAI's Database Structure:

```
PredictrAI Database (PostgreSQL)
├── tenants (company accounts)
├── users (company users)
├── assets (company equipment)
├── metrics (company metrics) ← Stored here
├── logs (company logs) ← Stored here
├── predictions (AI predictions) ← Stored here
├── alerts (alerts for company) ← Stored here
└── incidents (incidents for company) ← Stored here
```

**All in PredictrAI's database - companies don't need any database!**

---

## Question 3: How Is It Trained? What Data?

### Answer: **It's Trained on EACH COMPANY'S OWN DATA (Per-Tenant Training)**

PredictrAI does NOT use pre-trained models. Instead, it learns from **your specific data** after you start sending metrics.

---

### Training Process:

#### **Step 1: Company Starts Sending Data**
```
Day 1: Company sends first metrics
Day 7: Company has collected data for a week
Day 30: Company has collected enough data
```

#### **Step 2: PredictrAI Trains Models for That Company**
```python
# When company has enough data, PredictrAI trains:
train_anomaly_detector(tenant_id="company-123", data=company_data)
train_rul_forecaster(tenant_id="company-123", data=company_data)
train_log_analyzer(tenant_id="company-123", logs=company_logs)
```

#### **Step 3: Each Company Gets Its Own Model**
- Company A → Model trained on Company A's data
- Company B → Model trained on Company B's data
- Company C → Model trained on Company C's data

**Each model learns what's "normal" for that specific company!**

---

### Training Data Requirements:

#### **Anomaly Detection:**
- **Minimum:** 100 data points (metrics)
- **Optimal:** 1,000+ data points
- **Data:** Your own metrics (CPU, memory, response time, etc.)
- **Training:** Learns what's "normal" for YOUR systems

#### **RUL Forecasting:**
- **Minimum:** 500 data points with failure history
- **Optimal:** 5,000+ data points
- **Data:** Your metrics + failure timestamps
- **Training:** Learns failure patterns for YOUR equipment

#### **Log Analysis:**
- **Minimum:** 50 log messages
- **Optimal:** 1,000+ log messages
- **Data:** Your own application logs
- **Training:** Learns error patterns for YOUR applications

---

### What Data Is Used for Training?

#### **1. Metrics (For Anomaly Detection & RUL)**
```
Training Data Example:
- Timestamp: 2026-01-01 10:00:00
- CPU Usage: 45%
- Memory Usage: 65%
- Response Time: 200ms
- Error Rate: 0.2%
...
```

**The model learns:**
- "For this company, normal CPU is 40-50%"
- "For this company, normal memory is 60-70%"
- "When CPU goes to 85% AND memory to 92%, that's unusual"

#### **2. Logs (For Log Analysis)**
```
Training Data Example:
- "2026-01-01 10:00:00 INFO System started"
- "2026-01-01 10:05:00 ERROR Connection failed"
- "2026-01-01 10:10:00 WARNING High load detected"
...
```

**The model learns:**
- Common error patterns in your logs
- Clusters similar errors together
- Identifies root causes

#### **3. Failure History (For RUL)**
```
Training Data Example:
- Asset failed on: 2026-01-15 14:30:00
- Metrics before failure: CPU 95%, Memory 98%
- Pattern: Memory increased from 70% to 98% over 3 hours
```

**The model learns:**
- "When memory increases like this, failure happens in 3 hours"
- Predicts remaining useful life based on patterns

---

### Training Schedule:

#### **Initial Training:**
- Happens automatically when you have enough data
- Triggered when:
  - Anomaly: 100+ data points collected
  - RUL: 500+ data points collected
  - Logs: 50+ log messages collected

#### **Ongoing Retraining:**
- **Nightly:** Models retrain every night with new data
- **Drift Detection:** Retrains if data distribution changes
- **Auto-Update:** Models continuously improve with more data

---

### Why Per-Tenant Training?

#### **Different Companies = Different Normals**

**Example 1: Website vs Factory**
- Website: Normal CPU 30-50%, Normal Memory 60-80%
- Factory: Normal CPU 60-80%, Normal Memory 40-60%
- **Same metrics, different "normal"!**

**Example 2: High-Traffic vs Low-Traffic**
- High-traffic: Normal response time 100-300ms
- Low-traffic: Normal response time 50-150ms
- **Same metric, different baselines!**

**Example 3: Day vs Night**
- Day: Normal traffic 10,000 requests/min
- Night: Normal traffic 1,000 requests/min
- **Model learns YOUR patterns!**

---

### Training Code (How It Works):

```python
# From training_pipeline.py

async def train_tenant_models(tenant_id: str):
    # Step 1: Fetch THIS company's data
    metrics_data = await fetch_metrics_data(tenant_id)
    logs_data = await fetch_logs_data(tenant_id)
    
    # Step 2: Train models on THIS company's data
    if len(metrics_data) >= 100:
        anomaly_detector.fit(metrics_data)  # Learns THIS company's normal
    
    if len(metrics_data) >= 500:
        rul_forecaster.fit(metrics_data)  # Learns THIS company's failure patterns
    
    if len(logs_data) >= 50:
        log_analyzer.fit(logs_data)  # Learns THIS company's log patterns
    
    # Step 3: Save model for THIS company
    save_model(tenant_id, anomaly_detector)
```

---

### Data Privacy & Security:

- ✅ **Isolated Training:** Each company's model trained only on their data
- ✅ **No Cross-Contamination:** Company A's data never used for Company B
- ✅ **Encryption:** All data encrypted in transit and at rest
- ✅ **Row-Level Security:** Database ensures data isolation
- ✅ **Compliance:** GDPR, SOC 2, HIPAA compliant

---

### Timeline Example:

**Week 1: Initial Setup**
- Company signs up
- Gets API key
- Starts sending metrics
- **No model yet** (need more data)

**Week 2-3: Data Collection**
- Metrics accumulating: 200 points
- Logs accumulating: 150 messages
- **Still collecting data**

**Week 4: First Training**
- Metrics: 1,000+ points ✅
- Logs: 500+ messages ✅
- **Automatic training triggered!**
- Models created for this company
- Anomaly detection starts working

**Week 5+: Continuous Improvement**
- More data = Better models
- Nightly retraining
- Models improve over time

---

## Summary

### 1. **Fixing Issues:**
- ✅ **Suggests solutions** automatically
- ✅ **Sends alerts** automatically
- ✅ **Creates tickets** automatically
- ❌ **Does NOT fix** automatically (for safety)
- ✅ **CAN trigger** your automation via webhooks

### 2. **Database:**
- ❌ **Companies do NOT need database**
- ✅ **PredictrAI provides everything**
- ✅ **Just send data via API**
- ✅ **Fully managed SaaS**

### 3. **Training:**
- ✅ **Trained on YOUR data** (per-tenant)
- ✅ **Learns YOUR normal patterns**
- ✅ **No pre-trained models**
- ✅ **Automatic training** when enough data
- ✅ **Continuous improvement** over time

---

## Real-World Example

**Company: E-commerce Website**

**Setup (No Database Needed):**
1. Signs up for PredictrAI
2. Gets API key
3. Deploys simple script to send metrics
4. Starts sending CPU, memory, response time

**Training (Automatic):**
1. Week 1-3: Data collection
2. Week 4: Model trains automatically on company's data
3. Model learns: "For this website, normal CPU is 40-60%, normal response time is 100-250ms"

**Detection (Automatic Suggestions):**
1. CPU spikes to 85%, memory to 92%
2. AI detects anomaly (score: 0.87)
3. AI suggests: "Memory leak detected, restart app server, check code"
4. AI creates Jira ticket with full details
5. Engineer receives alert, manually fixes issue

**No database needed, fully automatic suggestions, trained on company's own data!**

