"""
Cache Manager com fallback local
Suporta Redis quando disponível, caso contrário usa cache em memória
"""

import pickle
import time
from pathlib import Path
from typing import Any, Optional
import structlog

logger = structlog.get_logger()


class CacheManager:
    """
    Gerenciador de cache com fallback local

    Tenta usar Redis se disponível, caso contrário usa cache em memória (pickle)
    """

    def __init__(self, cache_dir: str = "cache", default_ttl: int = 3600):
        """
        Inicializa o cache manager

        Args:
            cache_dir: Diretório para cache local
            default_ttl: Tempo de vida padrão em segundos (1 hora)
        """
        self.default_ttl = default_ttl
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.backend = "local"

        # Tentar conectar ao Redis
        try:
            import redis

            self.redis_client = redis.Redis(
                host="localhost", port=6379, db=0, decode_responses=False, socket_connect_timeout=1
            )
            # Testar conexão
            self.redis_client.ping()
            self.backend = "redis"
            logger.info("cache_initialized", backend="redis")
        except Exception as e:
            # Redis não disponível, usar cache local silenciosamente
            self.redis_client = None
            logger.info("cache_initialized", backend="local", cache_dir=str(self.cache_dir))

    def _get_cache_path(self, key: str) -> Path:
        """Retorna o caminho do arquivo de cache para uma chave"""
        # Sanitizar key para nome de arquivo válido
        safe_key = "".join(c if c.isalnum() or c in "._-" else "_" for c in key)
        return self.cache_dir / f"{safe_key}.pkl"

    def get(self, key: str) -> Optional[Any]:
        """
        Recupera valor do cache

        Args:
            key: Chave do cache

        Returns:
            Valor armazenado ou None se não encontrado/expirado
        """
        if self.backend == "redis" and self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    return pickle.loads(value)
                return None
            except Exception as e:
                logger.warning("redis_get_error", key=key, error=str(e))
                # Fallback para cache local
                return self._get_local(key)
        else:
            return self._get_local(key)

    def _get_local(self, key: str) -> Optional[Any]:
        """Recupera valor do cache local"""
        cache_file = self._get_cache_path(key)

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "rb") as f:
                data = pickle.load(f)

            # Verificar se expirou
            if "expires_at" in data and data["expires_at"] < time.time():
                cache_file.unlink()  # Remover arquivo expirado
                return None

            return data.get("value")
        except Exception as e:
            logger.warning("local_cache_get_error", key=key, error=str(e))
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Armazena valor no cache

        Args:
            key: Chave do cache
            value: Valor a armazenar
            ttl: Tempo de vida em segundos (usa default_ttl se None)

        Returns:
            True se armazenado com sucesso
        """
        ttl = ttl or self.default_ttl

        if self.backend == "redis" and self.redis_client:
            try:
                serialized = pickle.dumps(value)
                self.redis_client.setex(key, ttl, serialized)
                return True
            except Exception as e:
                logger.warning("redis_set_error", key=key, error=str(e))
                # Fallback para cache local
                return self._set_local(key, value, ttl)
        else:
            return self._set_local(key, value, ttl)

    def _set_local(self, key: str, value: Any, ttl: int) -> bool:
        """Armazena valor no cache local"""
        cache_file = self._get_cache_path(key)

        try:
            data = {"value": value, "expires_at": time.time() + ttl, "created_at": time.time()}

            with open(cache_file, "wb") as f:
                pickle.dump(data, f)

            return True
        except Exception as e:
            logger.warning("local_cache_set_error", key=key, error=str(e))
            return False

    def delete(self, key: str) -> bool:
        """
        Remove valor do cache

        Args:
            key: Chave do cache

        Returns:
            True se removido com sucesso
        """
        if self.backend == "redis" and self.redis_client:
            try:
                self.redis_client.delete(key)
                return True
            except Exception as e:
                logger.warning("redis_delete_error", key=key, error=str(e))
                return self._delete_local(key)
        else:
            return self._delete_local(key)

    def _delete_local(self, key: str) -> bool:
        """Remove valor do cache local"""
        cache_file = self._get_cache_path(key)

        try:
            if cache_file.exists():
                cache_file.unlink()
            return True
        except Exception as e:
            logger.warning("local_cache_delete_error", key=key, error=str(e))
            return False

    def clear(self) -> bool:
        """
        Limpa todo o cache

        Returns:
            True se limpo com sucesso
        """
        if self.backend == "redis" and self.redis_client:
            try:
                self.redis_client.flushdb()
                return True
            except Exception as e:
                logger.warning("redis_clear_error", error=str(e))
                return self._clear_local()
        else:
            return self._clear_local()

    def _clear_local(self) -> bool:
        """Limpa cache local"""
        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
            return True
        except Exception as e:
            logger.warning("local_cache_clear_error", error=str(e))
            return False

    def cleanup_expired(self) -> int:
        """
        Remove entradas expiradas do cache local

        Returns:
            Número de entradas removidas
        """
        if self.backend == "redis":
            # Redis faz isso automaticamente
            return 0

        removed = 0
        current_time = time.time()

        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                try:
                    with open(cache_file, "rb") as f:
                        data = pickle.load(f)

                    if "expires_at" in data and data["expires_at"] < current_time:
                        cache_file.unlink()
                        removed += 1
                except Exception:
                    # Se não conseguir ler, remover arquivo corrompido
                    cache_file.unlink()
                    removed += 1
        except Exception as e:
            logger.warning("cleanup_error", error=str(e))

        return removed


# Instância global do cache manager
cache_manager = CacheManager()
