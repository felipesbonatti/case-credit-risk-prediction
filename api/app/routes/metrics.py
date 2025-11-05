"""
Metrics Router - Dados Reais de 5 Milhões de Clientes
"""

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

router = APIRouter()

# Importar o data service
try:
    from app.services.data_service import data_service

    DATA_SERVICE_LOADED = True
except Exception as e:
    print(f"ERRO ao importar data_service: {e}")
    DATA_SERVICE_LOADED = False


@router.get("")
async def get_metrics_root(threshold: float = Query(default=0.5, ge=0.0, le=1.0)):
    """Get metrics com dados reais - rota raiz"""
    if not DATA_SERVICE_LOADED:
        return JSONResponse(status_code=500, content={"error": "Data service não carregado"})

    try:
        metrics = data_service.get_metrics(threshold=threshold)
        return metrics
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/")
async def get_metrics_slash(threshold: float = Query(default=0.5, ge=0.0, le=1.0)):
    """Get metrics com dados reais - rota com barra"""
    if not DATA_SERVICE_LOADED:
        return JSONResponse(status_code=500, content={"error": "Data service não carregado"})

    try:
        metrics = data_service.get_metrics(threshold=threshold)
        return metrics
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
