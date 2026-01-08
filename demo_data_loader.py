"""
Demo Data Loader - Populates PredictrAI with sample data for client demonstrations

Usage:
1. Sign up/login to get API key
2. Update API_KEY below
3. Run: python demo_data_loader.py
"""

import requests
import time
from datetime import datetime, timedelta
import random
import sys

# Configuration
API_BASE = "http://localhost:8000/api/v1"
API_KEY = None  # Will be set from signup

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

def signup_demo_account():
    """Create a demo account and get API key."""
    print_header("Step 1: Creating Demo Account")
    
    email = f"demo_{int(time.time())}@predictr.ai"
    password = "demo123456"
    
    signup_data = {
        "email": email,
        "password": password,
        "company_name": "Demo Company"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/auth/signup",
            json=signup_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Account created: {email}")
            print_info(f"Password: {password}")
            
            # Login to get API key
            login_response = requests.post(
                f"{API_BASE}/auth/login",
                json={"email": email, "password": password}
            )
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                api_key = login_data.get("api_key")
                print_success(f"API Key obtained: {api_key[:20]}...")
                return api_key, email, password
            else:
                print_error("Failed to login after signup")
                return None, None, None
        else:
            print_error(f"Failed to create account: {response.text}")
            return None, None, None
            
    except Exception as e:
        print_error(f"Error creating account: {e}")
        return None, None, None

def create_demo_assets(api_key):
    """Create demo assets."""
    print_header("Step 2: Creating Demo Assets")
    
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    assets = [
        {
            "name": "Web Server 01",
            "type": "server",
            "location": "Data Center A",
            "tags": ["production", "web", "critical"]
        },
        {
            "name": "Web Server 02",
            "type": "server",
            "location": "Data Center A",
            "tags": ["production", "web"]
        },
        {
            "name": "Database Server",
            "type": "server",
            "location": "Data Center B",
            "tags": ["production", "database", "critical"]
        },
        {
            "name": "Production Line Machine A",
            "type": "machine",
            "location": "Factory Floor",
            "tags": ["manufacturing", "production"]
        },
        {
            "name": "Load Balancer",
            "type": "server",
            "location": "Data Center A",
            "tags": ["infrastructure", "critical"]
        },
    ]
    
    asset_ids = []
    for asset in assets:
        try:
            response = requests.post(
                f"{API_BASE}/assets",
                headers=headers,
                json=asset
            )
            
            if response.status_code == 200:
                asset_id = response.json()["id"]
                asset_ids.append(asset_id)
                print_success(f"Created: {asset['name']} ({asset_id[:8]}...)")
            else:
                print_error(f"Failed to create {asset['name']}: {response.text}")
        except Exception as e:
            print_error(f"Error creating {asset['name']}: {e}")
    
    return asset_ids

def send_normal_metrics(api_key, asset_id, hours=48):
    """Send normal metrics for an asset (historical baseline)."""
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    base_time = datetime.utcnow() - timedelta(hours=hours)
    points_sent = 0
    
    # Send metrics every 10 minutes
    for i in range(hours * 6):
        timestamp = base_time + timedelta(minutes=i * 10)
        
        # Normal operating ranges
        metrics = [
            {
                "asset_id": asset_id,
                "timestamp": timestamp.isoformat() + "Z",
                "metric_name": "cpu_usage",
                "metric_value": round(random.uniform(40, 55), 2)  # Normal: 40-55%
            },
            {
                "asset_id": asset_id,
                "timestamp": timestamp.isoformat() + "Z",
                "metric_name": "memory_usage",
                "metric_value": round(random.uniform(60, 75), 2)  # Normal: 60-75%
            },
            {
                "asset_id": asset_id,
                "timestamp": timestamp.isoformat() + "Z",
                "metric_name": "response_time_ms",
                "metric_value": round(random.uniform(100, 300), 2)  # Normal: 100-300ms
            },
            {
                "asset_id": asset_id,
                "timestamp": timestamp.isoformat() + "Z",
                "metric_name": "error_rate",
                "metric_value": round(random.uniform(0.1, 0.5), 2)  # Normal: 0.1-0.5%
            },
            {
                "asset_id": asset_id,
                "timestamp": timestamp.isoformat() + "Z",
                "metric_name": "request_rate",
                "metric_value": round(random.uniform(8000, 12000), 2)  # Normal: 8k-12k/min
            },
            {
                "asset_id": asset_id,
                "timestamp": timestamp.isoformat() + "Z",
                "metric_name": "database_connections",
                "metric_value": round(random.uniform(300, 600), 2)  # Normal: 300-600/1000
            },
        ]
        
        try:
            response = requests.post(
                f"{API_BASE}/ingest/metrics",
                headers=headers,
                json={"data": metrics}
            )
            
            if response.status_code == 200:
                points_sent += len(metrics)
                if points_sent % 50 == 0:
                    print(f"  Sent {points_sent} metric points...")
            else:
                print_error(f"Failed to send metrics: {response.text}")
                
        except Exception as e:
            print_error(f"Error sending metrics: {e}")
        
        time.sleep(0.05)  # Rate limiting
    
    return points_sent

def send_anomaly_metrics(api_key, asset_id, start_hours_ago=2):
    """Send metrics showing an anomaly (memory leak simulation)."""
    print_info(f"Simulating memory leak for asset {asset_id[:8]}...")
    
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
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
        # DB connections increase
        db_connections = 600 + (progress * 380)
        
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
            {
                "asset_id": asset_id,
                "timestamp": timestamp.isoformat() + "Z",
                "metric_name": "database_connections",
                "metric_value": round(db_connections, 2)
            },
        ]
        
        try:
            response = requests.post(
                f"{API_BASE}/ingest/metrics",
                headers=headers,
                json={"data": metrics}
            )
            
            if response.status_code == 200:
                print(f"  {timestamp.strftime('%H:%M')} - Memory: {memory:.1f}%, CPU: {cpu:.1f}%")
            else:
                print_error(f"Failed to send anomaly metrics: {response.text}")
                
        except Exception as e:
            print_error(f"Error sending anomaly metrics: {e}")
        
        time.sleep(0.1)

def send_logs(api_key, asset_id, num_logs=30):
    """Send sample logs."""
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
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
        "INFO Cache cleared successfully",
        "WARNING Response time exceeded 1 second",
        "ERROR Connection pool exhausted",
    ]
    
    base_time = datetime.utcnow() - timedelta(hours=24)
    
    for i in range(num_logs):
        timestamp = base_time + timedelta(minutes=i * 50)
        log_message = random.choice(log_samples)
        
        log_data = {
            "data": [{
                "asset_id": asset_id,
                "timestamp": timestamp.isoformat() + "Z",
                "raw_text": f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} {log_message}"
            }]
        }
        
        try:
            response = requests.post(
                f"{API_BASE}/ingest/logs",
                headers=headers,
                json=log_data
            )
            
            if response.status_code == 200:
                pass  # Silent success
            else:
                print_error(f"Failed to send log: {response.text}")
                
        except Exception as e:
            print_error(f"Error sending log: {e}")
        
        time.sleep(0.05)

def main():
    """Main function to load demo data."""
    print_header("PredictrAI Demo Data Loader")
    print_info("This script will create demo data for client presentations")
    print_info("Make sure the backend is running on http://localhost:8000\n")
    
    # Check if backend is reachable
    try:
        response = requests.get(f"{API_BASE.replace('/api/v1', '')}/health", timeout=5)
        if response.status_code != 200:
            print_error("Backend is not responding. Please start the backend first.")
            sys.exit(1)
    except Exception as e:
        print_error(f"Cannot reach backend: {e}")
        print_error("Please start the backend: uvicorn app.main:app --reload --port 8000")
        sys.exit(1)
    
    # Step 1: Create demo account
    api_key, email, password = signup_demo_account()
    if not api_key:
        print_error("Failed to create demo account. Exiting.")
        sys.exit(1)
    
    # Step 2: Create assets
    asset_ids = create_demo_assets(api_key)
    if not asset_ids:
        print_error("Failed to create assets. Exiting.")
        sys.exit(1)
    
    # Step 3: Send normal metrics (historical baseline)
    print_header("Step 3: Loading Historical Metrics (Normal Operations)")
    print_info("This may take a few minutes...")
    
    for asset_id in asset_ids[:3]:  # First 3 assets
        print(f"\nLoading metrics for asset {asset_id[:8]}...")
        points = send_normal_metrics(api_key, asset_id, hours=48)
        print_success(f"Sent {points} metric points for baseline")
    
    # Step 4: Send anomaly metrics (for demo)
    print_header("Step 4: Simulating Anomaly (Memory Leak)")
    print_info("Injecting anomaly data to demonstrate detection...")
    
    if asset_ids:
        send_anomaly_metrics(api_key, asset_ids[0])  # First asset has anomaly
        print_success("Anomaly metrics sent - memory leak simulation complete")
    
    # Step 5: Send logs
    print_header("Step 5: Loading Sample Logs")
    for asset_id in asset_ids[:3]:
        send_logs(api_key, asset_id, num_logs=30)
    print_success("Sample logs loaded")
    
    # Summary
    print_header("✅ Demo Data Loaded Successfully!")
    print(f"\n{Colors.BOLD}Demo Account:{Colors.ENDC}")
    print(f"  Email: {Colors.OKGREEN}{email}{Colors.ENDC}")
    print(f"  Password: {Colors.OKGREEN}{password}{Colors.ENDC}")
    print(f"  API Key: {Colors.OKGREEN}{api_key[:30]}...{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}Demo Assets Created:{Colors.ENDC} {len(asset_ids)}")
    if asset_ids:
        print(f"  Main Demo Asset: {Colors.OKCYAN}{asset_ids[0]}{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}Next Steps:{Colors.ENDC}")
    print(f"  1. Login at: {Colors.OKBLUE}http://localhost:3000/login{Colors.ENDC}")
    print(f"  2. Use email: {Colors.OKGREEN}{email}{Colors.ENDC}")
    print(f"  3. View dashboard: {Colors.OKBLUE}http://localhost:3000/dashboard{Colors.ENDC}")
    if asset_ids:
        print(f"  4. View demo asset: {Colors.OKBLUE}http://localhost:3000/dashboard/assets/{asset_ids[0]}{Colors.ENDC}")
    
    print(f"\n{Colors.WARNING}Note: Wait a few minutes for models to train on the data.{Colors.ENDC}")
    print(f"{Colors.WARNING}After training, anomaly detection will work automatically.{Colors.ENDC}\n")

if __name__ == "__main__":
    main()

