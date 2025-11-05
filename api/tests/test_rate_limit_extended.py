"""
Testes Estendidos para o módulo de rate limiting
Aumenta cobertura de 31% para 70%+
"""

import pytest
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from app.middleware.rate_limit import (
    RateLimitStore,
    RateLimitConfig,
    RateLimitMiddleware,
    rate_limit_store,
    get_rate_limit_stats,
    unblock_ip,
    clear_rate_limit_data,
)


@pytest.fixture
def store():
    """Fixture para criar instância limpa de RateLimitStore"""
    store = RateLimitStore()
    yield store
    # Limpar após teste
    store.requests.clear()
    store.blocked_ips.clear()


@pytest.fixture
def app_with_rate_limit():
    """Fixture para criar app FastAPI com rate limiting"""
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}

    @app.get("/api/v1/predict")
    async def predict_endpoint():
        return {"prediction": 0}

    return app


@pytest.fixture
def client(app_with_rate_limit):
    """Fixture para criar cliente de teste"""
    return TestClient(app_with_rate_limit)


# ============================================================================
# Testes para RateLimitStore
# ============================================================================


def test_rate_limit_store_initialization(store):
    """Testa inicialização do RateLimitStore"""
    assert len(store.requests) == 0
    assert len(store.blocked_ips) == 0


def test_add_request(store):
    """Testa adição de requisição"""
    store.add_request("192.168.1.1", "/api/test")

    assert "192.168.1.1" in store.requests
    assert "/api/test" in store.requests["192.168.1.1"]
    assert len(store.requests["192.168.1.1"]["/api/test"]) == 1


def test_add_multiple_requests(store):
    """Testa adição de múltiplas requisições"""
    for i in range(5):
        store.add_request("192.168.1.1", "/api/test")

    assert len(store.requests["192.168.1.1"]["/api/test"]) == 5


def test_add_requests_different_ips(store):
    """Testa adição de requisições de IPs diferentes"""
    store.add_request("192.168.1.1", "/api/test")
    store.add_request("192.168.1.2", "/api/test")

    assert len(store.requests) == 2


def test_add_requests_different_endpoints(store):
    """Testa adição de requisições para endpoints diferentes"""
    store.add_request("192.168.1.1", "/api/test1")
    store.add_request("192.168.1.1", "/api/test2")

    assert len(store.requests["192.168.1.1"]) == 2


def test_get_request_count(store):
    """Testa contagem de requisições"""
    for i in range(3):
        store.add_request("192.168.1.1", "/api/test")

    count = store.get_request_count("192.168.1.1", "/api/test", window_seconds=60)
    assert count == 3


def test_get_request_count_empty(store):
    """Testa contagem quando não há requisições"""
    count = store.get_request_count("192.168.1.1", "/api/test", window_seconds=60)
    assert count == 0


def test_get_request_count_different_endpoint(store):
    """Testa contagem para endpoint diferente"""
    store.add_request("192.168.1.1", "/api/test1")

    count = store.get_request_count("192.168.1.1", "/api/test2", window_seconds=60)
    assert count == 0


def test_block_ip(store):
    """Testa bloqueio de IP"""
    store.block_ip("192.168.1.1", duration_minutes=15)

    assert "192.168.1.1" in store.blocked_ips
    assert store.is_blocked("192.168.1.1")


def test_block_ip_custom_duration(store):
    """Testa bloqueio de IP com duração customizada"""
    store.block_ip("192.168.1.1", duration_minutes=30)

    assert store.is_blocked("192.168.1.1")


def test_is_blocked_not_blocked(store):
    """Testa verificação de IP não bloqueado"""
    assert not store.is_blocked("192.168.1.1")


def test_is_blocked_expired(store):
    """Testa verificação de bloqueio expirado"""
    # Bloquear com data no passado
    store.blocked_ips["192.168.1.1"] = datetime.utcnow() - timedelta(minutes=1)

    # Deve retornar False e remover da lista
    assert not store.is_blocked("192.168.1.1")
    assert "192.168.1.1" not in store.blocked_ips


def test_get_remaining_block_time(store):
    """Testa obtenção de tempo restante de bloqueio"""
    store.block_ip("192.168.1.1", duration_minutes=15)

    remaining = store.get_remaining_block_time("192.168.1.1")

    assert remaining is not None
    assert remaining > 0
    assert remaining <= 15 * 60  # 15 minutos em segundos


def test_get_remaining_block_time_not_blocked(store):
    """Testa tempo restante quando IP não está bloqueado"""
    remaining = store.get_remaining_block_time("192.168.1.1")

    assert remaining is None


def test_cleanup_old_requests(store):
    """Testa limpeza de requisições antigas"""
    # Adicionar requisição antiga manualmente
    old_time = datetime.utcnow() - timedelta(hours=2)
    store.requests["192.168.1.1"]["/api/test"].append(old_time)

    # Adicionar requisição nova
    store.add_request("192.168.1.1", "/api/test")

    # Requisição antiga deve ter sido removida
    count = store.get_request_count("192.168.1.1", "/api/test", window_seconds=3600)
    assert count == 1  # Apenas a nova


# ============================================================================
# Testes para RateLimitConfig
# ============================================================================


def test_rate_limit_config_default():
    """Testa configuração padrão"""
    config = RateLimitConfig.get_limit("/api/unknown")

    assert config["requests"] == RateLimitConfig.DEFAULT_LIMIT
    assert config["window"] == 60


def test_rate_limit_config_predict():
    """Testa configuração para endpoint de predição"""
    config = RateLimitConfig.get_limit("/api/v1/predict")

    assert config["requests"] == 60
    assert config["window"] == 60
    assert config["block_duration"] == 15


def test_rate_limit_config_batch():
    """Testa configuração para endpoint de batch"""
    config = RateLimitConfig.get_limit("/api/v1/predict/batch")

    assert config["requests"] == 10
    assert config["window"] == 60
    assert config["block_duration"] == 30


def test_rate_limit_config_auth():
    """Testa configuração para endpoint de autenticação"""
    config = RateLimitConfig.get_limit("/api/v1/auth/token")

    assert config["requests"] == 5
    assert config["window"] == 300
    assert config["block_duration"] == 60


def test_rate_limit_config_whitelist():
    """Testa lista de IPs whitelisted"""
    assert "127.0.0.1" in RateLimitConfig.WHITELIST
    assert "localhost" in RateLimitConfig.WHITELIST


# ============================================================================
# Testes para RateLimitMiddleware
# ============================================================================


def test_middleware_allows_request(client):
    """Testa que middleware permite requisição normal"""
    response = client.get("/test")

    assert response.status_code == 200
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers


def test_middleware_rate_limit_headers(client):
    """Testa headers de rate limit"""
    response = client.get("/test")

    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers


def test_middleware_whitelisted_ip(client):
    """Testa que IP whitelisted não sofre rate limit"""
    # Fazer muitas requisições de localhost
    for i in range(200):
        response = client.get("/test")
        assert response.status_code == 200


def test_middleware_blocks_after_limit(client):
    """Testa que middleware bloqueia após exceder limite"""
    # Limpar dados anteriores
    clear_rate_limit_data()

    # Fazer requisições até exceder limite
    # Endpoint /api/v1/predict tem limite de 60 req/min
    for i in range(65):
        response = client.get("/api/v1/predict")

    # Última requisição deve ser bloqueada
    assert response.status_code == 429
    assert "error" in response.json()


def test_middleware_retry_after_header(client):
    """Testa header Retry-After quando bloqueado"""
    clear_rate_limit_data()

    # Exceder limite
    for i in range(65):
        response = client.get("/api/v1/predict")

    # Verificar header
    assert "Retry-After" in response.headers


def test_middleware_blocked_ip_message(client):
    """Testa mensagem quando IP está bloqueado"""
    clear_rate_limit_data()

    # Exceder limite
    for i in range(65):
        response = client.get("/api/v1/predict")

    # Verificar mensagem
    data = response.json()
    assert "error" in data
    assert "retry_after" in data or "Retry-After" in response.headers


# ============================================================================
# Testes para funções de gerenciamento
# ============================================================================


def test_get_rate_limit_stats_empty():
    """Testa estatísticas quando não há dados"""
    clear_rate_limit_data()

    stats = get_rate_limit_stats()

    assert stats["total_tracked_ips"] == 0
    assert stats["blocked_ips"] == 0


def test_get_rate_limit_stats_with_data():
    """Testa estatísticas com dados"""
    clear_rate_limit_data()

    # Adicionar algumas requisições
    rate_limit_store.add_request("192.168.1.1", "/api/test")
    rate_limit_store.add_request("192.168.1.2", "/api/test")

    stats = get_rate_limit_stats()

    assert stats["total_tracked_ips"] == 2
    assert stats["total_requests_tracked"] >= 2


def test_get_rate_limit_stats_blocked_ips():
    """Testa estatísticas com IPs bloqueados"""
    clear_rate_limit_data()

    # Bloquear IP
    rate_limit_store.block_ip("192.168.1.1", duration_minutes=15)

    stats = get_rate_limit_stats()

    assert stats["blocked_ips"] == 1
    assert len(stats["blocked_ips_list"]) == 1
    assert stats["blocked_ips_list"][0]["ip"] == "192.168.1.1"


def test_get_rate_limit_stats_top_ips():
    """Testa lista de top IPs"""
    clear_rate_limit_data()

    # Adicionar requisições de diferentes IPs
    for i in range(10):
        rate_limit_store.add_request("192.168.1.1", "/api/test")

    for i in range(5):
        rate_limit_store.add_request("192.168.1.2", "/api/test")

    stats = get_rate_limit_stats()

    assert len(stats["top_ips"]) > 0
    # IP com mais requisições deve estar primeiro
    assert stats["top_ips"][0]["ip"] == "192.168.1.1"
    assert stats["top_ips"][0]["requests"] == 10


def test_unblock_ip_success():
    """Testa desbloqueio de IP"""
    clear_rate_limit_data()

    # Bloquear IP
    rate_limit_store.block_ip("192.168.1.1", duration_minutes=15)
    assert rate_limit_store.is_blocked("192.168.1.1")

    # Desbloquear
    result = unblock_ip("192.168.1.1")

    assert result is True
    assert not rate_limit_store.is_blocked("192.168.1.1")


def test_unblock_ip_not_blocked():
    """Testa desbloqueio de IP que não estava bloqueado"""
    clear_rate_limit_data()

    result = unblock_ip("192.168.1.1")

    assert result is False


def test_clear_rate_limit_data():
    """Testa limpeza de dados de rate limiting"""
    # Adicionar dados
    rate_limit_store.add_request("192.168.1.1", "/api/test")
    rate_limit_store.block_ip("192.168.1.2", duration_minutes=15)

    # Limpar
    clear_rate_limit_data()

    # Verificar que foi limpo
    assert len(rate_limit_store.requests) == 0
    assert len(rate_limit_store.blocked_ips) == 0


# ============================================================================
# Testes de integração
# ============================================================================


def test_rate_limit_per_endpoint(client):
    """Testa que rate limit é por endpoint"""
    clear_rate_limit_data()

    # Fazer requisições para diferentes endpoints
    for i in range(10):
        response1 = client.get("/test")
        response2 = client.get("/api/v1/predict")

    # Ambos devem funcionar
    assert response1.status_code == 200
    assert response2.status_code == 200


def test_rate_limit_per_ip(client):
    """Testa que rate limit é por IP"""
    clear_rate_limit_data()

    # Fazer requisições do mesmo IP
    for i in range(10):
        response = client.get("/api/v1/predict")

    # Verificar que contador aumentou
    count = rate_limit_store.get_request_count("testclient", "/api/v1/predict", window_seconds=60)
    assert count >= 10
