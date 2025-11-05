"""
Endpoint de teste com dados reais
"""

from fastapi import APIRouter, Query
from app.services.data_service import data_service

router = APIRouter()


@router.get("/dados-reais")
async def get_dados_reais(threshold: float = Query(0.5, ge=0.0, le=1.0)):
    """
    Endpoint de teste com dados reais de 5 milhões de clientes
    """
    if data_service.df is None:
        return {
            "error": "Base de dados não carregada",
            "saldoLiquido": 0,
            "taxaAprovacao": 0,
            "taxaInadimplencia": 0,
            "totalClientes": 0,
        }

    metrics = data_service.get_metrics(threshold=threshold)
    return metrics
