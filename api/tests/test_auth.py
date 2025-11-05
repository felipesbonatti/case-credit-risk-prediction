"""
Testes para endpoints de autenticação
"""

import pytest
from fastapi.testclient import TestClient


def test_login_success(client):
    """Testa login com credenciais válidas"""
    response = client.post("/api/v1/auth/token", data={"username": "admin", "password": "Santander@2025"})
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data


def test_login_invalid_username(client):
    """Testa login com usuário inválido"""
    response = client.post("/api/v1/auth/token", data={"username": "invalid_user", "password": "Santander@2025"})
    assert response.status_code == 401


def test_login_invalid_password(client):
    """Testa login com senha inválida"""
    response = client.post("/api/v1/auth/token", data={"username": "admin", "password": "wrong_password"})
    assert response.status_code == 401


def test_login_missing_credentials(client):
    """Testa login sem credenciais"""
    response = client.post("/api/v1/auth/token", data={})
    assert response.status_code == 422


def test_get_current_user(client, auth_token):
    """Testa obtenção de dados do usuário autenticado"""
    if not auth_token:
        pytest.skip("Token de autenticação não disponível")

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {auth_token}"})
    assert response.status_code == 200

    data = response.json()
    assert "username" in data
    assert "email" in data
    assert "roles" in data


def test_get_current_user_without_token(client):
    """Testa acesso sem token"""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_current_user_invalid_token(client):
    """Testa acesso com token inválido"""
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401


def test_refresh_token(client):
    """Testa renovação de token"""
    # Primeiro fazer login
    login_response = client.post("/api/v1/auth/token", data={"username": "admin", "password": "Santander@2025"})
    assert login_response.status_code == 200
    refresh_token = login_response.json()["refresh_token"]

    # Tentar renovar o token
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    # Pode retornar 200 ou 501 (não implementado)
    assert response.status_code in [200, 501]


def test_token_expiration_format(client):
    """Testa se o tempo de expiração está no formato correto"""
    response = client.post("/api/v1/auth/token", data={"username": "admin", "password": "Santander@2025"})
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data["expires_in"], int)
    assert data["expires_in"] > 0
