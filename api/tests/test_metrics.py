"""
Testes para endpoints de métricas e análise
"""

import pytest
from fastapi.testclient import TestClient


def test_metrics_endpoint(client):
    """Testa o endpoint /api/v1/metrics"""
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200

    data = response.json()
    # Verificar campos obrigatórios
    assert "saldoLiquido" in data
    assert "taxaAprovacao" in data
    assert "taxaInadimplencia" in data
    assert "totalClientes" in data
    assert "threshold" in data

    # Verificar tipos
    assert isinstance(data["saldoLiquido"], (int, float))
    assert isinstance(data["taxaAprovacao"], (int, float))
    assert isinstance(data["taxaInadimplencia"], (int, float))
    assert isinstance(data["totalClientes"], int)


def test_roc_curve_endpoint(client):
    """Testa o endpoint /api/v1/analysis/roc-curve"""
    response = client.get("/api/v1/analysis/roc-curve")
    assert response.status_code == 200

    data = response.json()
    assert "fpr" in data
    assert "tpr" in data
    assert "thresholds" in data
    assert "auc" in data

    # Verificar tipos
    assert isinstance(data["fpr"], list)
    assert isinstance(data["tpr"], list)
    assert isinstance(data["thresholds"], list)
    assert isinstance(data["auc"], (int, float))


def test_confusion_matrix_endpoint(client):
    """Testa o endpoint /api/v1/analysis/confusion-matrix"""
    response = client.get("/api/v1/analysis/confusion-matrix")
    assert response.status_code == 200

    data = response.json()
    assert "tp" in data
    assert "fp" in data
    assert "tn" in data
    assert "fn" in data

    # Verificar tipos
    assert isinstance(data["tp"], int)
    assert isinstance(data["fp"], int)
    assert isinstance(data["tn"], int)
    assert isinstance(data["fn"], int)


def test_threshold_sensitivity_endpoint(client):
    """Testa o endpoint /api/v1/analysis/threshold-sensitivity"""
    response = client.get("/api/v1/analysis/threshold-sensitivity")
    assert response.status_code == 200

    data = response.json()
    # O endpoint retorna um dicionário com análise de sensibilidade
    assert isinstance(data, dict)
    # Verificar se tem dados (pode estar vazio se não houver histórico)
    if data:
        # Se houver dados, verificar estrutura
        assert len(data) > 0


def test_optimize_threshold_endpoint(client):
    """Testa o endpoint /api/v1/analysis/optimize-threshold"""
    response = client.get("/api/v1/analysis/optimize-threshold")
    assert response.status_code == 200

    data = response.json()
    assert "optimal_threshold" in data
    assert "objective" in data

    assert isinstance(data["optimal_threshold"], (int, float))
    assert 0 <= data["optimal_threshold"] <= 1


def test_metrics_with_custom_threshold(client):
    """Testa métricas com threshold customizado"""
    response = client.get("/api/v1/metrics?threshold=0.6")
    assert response.status_code == 200

    data = response.json()
    assert data["threshold"] == 0.6


def test_analysis_endpoints_response_time(client):
    """Testa se os endpoints de análise respondem em tempo aceitável"""
    import time

    endpoints = [
        "/api/v1/analysis/roc-curve",
        "/api/v1/analysis/confusion-matrix",
        "/api/v1/analysis/threshold-sensitivity",
        "/api/v1/analysis/optimize-threshold",
    ]

    for endpoint in endpoints:
        start = time.time()
        response = client.get(endpoint)
        elapsed = time.time() - start

        assert response.status_code == 200
        # Aceitar até 60 segundos para análises (podem ser muito lentas com 1M de registros)
        assert elapsed < 60.0, f"Endpoint {endpoint} demorou {elapsed:.2f}s"
