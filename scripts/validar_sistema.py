#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Validação do Sistema - Santander Credit Risk Platform
Verifica se todos os componentes estão prontos
"""

import sys
from pathlib import Path
import joblib

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

def check_file_exists(path, description):
    """Verifica se arquivo existe"""
    if path.exists():
        size_mb = path.stat().st_size / 1024 / 1024
        print_success(f"{description}: {path.name} ({size_mb:.1f} MB)")
        return True
    else:
        print_error(f"{description} NÃO ENCONTRADO: {path}")
        return False

def validate_model(model_path):
    """Valida modelo ML"""
    try:
        model = joblib.load(model_path)
        
        # Verificar se tem predict_proba
        if not hasattr(model, 'predict_proba'):
            print_error("Modelo não tem método predict_proba()")
            return False
        
        # Verificar features
        if hasattr(model, 'n_features_in_'):
            print_success(f"Modelo espera {model.n_features_in_} features")
        
        print_success(f"Modelo validado: {type(model).__name__}")
        return True
    except Exception as e:
        print_error(f"Erro ao validar modelo: {e}")
        return False

def validate_encoders(encoders_path):
    """Valida label encoders"""
    try:
        encoders = joblib.load(encoders_path)
        
        expected_encoders = [
            'faixa_etaria', 'genero', 'estado_civil', 'escolaridade',
            'regiao', 'uf', 'porte_municipio', 'tipo_credito'
        ]
        
        for encoder_name in expected_encoders:
            if encoder_name not in encoders:
                print_warning(f"Encoder ausente: {encoder_name}")
        
        print_success(f"Encoders validados: {len(encoders)} encoders")
        return True
    except Exception as e:
        print_error(f"Erro ao validar encoders: {e}")
        return False

def validate_features(features_path):
    """Valida lista de features"""
    try:
        features = joblib.load(features_path)
        
        if len(features) != 21:
            print_warning(f"Número de features diferente de 21: {len(features)}")
        
        print_success(f"Features validadas: {len(features)} features")
        return True
    except Exception as e:
        print_error(f"Erro ao validar features: {e}")
        return False

def validate_dataset(dataset_path):
    """Valida dataset"""
    try:
        import pandas as pd
        df = pd.read_parquet(dataset_path)
        
        required_columns = [
            'score', 'renda', 'idade', 'ticket', 'prazo_meses',
            'taxa_juros_aa', 'inadimplente'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print_error(f"Colunas ausentes no dataset: {missing_columns}")
            return False
        
        print_success(f"Dataset validado: {len(df):,} registros, {len(df.columns)} colunas")
        
        # Estatísticas
        taxa_inadimplencia = df['inadimplente'].mean() * 100
        print(f"   Taxa de inadimplência: {taxa_inadimplencia:.2f}%")
        
        return True
    except Exception as e:
        print_error(f"Erro ao validar dataset: {e}")
        return False

def main():
    print_header("VALIDAÇÃO DO SISTEMA - SANTANDER CREDIT RISK")
    
    # Determinar diretório base
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    print(f"Diretório base: {BASE_DIR}\n")
    
    # Lista de verificações
    checks = []
    
    # 1. Verificar estrutura de diretórios
    print(f"{BLUE}[1/5] Verificando estrutura de diretórios...{RESET}")
    api_dir = BASE_DIR / "api"
    data_dir = BASE_DIR / "data" / "processed"
    scripts_dir = BASE_DIR / "scripts"
    
    checks.append(check_file_exists(api_dir, "Diretório API"))
    checks.append(check_file_exists(data_dir, "Diretório de dados"))
    checks.append(check_file_exists(scripts_dir, "Diretório de scripts"))
    
    # 2. Verificar modelo ML
    print(f"\n{BLUE}[2/5] Verificando modelo ML...{RESET}")
    model_path = api_dir / "modelo_lgbm.pkl"
    if check_file_exists(model_path, "Modelo LightGBM"):
        checks.append(validate_model(model_path))
    else:
        checks.append(False)
    
    # 3. Verificar encoders
    print(f"\n{BLUE}[3/5] Verificando encoders...{RESET}")
    encoders_path = api_dir / "label_encoders.pkl"
    if check_file_exists(encoders_path, "Label Encoders"):
        checks.append(validate_encoders(encoders_path))
    else:
        checks.append(False)
    
    # 4. Verificar features
    print(f"\n{BLUE}[4/5] Verificando features...{RESET}")
    features_path = api_dir / "feature_cols.pkl"
    if check_file_exists(features_path, "Features"):
        checks.append(validate_features(features_path))
    else:
        checks.append(False)
    
    # 5. Verificar dataset
    print(f"\n{BLUE}[5/5] Verificando dataset...{RESET}")
    dataset_path = data_dir / "dataset_realista_1m.parquet"
    if check_file_exists(dataset_path, "Dataset"):
        checks.append(validate_dataset(dataset_path))
    else:
        checks.append(False)
    
    # Resultado final
    print_header("RESULTADO DA VALIDAÇÃO")
    
    total_checks = len(checks)
    passed_checks = sum(checks)
    
    if passed_checks == total_checks:
        print_success(f"SISTEMA PRONTO! {passed_checks}/{total_checks} verificações passaram")
        print(f"\n{GREEN} O sistema está pronto!{RESET}")
        print(f"{GREEN}Execute: python run_all.py{RESET}\n")
        return 0
    else:
        print_error(f"SISTEMA COM PROBLEMAS! {passed_checks}/{total_checks} verificações passaram")
        print(f"\n{RED}  Corrija os problemas antes de iniciar o sistema{RESET}")
        print(f"{YELLOW}Dica: Execute os scripts de geração de dados e treinamento:{RESET}")
        print(f"  1. python scripts/gerar_dados_REALISTICOS.py")
        print(f"  2. python scripts/treinar_modelo_SKLEARN.py\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
