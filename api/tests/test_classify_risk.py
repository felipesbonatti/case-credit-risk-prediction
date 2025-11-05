"""
Testes para função classify_risk
Validação da lógica de classificação de risco
"""

import pytest


def classify_risk(prob_default: float) -> str:
    """
    Classifica risco baseado na probabilidade de inadimplência

    Args:
        prob_default: Probabilidade de inadimplência (0-1)

    Returns:
        Categoria de risco
    """
    if prob_default > 0.7:
        return "Reprovado - Alto Risco"
    elif prob_default > 0.4:
        return "Atenção - Risco Moderado"
    else:
        return "Aprovado - Baixo Risco"


@pytest.mark.parametrize(
    "prob,expected",
    [
        (0.2, "Aprovado - Baixo Risco"),
        (0.5, "Atenção - Risco Moderado"),
        (0.9, "Reprovado - Alto Risco"),
        (0.0, "Aprovado - Baixo Risco"),
        (0.4, "Aprovado - Baixo Risco"),
        (0.40001, "Atenção - Risco Moderado"),
        (0.7, "Atenção - Risco Moderado"),
        (0.70001, "Reprovado - Alto Risco"),
        (1.0, "Reprovado - Alto Risco"),
    ],
)
def test_classify_risk(prob, expected):
    """
    Testa classificação de risco para diferentes probabilidades
    """
    assert classify_risk(prob) == expected


def test_classify_risk_boundaries():
    """
    Testa valores nos limites das categorias
    """
    # Limite inferior - Aprovado
    assert classify_risk(0.0) == "Aprovado - Baixo Risco"
    assert classify_risk(0.39999) == "Aprovado - Baixo Risco"

    # Limite Moderado
    assert classify_risk(0.4001) == "Atenção - Risco Moderado"
    assert classify_risk(0.6999) == "Atenção - Risco Moderado"

    # Limite Alto Risco
    assert classify_risk(0.7001) == "Reprovado - Alto Risco"
    assert classify_risk(1.0) == "Reprovado - Alto Risco"


def test_classify_risk_edge_cases():
    """
    Testa casos extremos
    """
    # Valores muito próximos aos limites
    assert classify_risk(0.40) == "Aprovado - Baixo Risco"
    assert classify_risk(0.70) == "Atenção - Risco Moderado"

    # Valores típicos de cada categoria
    assert classify_risk(0.25) == "Aprovado - Baixo Risco"
    assert classify_risk(0.55) == "Atenção - Risco Moderado"
    assert classify_risk(0.85) == "Reprovado - Alto Risco"
