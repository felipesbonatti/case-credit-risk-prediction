"""
Health check endpoints - Versão simplificada e robusta
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import structlog

router = APIRouter()
logger = structlog.get_logger()


@router.get("")
@router.get("/")
async def health_check(req: Request):
    """
    Health check endpoint simplificado

    Verifica:
    - Status do modelo ML
    - Retorna informações básicas de saúde

    Returns 503 se modelo não estiver carregado
    """
    try:
        model_service = req.app.state.model_service
        model_loaded = getattr(model_service, "model_loaded", False)

        if not model_loaded:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "version": "1.0.0-fixed",
                    "model_loaded": False,
                    "database": "not_configured",
                    "redis": "not_configured",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

        # Preparar resposta com dados seguros
        response_data = {
            "status": "healthy",
            "version": "1.0.0-fixed",
            "model_loaded": True,
            "model_type": type(model_service.model).__name__ if model_service.model else None,
            "model_features": len(model_service.feature_cols) if model_service.feature_cols else 0,
            "database": "not_configured",
            "redis": "not_configured",
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info("Health check OK")

        return JSONResponse(status_code=200, content=response_data)

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=503, content={"status": "error", "error": str(e), "timestamp": datetime.utcnow().isoformat()}
        )


@router.get("/liveness")
async def liveness():
    """
    Kubernetes liveness probe

    Verifica se a aplicação está rodando.
    Retorna 200 se o processo está vivo.
    """
    return JSONResponse(status_code=200, content={"status": "alive", "timestamp": datetime.utcnow().isoformat()})


@router.get("/readiness")
async def readiness(req: Request):
    """
    Kubernetes readiness probe

    Verifica se a aplicação está pronta para receber tráfego.
    Retorna 200 apenas se modelo estiver carregado.
    """
    try:
        model_service = req.app.state.model_service
        is_ready = getattr(model_service, "model_loaded", False)

        if is_ready:
            return JSONResponse(
                status_code=200,
                content={"status": "ready", "model_loaded": True, "timestamp": datetime.utcnow().isoformat()},
            )
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "reason": "Model not loaded",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": str(e), "timestamp": datetime.utcnow().isoformat()},
        )


@router.get("/startup")
async def startup(req: Request):
    """
    Kubernetes startup probe

    Verifica se a aplicação terminou de inicializar.
    Usado para aplicações com startup lento (carregamento de modelo).
    """
    try:
        model_service = req.app.state.model_service
        is_started = getattr(model_service, "model_loaded", False)

        if is_started:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "started",
                    "model_loaded": True,
                    "model_version": getattr(model_service, "model_version", None),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "starting",
                    "reason": "Model still loading",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
    except Exception as e:
        logger.error(f"Startup check failed: {e}")
        return JSONResponse(
            status_code=503, content={"status": "failed", "reason": str(e), "timestamp": datetime.utcnow().isoformat()}
        )


@router.get("/metrics/health")
async def health_metrics(req: Request):
    """
    Endpoint detalhado de métricas de saúde para monitoramento

    Retorna informações detalhadas sobre o estado de todos os componentes
    """
    try:
        model_service = req.app.state.model_service

        model_info = {
            "loaded": getattr(model_service, "model_loaded", False),
            "type": type(model_service.model).__name__ if model_service.model else None,
            "version": getattr(model_service, "model_version", None),
            "features": len(model_service.feature_cols) if model_service.feature_cols else 0,
            "threshold": getattr(model_service, "threshold", None),
        }

        if hasattr(model_service, "metricas") and model_service.metricas:
            model_info["auc_roc"] = model_service.metricas.get("auc_roc")
            model_info["ks_statistic"] = model_service.metricas.get("ks_statistic")

        response_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "model": model_info,
            "database": {"status": "not_configured", "message": "Database persistence not implemented yet"},
            "cache": {"status": "not_configured", "message": "Redis cache not implemented yet"},
            "system": {"python_version": "3.11", "fastapi_version": "0.104.1"},
        }

        return JSONResponse(status_code=200, content=response_data)

    except Exception as e:
        logger.error(f"Health metrics failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=500, content={"status": "error", "error": str(e), "timestamp": datetime.utcnow().isoformat()}
        )
