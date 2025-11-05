"""
Middleware de Rate Limiting
Proteção contra abuso e DDoS
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import structlog

from app.security.audit import audit_logger

logger = structlog.get_logger()


class RateLimitStore:
    """
    Armazena contadores de rate limit em memória

    TODO: Migrar para Redis em produção para suportar múltiplas instâncias
    """

    def __init__(self):
        # {ip_address: {endpoint: [(timestamp, count)]}}
        self.requests: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))
        self.blocked_ips: Dict[str, datetime] = {}

    def add_request(self, ip: str, endpoint: str):
        """Registra uma requisição"""
        now = datetime.utcnow()
        self.requests[ip][endpoint].append(now)

        # Limpar requisições antigas (> 1 hora)
        cutoff = now - timedelta(hours=1)
        self.requests[ip][endpoint] = [ts for ts in self.requests[ip][endpoint] if ts > cutoff]

    def get_request_count(self, ip: str, endpoint: str, window_seconds: int) -> int:
        """Retorna número de requisições na janela de tempo"""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=window_seconds)

        return len([ts for ts in self.requests[ip][endpoint] if ts > cutoff])

    def block_ip(self, ip: str, duration_minutes: int = 15):
        """Bloqueia IP temporariamente"""
        self.blocked_ips[ip] = datetime.utcnow() + timedelta(minutes=duration_minutes)
        logger.warning(f"IP blocked for {duration_minutes} minutes", ip=ip)

    def is_blocked(self, ip: str) -> bool:
        """Verifica se IP está bloqueado"""
        if ip not in self.blocked_ips:
            return False

        if datetime.utcnow() > self.blocked_ips[ip]:
            # Bloqueio expirou
            del self.blocked_ips[ip]
            return False

        return True

    def get_remaining_block_time(self, ip: str) -> Optional[int]:
        """Retorna tempo restante de bloqueio em segundos"""
        if ip not in self.blocked_ips:
            return None

        remaining = (self.blocked_ips[ip] - datetime.utcnow()).total_seconds()
        return max(0, int(remaining))


# Instância global
rate_limit_store = RateLimitStore()


class RateLimitConfig:
    """
    Configuração de rate limits por endpoint
    """

    # Limites padrão (requisições por minuto)
    DEFAULT_LIMIT = 100

    # Limites específicos por endpoint
    ENDPOINT_LIMITS = {
        "/api/v1/predict": {
            "requests": 60,  # 60 requisições
            "window": 60,  # por minuto
            "block_duration": 15,  # bloqueia por 15 min se exceder
        },
        "/api/v1/predict/batch": {
            "requests": 10,  # 10 requisições
            "window": 60,  # por minuto
            "block_duration": 30,  # bloqueia por 30 min se exceder
        },
        "/api/v1/auth/token": {
            "requests": 5,  # 5 tentativas
            "window": 300,  # por 5 minutos
            "block_duration": 60,  # bloqueia por 1 hora se exceder
        },
        "/api/v1/auth/login": {"requests": 5, "window": 300, "block_duration": 60},
    }

    # IPs whitelisted (não sofrem rate limit)
    WHITELIST = [
        "127.0.0.1",
        "localhost",
        # Adicionar IPs de servidores internos
    ]

    @classmethod
    def get_limit(cls, endpoint: str) -> dict:
        """Retorna configuração de limite para endpoint"""
        # Buscar configuração específica
        for pattern, config in cls.ENDPOINT_LIMITS.items():
            if pattern in endpoint:
                return config

        # Retornar limite padrão
        return {"requests": cls.DEFAULT_LIMIT, "window": 60, "block_duration": 15}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware de Rate Limiting

    Limita número de requisições por IP e endpoint
    """

    async def dispatch(self, request: Request, call_next):
        # Extrair IP do cliente
        client_ip = self._get_client_ip(request)
        endpoint = request.url.path

        # Verificar se IP está whitelisted
        if client_ip in RateLimitConfig.WHITELIST:
            return await call_next(request)

        # Verificar se IP está bloqueado
        if rate_limit_store.is_blocked(client_ip):
            remaining_time = rate_limit_store.get_remaining_block_time(client_ip)

            logger.warning(
                "Blocked IP attempted access", ip=client_ip, endpoint=endpoint, remaining_time=remaining_time
            )

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Too many requests",
                    "message": f"IP bloqueado temporariamente. Tente novamente em {remaining_time} segundos.",
                    "retry_after": remaining_time,
                },
                headers={"Retry-After": str(remaining_time)},
            )

        # Obter configuração de limite
        limit_config = RateLimitConfig.get_limit(endpoint)

        # Verificar rate limit
        request_count = rate_limit_store.get_request_count(client_ip, endpoint, limit_config["window"])

        if request_count >= limit_config["requests"]:
            # Limite excedido - bloquear IP
            rate_limit_store.block_ip(client_ip, duration_minutes=limit_config["block_duration"])

            # Logar para auditoria
            audit_logger.log_rate_limit_exceeded(
                user_id=None, username=None, ip_address=client_ip, endpoint=endpoint, limit=limit_config["requests"]
            )

            logger.warning(
                "Rate limit exceeded",
                ip=client_ip,
                endpoint=endpoint,
                limit=limit_config["requests"],
                window=limit_config["window"],
                count=request_count,
            )

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": (
                        f"Limite de {limit_config['requests']} requisições " f"por {limit_config['window']}s excedido."
                    ),
                    "limit": limit_config["requests"],
                    "window": limit_config["window"],
                    "retry_after": limit_config["window"],
                },
                headers={
                    "X-RateLimit-Limit": str(limit_config["requests"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(limit_config["window"]),
                    "Retry-After": str(limit_config["window"]),
                },
            )

        # Registrar requisição
        rate_limit_store.add_request(client_ip, endpoint)

        # Calcular requisições restantes
        remaining = limit_config["requests"] - request_count - 1

        # Processar requisição
        response = await call_next(request)

        # Adicionar headers de rate limit
        response.headers["X-RateLimit-Limit"] = str(limit_config["requests"])
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(limit_config["window"])

        return response

    def _get_client_ip(self, request: Request) -> str:
        """
        Extrai IP real do cliente

        Considera headers de proxy (X-Forwarded-For, X-Real-IP)
        """
        # Verificar headers de proxy
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Pegar primeiro IP da lista (cliente original)
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback para IP direto
        return request.client.host


# ============================================================================
# Funções de Gerenciamento
# ============================================================================


def get_rate_limit_stats() -> dict:
    """
    Retorna estatísticas de rate limiting

    Returns:
        Dicionário com estatísticas
    """
    total_requests = sum(len(endpoints) for endpoints in rate_limit_store.requests.values())

    blocked_ips = len(rate_limit_store.blocked_ips)

    # Top IPs por número de requisições
    ip_counts = {}
    for ip, endpoints in rate_limit_store.requests.items():
        total = sum(len(requests) for requests in endpoints.values())
        ip_counts[ip] = total

    top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "total_tracked_ips": len(rate_limit_store.requests),
        "total_requests_tracked": total_requests,
        "blocked_ips": blocked_ips,
        "blocked_ips_list": [
            {
                "ip": ip,
                "unblock_at": block_until.isoformat(),
                "remaining_seconds": (block_until - datetime.utcnow()).total_seconds(),
            }
            for ip, block_until in rate_limit_store.blocked_ips.items()
        ],
        "top_ips": [{"ip": ip, "requests": count} for ip, count in top_ips],
    }


def unblock_ip(ip: str) -> bool:
    """
    Remove bloqueio de IP manualmente

    Args:
        ip: Endereço IP a desbloquear

    Returns:
        True se IP estava bloqueado, False caso contrário
    """
    if ip in rate_limit_store.blocked_ips:
        del rate_limit_store.blocked_ips[ip]
        logger.info("IP manually unblocked", ip=ip)
        return True
    return False


def clear_rate_limit_data():
    """
    Limpa todos os dados de rate limiting

    Útil para testes ou reset manual
    """
    rate_limit_store.requests.clear()
    rate_limit_store.blocked_ips.clear()
    logger.info("Rate limit data cleared")
