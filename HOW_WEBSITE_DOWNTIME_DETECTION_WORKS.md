# How PredictrAI Detects Website Downtime

## Overview

PredictrAI doesn't directly monitor your website. Instead, **you send metrics and logs** from your website/server infrastructure, and the AI system analyzes patterns to predict potential failures **before they happen**.

---

## How It Works: Step-by-Step

### Step 1: You Send Metrics & Logs

Your monitoring tools (Prometheus, Datadog, New Relic, custom scripts, etc.) collect server metrics and send them to PredictrAI via API:

```json
POST /api/v1/ingest/metrics
{
  "data": [
    {
      "asset_id": "web-server-01",
      "timestamp": "2026-01-15T10:00:00Z",
      "metric_name": "cpu_usage",
      "metric_value": 85.5
    },
    {
      "asset_id": "web-server-01",
      "timestamp": "2026-01-15T10:00:00Z",
      "metric_name": "memory_usage",
      "metric_value": 92.3
    },
    {
      "asset_id": "web-server-01",
      "timestamp": "2026-01-15T10:00:00Z",
      "metric_name": "response_time_ms",
      "metric_value": 1250.0
    },
    {
      "asset_id": "web-server-01",
      "timestamp": "2026-01-15T10:00:00Z",
      "metric_name": "error_rate",
      "metric_value": 5.2
    },
    {
      "asset_id": "web-server-01",
      "timestamp": "2026-01-15T10:00:00Z",
      "metric_name": "request_rate",
      "metric_value": 12500.0
    },
    {
      "asset_id": "web-server-01",
      "timestamp": "2026-01-15T10:00:00Z",
      "metric_name": "database_connections",
      "metric_value": 980
    }
  ]
}
```

### Step 2: AI Analyzes Patterns (Anomaly Detection)

The system uses **Isolation Forest ML algorithm** to learn normal patterns from historical data, then identifies anomalies:

**Normal Pattern:**
```
CPU: 30-50%, Memory: 50-70%, Response Time: 100-300ms, Error Rate: 0.1-0.5%
```

**Anomaly Pattern (Early Warning):**
```
CPU: 85% ↗️, Memory: 92% ↗️, Response Time: 1250ms ↗️, Error Rate: 5.2% ↗️
→ AI Detects: "This combination is unusual and indicates potential failure"
```

### Step 3: Explainability (SHAP Values)

The AI explains **WHY** it detected an anomaly:

```
Anomaly Score: 0.87 (CRITICAL)

Top Contributing Factors:
1. Memory Usage (92.3%) → Contributed +0.35 to anomaly score
2. Database Connections (980/1000) → Contributed +0.28 to anomaly score  
3. Response Time (1250ms vs normal 200ms) → Contributed +0.18 to anomaly score
4. CPU Usage (85%) → Contributed +0.12 to anomaly score

Similar Historical Incidents:
- Incident #1234 (2025-12-10): Memory leak caused website crash 4 hours later
- Incident #1156 (2025-11-22): Database connection exhaustion led to 30-min downtime
```

### Step 4: AI Copilot Takes Action

The AI Copilot automatically:
- ✅ Creates an alert: "Memory usage at 92% - potential memory leak detected"
- ✅ Suggests action: "Check for memory leaks, restart app server, increase DB connection pool"
- ✅ Creates ticket in Jira: "Web Server 01 - Critical memory pressure detected"
- ✅ Sends notification to on-call engineer

---

## Real Examples: What Metrics Indicate Website Will Go Down

### Example 1: Memory Leak → Server Crash

**Metrics Sent:**
```
Time 10:00 - Memory: 70%, CPU: 50%, Errors: 0.2%
Time 11:00 - Memory: 78%, CPU: 55%, Errors: 0.3%
Time 12:00 - Memory: 85%, CPU: 60%, Errors: 0.8%
Time 13:00 - Memory: 92%, CPU: 65%, Errors: 2.1% ⚠️
```

**AI Detection:**
- **Anomaly Score:** 0.82 (WARNING at 13:00)
- **Prediction:** "Memory increasing steadily with no release - likely memory leak"
- **RUL Estimate:** "Estimated 2-4 hours until server crash or forced restart"
- **Action:** "Schedule memory leak investigation, prepare for restart"

**Result:** Website crashes at 15:30. AI predicted it 2.5 hours earlier.

---

### Example 2: Database Connection Exhaustion

**Metrics Sent:**
```
Time 09:00 - DB Connections: 450/1000, Response Time: 200ms
Time 10:00 - DB Connections: 680/1000, Response Time: 450ms
Time 11:00 - DB Connections: 850/1000, Response Time: 850ms ⚠️
Time 12:00 - DB Connections: 980/1000, Response Time: 1800ms 🔴
```

**AI Detection:**
- **Anomaly Score:** 0.89 (CRITICAL at 12:00)
- **Prediction:** "Database connections approaching limit, requests queuing"
- **RUL Estimate:** "30-60 minutes until connection pool exhaustion"
- **Top Feature:** Database connections (98% of max) contributed most to anomaly
- **Action:** "Increase connection pool size immediately or restart connection pool"

**Result:** Website stops responding at 12:45 when connection pool exhausted. AI predicted 45 minutes earlier.

---

### Example 3: CPU Spiral → Service Overload

**Metrics Sent:**
```
Time 14:00 - CPU: 45%, Response Time: 150ms, Request Rate: 8000/min
Time 15:00 - CPU: 65%, Response Time: 350ms, Request Rate: 12000/min
Time 16:00 - CPU: 82%, Response Time: 1200ms, Request Rate: 15000/min ⚠️
Time 17:00 - CPU: 95%, Response Time: 3500ms, Request Rate: 18000/min 🔴
```

**AI Detection:**
- **Anomaly Score:** 0.91 (CRITICAL at 17:00)
- **Prediction:** "CPU overload with degrading response times - cascade failure imminent"
- **Pattern:** Similar to historical incident where CPU hit 100% and service crashed
- **RUL Estimate:** "10-20 minutes until complete service failure"
- **Action:** "Implement rate limiting, scale horizontally, or restart service"

**Result:** Website becomes unresponsive at 17:15. AI predicted 15 minutes earlier.

---

### Example 4: Disk Space Exhaustion

**Metrics Sent:**
```
Time 08:00 - Disk Usage: 75%, Log Rate: 1000/min
Time 10:00 - Disk Usage: 82%, Log Rate: 2500/min
Time 12:00 - Disk Usage: 91%, Log Rate: 5000/min ⚠️
Time 14:00 - Disk Usage: 98%, Log Rate: 8000/min 🔴
```

**AI Detection:**
- **Anomaly Score:** 0.88 (CRITICAL)
- **Prediction:** "Disk filling rapidly due to log explosion"
- **RUL Estimate:** "30-60 minutes until disk full and service crash"
- **Action:** "Rotate logs immediately, clean up old files, increase disk quota"

**Result:** Website crashes when disk fills at 14:45. AI predicted 45 minutes earlier.

---

## Key Metrics to Monitor for Websites

### Infrastructure Metrics:
- ✅ **CPU Usage** (%) - High CPU indicates overload
- ✅ **Memory Usage** (%) - Memory leaks or insufficient RAM
- ✅ **Disk Usage** (%) - Storage exhaustion
- ✅ **Disk I/O** (IOPS) - Storage bottleneck
- ✅ **Network Bandwidth** (Mbps) - Network saturation
- ✅ **Database Connections** (active/max) - Connection pool exhaustion

### Application Metrics:
- ✅ **Response Time** (ms) - Performance degradation
- ✅ **Error Rate** (%) - Increasing errors indicate problems
- ✅ **Request Rate** (req/min) - Traffic spikes
- ✅ **Queue Depth** (messages) - Backlog buildup
- ✅ **Cache Hit Rate** (%) - Cache failures

### Log Patterns:
- ✅ **Error Logs** - Exception frequency
- ✅ **Slow Query Logs** - Database performance
- ✅ **OutOfMemory Errors** - Memory issues
- ✅ **Connection Timeout Logs** - Resource exhaustion
- ✅ **Deadlock Logs** - Database contention

---

## How Anomaly Detection Actually Works

### 1. Training Phase (Learning Normal)

The system learns what "normal" looks like from historical data:

```
Normal Pattern Matrix:
CPU: 30-50%
Memory: 50-70%
Response Time: 100-300ms
Error Rate: 0.1-0.5%
DB Connections: 300-600/1000

→ Model learns: "This combination is normal"
```

### 2. Detection Phase (Spotting Anomalies)

When new metrics arrive, the model compares them to normal:

```
Current Metrics:
CPU: 85% ← Abnormal
Memory: 92% ← Abnormal  
Response Time: 1250ms ← Abnormal
Error Rate: 5.2% ← Abnormal
DB Connections: 980/1000 ← Abnormal

→ Model calculates: "This combination is very unusual (0.87 anomaly score)"
→ Model explains: "Memory and DB connections are the main culprits"
```

### 3. Prediction (RUL - Remaining Useful Life)

Based on historical patterns of similar anomalies, it estimates:

```
Pattern Similarity: 92% match to Incident #1234 (Memory leak crash)
Time-to-failure in similar cases: 2-4 hours
Current trend: Memory increasing at 2% per hour

→ RUL Estimate: 2-3 hours until crash
→ Confidence: 85%
```

---

## Integration: How to Connect Your Website Monitoring

### Option 1: Use Existing Monitoring Tools

Most monitoring tools can export metrics via API. You can:

**Prometheus Example:**
```python
# Script that runs every minute
import requests
import prometheus_client

# Collect metrics from Prometheus
metrics = prometheus_client.query('cpu_usage{instance="web-server"}')

# Send to PredictrAI
requests.post(
    'https://api.predictrai.com/api/v1/ingest/metrics',
    headers={'X-API-Key': 'your-api-key'},
    json={'data': [
        {'asset_id': 'web-server-01', 'metric_name': 'cpu_usage', 'metric_value': metrics[0].value}
    ]}
)
```

**Datadog/New Relic Example:**
- Use their webhook/API features to forward metrics to PredictrAI
- Or use their export APIs to batch send metrics

### Option 2: Custom Agent/Collector

Deploy a lightweight agent on your servers:

```python
# predictr-agent.py (runs every 60 seconds)
import psutil
import requests
from datetime import datetime

metrics = [
    {'metric_name': 'cpu_usage', 'metric_value': psutil.cpu_percent()},
    {'metric_name': 'memory_usage', 'metric_value': psutil.virtual_memory().percent},
    {'metric_name': 'disk_usage', 'metric_value': psutil.disk_usage('/').percent},
]

requests.post(
    'https://api.predictrai.com/api/v1/ingest/metrics',
    headers={'X-API-Key': 'your-api-key'},
    json={
        'data': [
            {
                'asset_id': 'web-server-01',
                'timestamp': datetime.utcnow().isoformat(),
                **m
            } for m in metrics
        ]
    }
)
```

### Option 3: Log Forwarding

Send application logs for log analysis:

```python
# Forward logs from your application
import requests

# Your app's log file
with open('/var/log/app/error.log') as f:
    logs = f.readlines()

requests.post(
    'https://api.predictrai.com/api/v1/ingest/logs',
    headers={'X-API-Key': 'your-api-key'},
    json={
        'data': [
            {
                'asset_id': 'web-server-01',
                'timestamp': datetime.utcnow().isoformat(),
                'raw_text': log_line
            } for log_line in logs[-100:]  # Last 100 lines
        ]
    }
)
```

---

## What Makes This Better Than Traditional Monitoring?

### Traditional Monitoring (Datadog, New Relic, etc.):
- ❌ **Reactive:** Alerts AFTER something breaks
- ❌ **Static Thresholds:** "Alert if CPU > 90%" (too late)
- ❌ **No Context:** Just tells you what's wrong, not WHY
- ❌ **Alert Fatigue:** Too many false positives

### PredictrAI:
- ✅ **Predictive:** Warns you BEFORE failure (hours/days ahead)
- ✅ **Intelligent:** Learns what's normal for YOUR system
- ✅ **Explainable:** Shows WHY it's concerned (SHAP values)
- ✅ **Contextual:** Correlates metrics + logs + historical incidents
- ✅ **Actionable:** AI suggests specific actions to prevent failure

---

## Real-World Success Scenario

**Company:** E-commerce website with 10,000 daily visitors

**Situation:**
- Website goes down every 2-3 months due to memory leaks
- Each downtime costs $50,000 in lost sales
- Engineers spend hours debugging after the fact

**With PredictrAI:**
1. **Day 1:** System learns normal patterns (CPU 40%, Memory 65%, etc.)
2. **Day 30:** Memory starts creeping up: 68% → 72% → 78%
3. **Day 45:** AI detects anomaly: "Memory usage pattern suggests leak"
   - **Anomaly Score:** 0.76 (WARNING)
   - **RUL:** "Estimated 2-3 weeks until crash"
   - **Suggestion:** "Check for memory leaks in application code"
4. **Engineer investigates:** Finds memory leak in shopping cart code
5. **Engineer fixes:** Deploys patch
6. **Result:** Prevents downtime, saves $50,000 + engineering time

---

## Summary

**PredictrAI detects website downtime by:**

1. ✅ **Collecting metrics** you send (CPU, memory, response time, etc.)
2. ✅ **Learning normal patterns** from your historical data
3. ✅ **Detecting anomalies** that deviate from normal (early warning signs)
4. ✅ **Explaining WHY** it's concerned (which metrics are problematic)
5. ✅ **Predicting WHEN** failure might occur (RUL forecasting)
6. ✅ **Suggesting ACTIONS** to prevent the failure (AI Copilot)
7. ✅ **Correlating with logs** to understand root cause
8. ✅ **Learning from incidents** to improve predictions over time

**Key Difference:** Traditional monitoring tells you "CPU is high NOW". PredictrAI tells you "CPU pattern suggests server crash in 2 hours, caused by memory leak, fix it by restarting the app server."

