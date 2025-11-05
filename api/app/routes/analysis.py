"""
Analysis Router - Análise de Trade-off e Otimização
"""

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
import structlog
from app.utils.cache import cache_manager

logger = structlog.get_logger()
router = APIRouter()

# Importar o data service
try:
    from app.services.data_service import data_service

    DATA_SERVICE_LOADED = True
except Exception as e:
    print(f"ERRO ao importar data_service: {e}")
    DATA_SERVICE_LOADED = False


@router.get("/roc_curve")
async def get_roc_curve():
    """
    Retorna dados para curva ROC

    Cache: 1 hora (3600 segundos)
    """
    if not DATA_SERVICE_LOADED:
        return JSONResponse(status_code=500, content={"error": "Data service não carregado"})

    # Tentar recuperar do cache
    cache_key = "roc_curve_data"
    cached_data = cache_manager.get(cache_key)

    if cached_data is not None:
        logger.info("roc_curve_cache_hit")
        return cached_data

    # Se não estiver em cache, calcular
    try:
        logger.info("roc_curve_calculating")
        roc_data = data_service.get_roc_curve_data()

        # Armazenar em cache por 1 hora
        cache_manager.set(cache_key, roc_data, ttl=3600)
        logger.info("roc_curve_cached")

        return roc_data
    except Exception as e:
        logger.error("roc_curve_error", error=str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/confusion_matrix")
async def get_confusion_matrix(threshold: float = Query(default=0.5, ge=0.0, le=1.0)):
    """Retorna matriz de confusão para um threshold específico"""
    if not DATA_SERVICE_LOADED:
        return JSONResponse(status_code=500, content={"error": "Data service não carregado"})

    try:
        confusion_data = data_service.get_confusion_matrix(threshold=threshold)
        return confusion_data
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/threshold_sensitivity")
async def get_threshold_sensitivity():
    """Retorna análise de sensibilidade do threshold"""
    if not DATA_SERVICE_LOADED:
        return JSONResponse(status_code=500, content={"error": "Data service não carregado"})

    try:
        sensitivity_data = data_service.get_threshold_sensitivity()
        return sensitivity_data
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/optimize_threshold")
async def optimize_threshold(objective: str = Query(default="profit")):
    """
    Otimiza o threshold baseado em diferentes objetivos

    Objetivos disponíveis:
    - profit: Maximizar lucro
    - risk: Minimizar risco
    - balanced: Balancear aprovação e inadimplência
    """
    if not DATA_SERVICE_LOADED:
        return JSONResponse(status_code=500, content={"error": "Data service não carregado"})

    try:
        optimization_result = data_service.optimize_threshold(objective=objective)
        return optimization_result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
