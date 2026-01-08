"""
Pytest fixtures and configuration.
"""
import pytest
import asyncio
from datetime import datetime
from typing import Generator, AsyncGenerator
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4

import pandas as pd
import numpy as np

# For async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============ Mock Database Fixtures ============

@pytest.fixture
def mock_db_session():
    """Mock database session for unit tests."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def sample_tenant_id():
    """Sample tenant ID for tests."""
    return uuid4()


@pytest.fixture
def sample_asset_id():
    """Sample asset ID for tests."""
    return uuid4()


@pytest.fixture
def sample_user_id():
    """Sample user ID for tests."""
    return uuid4()


# ============ Mock User Fixture ============

@pytest.fixture
def mock_user(sample_tenant_id, sample_user_id):
    """Mock authenticated user."""
    user = MagicMock()
    user.id = sample_user_id
    user.tenant_id = sample_tenant_id
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.role = "admin"
    user.is_active = True
    return user


# ============ Sample Data Fixtures ============

@pytest.fixture
def sample_metrics_df():
    """Sample metrics DataFrame for ML testing."""
    np.random.seed(42)
    n_samples = 500
    
    return pd.DataFrame({
        "temperature": np.random.normal(65, 10, n_samples),
        "vibration": np.random.normal(0.5, 0.1, n_samples),
        "pressure": np.random.normal(100, 15, n_samples),
        "rpm": np.random.normal(1500, 100, n_samples),
        "current": np.random.normal(10, 2, n_samples),
    })


@pytest.fixture
def sample_metrics_with_anomalies():
    """Metrics with injected anomalies."""
    np.random.seed(42)
    n_samples = 500
    
    df = pd.DataFrame({
        "temperature": np.random.normal(65, 10, n_samples),
        "vibration": np.random.normal(0.5, 0.1, n_samples),
        "pressure": np.random.normal(100, 15, n_samples),
    })
    
    # Inject anomalies in last 50 rows
    df.loc[450:, "temperature"] = np.random.normal(95, 5, 50)
    df.loc[450:, "vibration"] = np.random.normal(1.5, 0.2, 50)
    
    return df


@pytest.fixture
def sample_rul_df():
    """Sample RUL training DataFrame."""
    np.random.seed(42)
    n_samples = 1000
    
    df = pd.DataFrame({
        "temperature": np.random.normal(65, 10, n_samples),
        "vibration": np.random.normal(0.5, 0.1, n_samples),
        "pressure": np.random.normal(100, 15, n_samples),
        "rpm": np.random.normal(1500, 100, n_samples),
    })
    
    # RUL decreases over time
    df["RUL"] = np.linspace(130, 0, n_samples)
    
    return df


@pytest.fixture
def sample_logs():
    """Sample log messages for testing."""
    return [
        "2026-01-08 10:00:00 INFO System started successfully",
        "2026-01-08 10:05:00 WARNING Temperature threshold exceeded: 85C",
        "2026-01-08 10:10:00 ERROR Connection failed to sensor 192.168.1.50",
        "2026-01-08 10:15:00 INFO Sensor reconnected",
        "2026-01-08 10:20:00 WARNING High vibration detected on motor A",
        "2026-01-08 10:25:00 ERROR Failed to read pressure sensor",
        "2026-01-08 10:30:00 INFO Maintenance scheduled for asset_1",
        "2026-01-08 10:35:00 ERROR Connection timeout to 192.168.1.51",
        "2026-01-08 10:40:00 WARNING Temperature rising: 78C",
        "2026-01-08 10:45:00 ERROR Sensor 192.168.1.50 offline",
    ] * 10  # 100 logs


# ============ Agent Test Fixtures ============

@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider for agent tests."""
    provider = AsyncMock()
    provider.generate_incident = AsyncMock(return_value={
        "title": "Test Incident",
        "description": "Test description",
        "root_cause": "Test root cause",
        "actions": ["Action 1", "Action 2"],
    })
    provider.generate_recommendation = AsyncMock(return_value="Test recommendation")
    provider.chat = AsyncMock(return_value="Test response")
    return provider


@pytest.fixture
def mock_ticket_provider():
    """Mock ticket provider for agent tests."""
    provider = AsyncMock()
    provider.create_ticket = AsyncMock(return_value={
        "status": "success",
        "ticket_id": "MOCK-123",
        "url": "https://mock.tickets/MOCK-123",
    })
    return provider


@pytest.fixture
def mock_notification_provider():
    """Mock notification provider for agent tests."""
    provider = AsyncMock()
    provider.send = AsyncMock(return_value={
        "status": "sent",
        "mock": True,
    })
    return provider


# ============ API Test Fixtures ============

@pytest.fixture
def sample_alert():
    """Sample alert data."""
    return {
        "id": str(uuid4()),
        "asset_id": str(uuid4()),
        "alert_type": "anomaly",
        "severity": "warning",
        "message": "Elevated vibration detected",
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_prediction():
    """Sample prediction data."""
    return {
        "id": str(uuid4()),
        "asset_id": str(uuid4()),
        "prediction_type": "anomaly",
        "value": 0.75,
        "confidence": 0.9,
        "model_version": "1.0.0",
        "explanation": {
            "top_features": [
                {"feature": "vibration", "contribution": 0.45},
                {"feature": "temperature", "contribution": 0.30},
            ]
        },
    }
