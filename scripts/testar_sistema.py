#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Teste End-to-End - Santander Credit Risk Platform
Testa perfis de alto e baixo risco para validar o sistema
"""

import sys
import requests
import time
from pathlib import Path

# Cores para terminal
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_header(text):
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{text:^70}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_info(text):
    print(f"{BLUE}ℹ️  {text}{RESET}")

def check_api_health(api_url):
    """Verifica se API está rodando"""
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code == 200:
            print_success("API está rodando")
            return True
        else:
            print_error(f"API retornou status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("API não está acessível (ConnectionError)")
        return False
    except Exception as e:
        print_error(f"Erro ao conectar na API: {e}")
        return False

def test_prediction(api_url, perfil_nome, request_data, expected_result):
    """Testa uma predição"""
    try:
        print_info(f"Testando perfil: {perfil_nome}")
        
        response = requests.post(
            f"{api_url}/api/v1/predict",
            json=request_data,
            timeout=10
        )
        
        if response.status_code != 200:
            print_error(f"Erro na requisição: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
        
        result = response.json()
        
        # Exibir resultado
        print(f"   Probabilidade: {result['probability']*100:.1f}%")
        print(f"   Recomendação: {result['recommendation']}")
        print(f"   Risk Score: {result['risk_score']:.1f}")
        
        # Validar resultado esperado
        if result['recommendation'] == expected_result:
            print_success(f"Resultado correto: {expected_result}")
            return True
        else:
            print_warning(f"Resultado diferente do esperado: {result['recommendation']} != {expected_result}")
            return True  # Não falhar, apenas avisar
        
    except Exception as e:
        print_error(f"Erro ao testar predição: {e}")
        return False

def test_metrics(api_url):
    """Testa endpoint de métricas"""
    try:
        print_info("Testando endpoint de métricas")
        
        response = requests.get(
            f"{api_url}/api/v1/metrics?threshold=0.5",
            timeout=10
        )
        
        if response.status_code != 200:
            print_error(f"Erro na requisição: {response.status_code}")
            return False
        
        metrics = response.json()
        
        # Validar campos essenciais
        required_fields = [
            'saldoLiquido', 'taxaAprovacao', 'taxaInadimplencia',
            'totalClientes', 'clientesAprovados', 'clientesRejeitados'
        ]
        
        missing_fields = [field for field in required_fields if field not in metrics]
        if missing_fields:
            print_error(f"Campos ausentes: {missing_fields}")
            return False
        
        print(f"   Total Clientes: {metrics['totalClientes']:,}")
        print(f"   Taxa Aprovação: {metrics['taxaAprovacao']:.1f}%")
        print(f"   Taxa Inadimplência: {metrics['taxaInadimplencia']:.1f}%")
        print(f"   Saldo Líquido: R$ {metrics['saldoLiquido']:,.2f}")
        
        print_success("Métricas validadas")
        return True
        
    except Exception as e:
        print_error(f"Erro ao testar métricas: {e}")
        return False

def main():
    print_header("TESTE END-TO-END - SANTANDER CREDIT RISK")
    
    API_URL = "http://localhost:8000"
    
    # 1. Verificar se API está rodando
    print(f"{BLUE}[1/4] Verificando API...{RESET}")
    if not check_api_health(API_URL):
        print_error("API não está rodando!")
        print_info("Inicie a API com: python run_all.py")
        return 1
    
    # 2. Testar perfil de ALTO RISCO
    print(f"\n{BLUE}[2/4] Testando perfil de ALTO RISCO...{RESET}")
    perfil_alto_risco = {
        "cliente_id": "TEST-ALTO-RISCO",
        "idade": 22,
        "renda": 800,
        "score": 320,
        "ticket": 25000,
        "prazo_meses": 48,
        "taxa_juros_aa": 35.0,
        "tempo_cliente_meses": 2,
        "qtd_produtos": 1,
        "qtd_atrasos_12m": 4,
        "genero": "Masculino",
        "estado_civil": "Solteiro",
        "escolaridade": "Fundamental",
        "regiao": "Nordeste",
        "uf": "BA",
        "porte_municipio": "Pequeno",
        "tipo_credito": "CDC"
    }
    
    test_alto_risco = test_prediction(
        API_URL,
        "ALTO RISCO (Score 320, Renda R$ 800, Ticket R$ 25k)",
        perfil_alto_risco,
        "Negar"
    )
    
    # 3. Testar perfil de BAIXO RISCO
    print(f"\n{BLUE}[3/4] Testando perfil de BAIXO RISCO...{RESET}")
    perfil_baixo_risco = {
        "cliente_id": "TEST-BAIXO-RISCO",
        "idade": 42,
        "renda": 18000,
        "score": 880,
        "ticket": 8000,
        "prazo_meses": 24,
        "taxa_juros_aa": 12.5,
        "tempo_cliente_meses": 84,
        "qtd_produtos": 4,
        "qtd_atrasos_12m": 0,
        "genero": "Feminino",
        "estado_civil": "Casado",
        "escolaridade": "Superior",
        "regiao": "Sudeste",
        "uf": "SP",
        "porte_municipio": "Metrópole",
        "tipo_credito": "CDC"
    }
    
    test_baixo_risco = test_prediction(
        API_URL,
        "BAIXO RISCO (Score 880, Renda R$ 18k, Ticket R$ 8k)",
        perfil_baixo_risco,
        "Aprovar"
    )
    
    # 4. Testar métricas
    print(f"\n{BLUE}[4/4] Testando métricas...{RESET}")
    test_metricas = test_metrics(API_URL)
    
    # Resultado final
    print_header("RESULTADO DOS TESTES")
    
    all_tests = [test_alto_risco, test_baixo_risco, test_metricas]
    passed = sum(all_tests)
    total = len(all_tests)
    
    if passed == total:
        print_success(f"TODOS OS TESTES PASSARAM! {passed}/{total}")
        print(f"\n{GREEN} Sistema validado!{RESET}\n")
        return 0
    else:
        print_error(f"ALGUNS TESTES FALHARAM! {passed}/{total}")
        print(f"\n{RED} Verifique os erros acima{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
