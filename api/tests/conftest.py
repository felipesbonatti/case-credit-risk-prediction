"""
Configuração dos testes pytest
"""

import pytest
import sys
import os
from pathlib import Path

# Desabilitar rate limiting durante os testes
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["DEBUG"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-do-not-use-in-production"

# Adicionar o diretório raiz ao path para imports
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    """
    Fixture que fornece um cliente de teste para a API
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_predict_request():
    """
    Fixture com dados de exemplo para predição
    """
    return {
        "cliente_id": "TEST001",
        "idade": 35,
        "renda_mensal": 8000,
        "score_credito": 750,
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


@pytest.fixture
def sample_batch_request(sample_predict_request):
    """
    Fixture com dados de exemplo para predição em lote
    """
    return {
        "requests": [
            sample_predict_request,
            {**sample_predict_request, "cliente_id": "TEST002", "idade": 45, "renda_mensal": 12000},
        ]
    }


@pytest.fixture
def auth_token(client):
    """
    Fixture que fornece um token de autenticação válido
    """
    response = client.post("/api/v1/auth/token", data={"username": "admin", "password": "Santander@2025"})
    if response.status_code == 200:
        return response.json()["access_token"]
    return None
