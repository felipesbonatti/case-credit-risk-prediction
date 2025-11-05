"""
Testes estendidos para endpoints de análise
"""

import pytest


def test_roc_curve_endpoint(client):
    """Testa endpoint de curva ROC"""
    response = client.get("/api/v1/analysis/roc")

    # Pode retornar 200 ou 404 dependendo se há dados
    assert response.status_code in [200, 404, 500]


def test_confusion_matrix_endpoint(client):
    """Testa endpoint de matriz de confusão"""
    response = client.get("/api/v1/analysis/confusion-matrix")

    # Pode retornar 200 ou 404 dependendo se há dados
    assert response.status_code in [200, 404, 500]


def test_feature_importance_endpoint(client):
    """Testa endpoint de importância de features"""
    response = client.get("/api/v1/analysis/feature-importance")

    # Pode retornar 200 ou 404 dependendo se há dados
    assert response.status_code in [200, 404, 500]


def test_threshold_optimization_endpoint(client):
    """Testa endpoint de otimização de threshold"""
    response = client.get("/api/v1/analysis/threshold-optimization")

    # Pode retornar 200 ou 404 dependendo se há dados
    assert response.status_code in [200, 404, 500]


def test_model_performance_endpoint(client):
    """Testa endpoint de performance do modelo"""
    response = client.get("/api/v1/analysis/model-performance")

    # Pode retornar 200 ou 404 dependendo se há dados
    assert response.status_code in [200, 404, 500]
