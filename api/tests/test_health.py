"""
Testes para endpoints de health check
"""

import pytest
from fastapi.testclient import TestClient


def test_health_endpoint(client):
    """Testa o endpoint /health"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert "timestamp" in data


def test_liveness_probe(client):
    """Testa o endpoint /health/liveness"""
    response = client.get("/health/liveness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data


def test_readiness_probe(client):
    """Testa o endpoint /health/readiness"""
    response = client.get("/health/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["model_loaded"] is True


def test_startup_probe(client):
    """Testa o endpoint /health/startup"""
    response = client.get("/health/startup")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "started"
    assert data["model_loaded"] is True
    assert "model_version" in data


def test_health_metrics(client):
    """Testa o endpoint /health/metrics/health"""
    response = client.get("/health/metrics/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model" in data
    assert data["model"]["loaded"] is True
    assert "auc_roc" in data["model"]
    assert data["model"]["auc_roc"] > 0.7  # Modelo deve ter AUC > 0.7 (realista)
