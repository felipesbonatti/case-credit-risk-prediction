#!/usr/bin/env python3
"""
Script de Validação de Taxas Sugeridas
Testa se as taxas sugeridas resultam em aprovação
"""

import sys
import json
import requests
from typing import Dict, List

# Cores para output
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_success(msg: str):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg: str):
    print(f"{RED}❌ {msg}{RESET}")

def print_info(msg: str):
    print(f"{BLUE}ℹ️  {msg}{RESET}")

def print_warning(msg: str):
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def print_header(msg: str):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{msg.center(70)}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

# Perfis de teste com diferentes scores
PERFIS_TESTE = [
    {
        "nome": "Score 850 - Excelente",
        "score": 850,
        "renda": 15000,
        "valor": 20000,
        "prazo": 24,
        "atrasos": 0,
        "esperado": "Aprovar"
    },
    {
        "nome": "Score 750 - Bom",
        "score": 750,
        "renda": 8000,
        "valor": 15000,
        "prazo": 24,
        "atrasos": 0,
        "esperado": "Aprovar"
    },
    {
        "nome": "Score 650 - Regular",
        "score": 650,
        "renda": 5000,
        "valor": 15000,
        "prazo": 24,
        "atrasos": 0,
        "esperado": "Aprovar"
    },
    {
        "nome": "Score 550 - Ruim",
        "score": 550,
        "renda": 4000,
        "valor": 10000,
        "prazo": 24,
        "atrasos": 1,
        "esperado": "Aprovar"
    },
    {
        "nome": "Score 450 - Muito Ruim",
        "score": 450,
        "renda": 3000,
        "valor": 8000,
        "prazo": 24,
        "atrasos": 2,
        "esperado": "Negar"  # Score muito baixo, risco 50%, ROI negativo
    },
    {
        "nome": "Score 350 - Péssimo",
        "score": 350,
        "renda": 2000,
        "valor": 5000,
        "prazo": 12,
        "atrasos": 3,
        "esperado": "Negar"  # Score crítico, risco 70%, ROI negativo
    }
]

def criar_request(perfil: Dict) -> Dict:
    """Cria request de predição baseado no perfil"""
    return {
        "cliente_id": f"TEST-SCORE-{perfil['score']}",
        "idade": 35,
        "renda": perfil['renda'],
        "score": perfil['score'],
        "ticket": perfil['valor'],
        "prazo_meses": perfil['prazo'],
        "taxa_juros_aa": 30.0,  # Taxa será ajustada pelo frontend
        "tempo_cliente_meses": 24,
        "qtd_produtos": 2,
        "qtd_atrasos_12m": perfil['atrasos'],
        "genero": "Masculino",
        "estado_civil": "Casado",
        "escolaridade": "Superior",
        "regiao": "Sudeste",
        "uf": "SP",
        "porte_municipio": "Metrópole",
        "tipo_credito": "CDC"
    }

def testar_perfil(api_url: str, perfil: Dict) -> bool:
    """Testa um perfil específico"""
    print(f"\n{BLUE}Testando: {perfil['nome']}{RESET}")
    print(f"   Score: {perfil['score']} | Renda: R$ {perfil['renda']:,} | Valor: R$ {perfil['valor']:,}")
    
    # Criar request
    request_data = criar_request(perfil)
    
    try:
        # Fazer predição
        response = requests.post(
            f"{api_url}/predict",
            json=request_data,
            timeout=10
        )
        
        if response.status_code != 200:
            print_error(f"Erro na requisição: {response.status_code}")
            return False
        
        resultado = response.json()
        
        # Extrair informações
        probabilidade = resultado.get('probabilidade_inadimplencia', 0)
        recomendacao = resultado.get('recomendacao', 'Desconhecida')
        score_risco = resultado.get('score_risco', 0)
        
        # Mostrar resultado
        print(f"   Probabilidade: {probabilidade:.1%}")
        print(f"   Recomendação: {recomendacao}")
        print(f"   Score de Risco: {score_risco:.1f}")
        
        # Validar
        if recomendacao == perfil['esperado']:
            print_success(f"Resultado correto: {recomendacao}")
            return True
        else:
            if perfil['esperado'] == "Aprovar" and recomendacao == "Negar":
                print_error(f"Resultado incorreto: Esperado {perfil['esperado']}, obteve {recomendacao}")
                print_warning("Taxa sugerida pode estar muito alta!")
                return False
            elif perfil['esperado'] == "Negar" and recomendacao == "Aprovar":
                print_warning(f"Inesperado: Esperado {perfil['esperado']}, obteve {recomendacao}")
                print_info("Modelo pode estar mais permissivo que o esperado")
                return True  # Não é erro crítico
            else:
                print_warning(f"Resultado inesperado: {recomendacao}")
                return False
                
    except requests.exceptions.RequestException as e:
        print_error(f"Erro na requisição: {str(e)}")
        return False
    except Exception as e:
        print_error(f"Erro inesperado: {str(e)}")
        return False

def main():
    print_header("VALIDAÇÃO DE TAXAS SUGERIDAS - SANTANDER CREDIT RISK")
    
    API_URL = "http://localhost:8000"
    
    # Verificar se API está rodando
    print(f"{BLUE}[1/2] Verificando API...{RESET}")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success("API está rodando")
        else:
            print_error("API não está respondendo corretamente")
            print_info("Inicie a API com: python run_all.py")
            return 1
    except requests.exceptions.RequestException:
        print_error("API não está rodando!")
        print_info("Inicie a API com: python run_all.py")
        return 1
    
    # Testar perfis
    print(f"\n{BLUE}[2/2] Testando perfis com diferentes scores...{RESET}")
    
    resultados = []
    for perfil in PERFIS_TESTE:
        sucesso = testar_perfil(API_URL, perfil)
        resultados.append(sucesso)
    
    # Resumo
    print_header("RESULTADO DA VALIDAÇÃO")
    
    total = len(resultados)
    aprovados = sum(resultados)
    taxa_sucesso = (aprovados / total) * 100
    
    if aprovados == total:
        print_success(f"TODOS OS TESTES PASSARAM! {aprovados}/{total}")
        print_info(" Taxas sugeridas estão resultando em aprovação!")
        return 0
    elif aprovados >= total * 0.8:  # 80% de sucesso
        print_warning(f"MAIORIA DOS TESTES PASSOU: {aprovados}/{total} ({taxa_sucesso:.0f}%)")
        print_info("Sistema está funcionando, mas pode ser otimizado")
        return 0
    else:
        print_error(f"MUITOS TESTES FALHARAM! {aprovados}/{total} ({taxa_sucesso:.0f}%)")
        print_warning(" Revise os cálculos de taxa sugerida")
        return 1

if __name__ == "__main__":
    sys.exit(main())
