"""
Testes de integração end-to-end
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.mark.integration
def test_full_prediction_workflow():
    """Testa workflow completo de predição"""
    # 1. Verificar saúde da API
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

    # 2. Fazer predição individual
    payload = {
        "cliente_id": "INTEGRATION_TEST",
        "idade": 35,
        "renda": 8000,
        "score": 750,
        "valor": 20000,
        "prazo": 24,
        "taxa": 10.5,
        "tempo_relacionamento": 36,
        "qtd_produtos_ativos": 3,
        "qtd_atrasos_12m": 0,
        "genero": "Masculino",
        "estado_civil": "Casado",
        "escolaridade": "Superior",
        "regiao": "Sudeste",
        "uf": "SP",
        "porte_municipio": "Metrópole",
        "tipo_produto": "CDC",
    }

    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "probability" in data
    assert "recommendation" in data
    assert 0 <= data["probability"] <= 1


@pytest.mark.integration
def test_batch_prediction_workflow():
    """Testa workflow de predição em lote"""
    payload = {
        "requests": [
            {
                "cliente_id": f"BATCH_TEST_{i}",
                "idade": 30 + i,
                "renda": 5000 + i * 1000,
                "score": 700 + i * 10,
                "valor": 15000,
                "prazo": 24,
                "taxa": 12.0,
                "tempo_relacionamento": 24,
                "qtd_produtos_ativos": 2,
                "qtd_atrasos_12m": 0,
                "genero": "Masculino",
                "estado_civil": "Solteiro",
                "escolaridade": "Superior",
                "regiao": "Sudeste",
                "uf": "SP",
                "porte_municipio": "Grande",
                "tipo_produto": "CDC",
            }
            for i in range(5)
        ]
    }

    response = client.post("/api/v1/predict/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "predictions" in data
    assert len(data["predictions"]) == 5


@pytest.mark.integration
def test_metrics_workflow():
    """Testa workflow de métricas"""
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "taxaAprovacao" in data
    assert "taxaInadimplencia" in data


@pytest.mark.integration
def test_health_checks_workflow():
    """Testa todos os health checks"""
    endpoints = ["/health", "/health/liveness", "/health/readiness", "/health/startup"]

    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 200


@pytest.mark.integration
def test_error_handling_workflow():
    """Testa tratamento de erros"""
    # Payload inválido
    invalid_payload = {"cliente_id": "ERROR_TEST", "idade": -1, "renda": 5000}  # Idade inválida

    response = client.post("/api/v1/predict", json=invalid_payload)
    assert response.status_code == 422  # Validation error


@pytest.mark.integration
def test_documentation_endpoints():
    """Testa endpoints de documentação"""
    # OpenAPI schema
    response = client.get("/openapi.json")
    assert response.status_code == 200

    # Swagger UI
    response = client.get("/docs")
    assert response.status_code == 200

    # ReDoc
    response = client.get("/redoc")
    assert response.status_code == 200


@pytest.mark.integration
def test_different_risk_profiles():
    """Testa predições para diferentes perfis de risco"""
    # Perfil baixo risco
    low_risk = {
        "cliente_id": "LOW_RISK",
        "idade": 45,
        "renda": 15000,
        "score": 900,
        "valor": 10000,
        "prazo": 12,
        "taxa": 8.0,
        "tempo_relacionamento": 120,
        "qtd_produtos_ativos": 5,
        "qtd_atrasos_12m": 0,
        "genero": "Masculino",
        "estado_civil": "Casado",
        "escolaridade": "Pós-graduação",
        "regiao": "Sudeste",
        "uf": "SP",
        "porte_municipio": "Metrópole",
        "tipo_produto": "CDC",
    }

    # Perfil alto risco
    high_risk = {
        "cliente_id": "HIGH_RISK",
        "idade": 22,
        "renda": 1500,
        "score": 350,
        "valor": 50000,
        "prazo": 60,
        "taxa": 25.0,
        "tempo_relacionamento": 3,
        "qtd_produtos_ativos": 1,
        "qtd_atrasos_12m": 5,
        "genero": "Masculino",
        "estado_civil": "Solteiro",
        "escolaridade": "Médio",
        "regiao": "Norte",
        "uf": "AM",
        "porte_municipio": "Pequeno",
        "tipo_produto": "CDC",
    }

    # Testar baixo risco
    response_low = client.post("/api/v1/predict", json=low_risk)
    assert response_low.status_code == 200
    prob_low = response_low.json()["probability"]

    # Testar alto risco
    response_high = client.post("/api/v1/predict", json=high_risk)
    assert response_high.status_code == 200
    prob_high = response_high.json()["probability"]

    # Alto risco deve ter maior probabilidade de inadimplência
    assert prob_high > prob_low
