"""
Testes para documentação da API
"""

import pytest
from fastapi.testclient import TestClient


def test_openapi_schema(client):
    """Testa se o schema OpenAPI está disponível"""
    response = client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema

    # Verificar informações básicas
    assert schema["info"]["title"] == "Santander Credit Risk API"
    assert "version" in schema["info"]


def test_swagger_ui(client):
    """Testa se a interface Swagger UI está disponível"""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()


def test_redoc(client):
    """Testa se o ReDoc está disponível"""
    response = client.get("/redoc")
    assert response.status_code == 200


def test_openapi_endpoints_documented(client):
    """Testa se os principais endpoints estão documentados"""
    response = client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    paths = schema["paths"]

    # Verificar se os endpoints principais estão documentados
    expected_endpoints = [
        "/health",
        "/api/v1/predict",
        "/api/v1/predict/batch",
        "/api/v1/metrics",
        "/api/v1/auth/token",
    ]

    for endpoint in expected_endpoints:
        assert endpoint in paths, f"Endpoint {endpoint} não está documentado"


def test_openapi_schemas_defined(client):
    """Testa se os schemas estão definidos"""
    response = client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert "components" in schema
    assert "schemas" in schema["components"]

    # Verificar se os schemas principais existem
    schemas = schema["components"]["schemas"]
    assert len(schemas) > 0


def test_endpoint_descriptions(client):
    """Testa se os endpoints têm descrições"""
    response = client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    paths = schema["paths"]

    # Verificar se pelo menos alguns endpoints têm descrição
    endpoints_with_description = 0
    for path, methods in paths.items():
        for method, details in methods.items():
            if "description" in details or "summary" in details:
                endpoints_with_description += 1

    assert endpoints_with_description > 0
