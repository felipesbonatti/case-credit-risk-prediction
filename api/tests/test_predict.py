"""
Testes para endpoints de predição
"""

import pytest
from fastapi.testclient import TestClient


def test_predict_individual_success(client, sample_predict_request):
    """Testa predição individual com sucesso"""
    response = client.post("/api/v1/predict", json=sample_predict_request)
    assert response.status_code == 200

    data = response.json()
    assert "cliente_id" in data
    assert data["cliente_id"] == sample_predict_request["cliente_id"]
    assert "prediction" in data
    assert "probability" in data
    assert "risk_score" in data
    assert "recommendation" in data
    assert "confidence" in data
    assert "model_version" in data
    assert "timestamp" in data

    # Validar tipos
    assert isinstance(data["prediction"], int)
    assert data["prediction"] in [0, 1]
    assert isinstance(data["probability"], (int, float))
    assert 0 <= data["probability"] <= 1
    assert isinstance(data["confidence"], (int, float))
    assert 0 <= data["confidence"] <= 1


def test_predict_individual_invalid_idade(client, sample_predict_request):
    """Testa predição com idade inválida"""
    invalid_request = {**sample_predict_request, "idade": 150}
    response = client.post("/api/v1/predict", json=invalid_request)
    assert response.status_code == 422  # Validation error


def test_predict_individual_invalid_score(client, sample_predict_request):
    """Testa predição com score inválido"""
    invalid_request = {**sample_predict_request, "score_credito": 1000}
    response = client.post("/api/v1/predict", json=invalid_request)
    assert response.status_code == 422


def test_predict_individual_missing_field(client, sample_predict_request):
    """Testa predição com campo obrigatório faltando"""
    incomplete_request = {**sample_predict_request}
    del incomplete_request["idade"]
    response = client.post("/api/v1/predict", json=incomplete_request)
    assert response.status_code == 422


def test_predict_batch_success(client, sample_batch_request):
    """Testa predição em lote com sucesso"""
    response = client.post("/api/v1/predict/batch", json=sample_batch_request)
    assert response.status_code == 200

    data = response.json()
    assert "predictions" in data
    assert len(data["predictions"]) == len(sample_batch_request["requests"])

    # Validar cada predição
    for prediction in data["predictions"]:
        assert "cliente_id" in prediction
        assert "prediction" in prediction
        assert "probability" in prediction
        assert "recommendation" in prediction


def test_predict_batch_empty_list(client):
    """Testa predição em lote com lista vazia"""
    response = client.post("/api/v1/predict/batch", json={"requests": []})
    assert response.status_code == 422


def test_predict_batch_too_many_requests(client, sample_predict_request):
    """Testa predição em lote com mais de 1000 requisições"""
    large_batch = {"requests": [sample_predict_request] * 1001}
    response = client.post("/api/v1/predict/batch", json=large_batch)
    assert response.status_code == 422


def test_predict_response_time(client, sample_predict_request):
    """Testa se o tempo de resposta é aceitável (<100ms)"""
    import time

    start = time.time()
    response = client.post("/api/v1/predict", json=sample_predict_request)
    elapsed = time.time() - start

    assert response.status_code == 200
    assert elapsed < 0.1  # Menos de 100ms


def test_predict_explainability(client, sample_predict_request):
    """Testa se a resposta inclui explicabilidade"""
    response = client.post("/api/v1/predict", json=sample_predict_request)
    assert response.status_code == 200

    data = response.json()
    assert "explainability" in data
    assert isinstance(data["explainability"], dict)
    assert len(data["explainability"]) > 0  # Deve ter pelo menos uma feature


def test_predict_different_profiles(client):
    """Testa predição com diferentes perfis de cliente"""
    # Cliente de baixo risco
    low_risk = {
        "cliente_id": "LOW_RISK",
        "idade": 40,
        "renda_mensal": 15000,
        "score_credito": 850,
        "valor": 10000,
        "prazo": 12,
        "taxa": 8.0,
        "tempo_relacionamento": 60,
        "qtd_produtos_ativos": 5,
        "qtd_atrasos_12m": 0,
        "genero": "Masculino",
        "estado_civil": "Casado",
        "escolaridade": "Pós-Graduação",
        "regiao": "Sudeste",
        "uf": "SP",
        "porte_municipio": "Metrópole",
        "tipo_produto": "CDC",
    }

    response = client.post("/api/v1/predict", json=low_risk)
    assert response.status_code == 200
    data = response.json()
    assert data["recommendation"] in ["Aprovar", "Rejeitar"]
