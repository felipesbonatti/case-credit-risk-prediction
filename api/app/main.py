"""
Santander Credit Risk Platform - API Main
FastAPI application entry point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
import structlog
import time

from app.routes import health, predict, metrics, test_real, analysis, auth
from app.middleware.logging import LoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.utils.config import settings
from app.utils.logger import setup_logging
from app.services.model_service import ModelService
from app.security.audit import setup_audit_logging, audit_logger, AuditEventType, AuditSeverity
from app import __version__

# Setup logging
setup_logging()
setup_audit_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    """
    # Startup
    logger.info("Starting Santander Credit Risk API")
    audit_logger.log_event(
        event_type=AuditEventType.MODEL_LOADED, severity=AuditSeverity.INFO, details={"message": "API starting up"}
    )

    # Load ML model
    try:
        model_service = ModelService()
        await model_service.load_model()
        app.state.model_service = model_service
        logger.info("ML model loaded successfully")
        audit_logger.log_event(
            event_type=AuditEventType.MODEL_LOADED,
            severity=AuditSeverity.INFO,
            details={
                "model_type": type(model_service.model).__name__,
                "features": len(model_service.feature_cols),
                "version": model_service.model_version,
            },
        )
    except Exception as e:
        logger.error(f"Failed to load ML model: {e}")
        audit_logger.log_system_error(error_type="ModelLoadError", error_message=str(e))
        raise

    yield

    # Shutdown
    logger.info("Shutting down Santander Credit Risk API")


# Create FastAPI app
app = FastAPI(
    title="Santander Credit Risk API",
    description="Machine Learning API for credit risk prediction",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ------------------------------------------------------------------------------
# Middleware
# ------------------------------------------------------------------------------

# CORS (RESTRITO PARA PRODUÇÃO)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # Configurar apenas domínios autorizados
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Métodos específicos
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],  # Headers específicos
    max_age=3600,  # Cache de preflight por 1 hora
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Custom middleware
app.add_middleware(LoggingMiddleware)

if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(RateLimitMiddleware)

# ------------------------------------------------------------------------------
# Exception Handlers
# ------------------------------------------------------------------------------


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler
    """
    logger.error("Unhandled exception", exc_info=exc, path=request.url.path, method=request.method)

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred",
            "path": request.url.path,
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """
    ValueError handler
    """
    return JSONResponse(
        status_code=400, content={"error": "Validation error", "message": str(exc), "path": request.url.path}
    )


# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------

# Authentication (SEM AUTENTICAÇÃO PARA FACILITAR TESTES)
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])

# Health check (PÚBLICO)
app.include_router(health.router, prefix="/health", tags=["Health"])

# Prediction (PROTEGIDO POR JWT EM PRODUÇÃO)
app.include_router(predict.router, prefix="/api/v1/predict", tags=["Prediction"])

# Metrics
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["Metrics"])

# Model management
app.include_router(test_real.router, prefix="/api/v1", tags=["Test Real"])

# Analysis (ROC, Confusion Matrix, Optimization)
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/prometheus", metrics_app)

# ------------------------------------------------------------------------------
# Root endpoint
# ------------------------------------------------------------------------------


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint
    """
    return {
        "name": "Santander Credit Risk API",
        "version": __version__,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
    }


# ------------------------------------------------------------------------------
# Request timing middleware
# ------------------------------------------------------------------------------


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Add process time header to response
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        workers=settings.API_WORKERS if not settings.API_RELOAD else 1,
        log_level=settings.LOG_LEVEL.lower(),
    )
