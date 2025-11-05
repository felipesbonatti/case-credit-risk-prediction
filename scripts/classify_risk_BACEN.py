"""
Função de Classificação de Risco - Baseada em Normas BACEN e Santander
Resolução BACEN 2682/1999 + Critérios Santander 2025
"""

def classify_risk_bacen(probability: float) -> dict:
    """
    Classifica risco de crédito baseado em normas BACEN 2682/1999 e critérios Santander.
    
    Args:
        probability: Probabilidade de inadimplência (0.0 a 1.0)
    
    Returns:
        dict com:
            - nivel_bacen: Nível BACEN (AA a H)
            - classificacao: Classificação textual
            - decisao: Decisão de crédito
            - provisao: Percentual de provisão BACEN
            - cor: Cor para interface (verde/amarelo/laranja/vermelho)
    """
    prob_percent = probability * 100
    
    # Mapeamento baseado em BACEN 2682/1999 + Santander
    if prob_percent <= 0.5:
        return {
            "nivel_bacen": "AA",
            "classificacao": "Risco Mínimo",
            "decisao": "Aprovar",
            "provisao": 0.0,
            "cor": "verde",
            "descricao": "Excelente perfil de crédito"
        }
    elif prob_percent <= 1.0:
        return {
            "nivel_bacen": "A",
            "classificacao": "Risco Baixo",
            "decisao": "Aprovar",
            "provisao": 0.5,
            "cor": "verde",
            "descricao": "Ótimo perfil de crédito"
        }
    elif prob_percent <= 3.0:
        return {
            "nivel_bacen": "B",
            "classificacao": "Risco Moderado",
            "decisao": "Aprovar",
            "provisao": 1.0,
            "cor": "verde",
            "descricao": "Bom perfil de crédito"
        }
    elif prob_percent <= 10.0:
        return {
            "nivel_bacen": "C",
            "classificacao": "Risco Médio",
            "decisao": "Revisar",
            "provisao": 3.0,
            "cor": "amarelo",
            "descricao": "Análise criteriosa necessária"
        }
    elif prob_percent <= 30.0:
        return {
            "nivel_bacen": "D",
            "classificacao": "Risco Alto",
            "decisao": "Revisar com Restrições",
            "provisao": 10.0,
            "cor": "laranja",
            "descricao": "Exigir garantias adicionais"
        }
    elif prob_percent <= 50.0:
        return {
            "nivel_bacen": "E",
            "classificacao": "Risco Elevado",
            "decisao": "Negar",
            "provisao": 30.0,
            "cor": "vermelho",
            "descricao": "Risco inaceitável"
        }
    elif prob_percent <= 70.0:
        return {
            "nivel_bacen": "F",
            "classificacao": "Risco Muito Elevado",
            "decisao": "Negar",
            "provisao": 50.0,
            "cor": "vermelho",
            "descricao": "Risco crítico"
        }
    elif prob_percent <= 100.0:
        return {
            "nivel_bacen": "G",
            "classificacao": "Risco Crítico",
            "decisao": "Negar",
            "provisao": 70.0,
            "cor": "vermelho",
            "descricao": "Inadimplência provável"
        }
    else:
        return {
            "nivel_bacen": "H",
            "classificacao": "Perda",
            "decisao": "Negar",
            "provisao": 100.0,
            "cor": "vermelho",
            "descricao": "Inadimplência confirmada"
        }


# Função simplificada para dashboard (3 níveis)
def classify_risk_simple(probability: float) -> str:
    """
    Classificação simplificada em 3 níveis para dashboard.
    Baseada em BACEN 2682/1999.
    
    Args:
        probability: Probabilidade de inadimplência (0.0 a 1.0)
    
    Returns:
        str: "Aprovado - Baixo Risco" | "Atenção - Risco Moderado" | "Reprovado - Alto Risco"
    """
    prob_percent = probability * 100
    
    if prob_percent <= 10.0:
        # Níveis BACEN: AA, A, B, C (0-10%)
        return "Aprovado - Baixo Risco"
    elif prob_percent <= 30.0:
        # Nível BACEN: D (10-30%)
        return "Atenção - Risco Moderado"
    else:
        # Níveis BACEN: E, F, G, H (>30%)
        return "Reprovado - Alto Risco"


# Testes
if __name__ == "__main__":
    print("=== TESTES DE CLASSIFICAÇÃO BACEN ===\n")
    
    test_cases = [
        (0.001, "Score 950 - Excelente"),
        (0.005, "Score 900 - Muito Bom"),
        (0.02, "Score 800 - Bom"),
        (0.05, "Score 700 - Regular"),
        (0.15, "Score 600 - Atenção"),
        (0.308, "Score 300 - Péssimo (caso real)"),
        (0.40, "Score 250 - Crítico"),
        (0.80, "Score 200 - Inadimplente"),
    ]
    
    for prob, descricao in test_cases:
        result = classify_risk_bacen(prob)
        simple = classify_risk_simple(prob)
        print(f"{descricao}")
        print(f"  Probabilidade: {prob*100:.1f}%")
        print(f"  Nível BACEN: {result['nivel_bacen']}")
        print(f"  Classificação: {result['classificacao']}")
        print(f"  Decisão: {result['decisao']}")
        print(f"  Provisão: {result['provisao']}%")
        print(f"  Dashboard: {simple}")
        print()
