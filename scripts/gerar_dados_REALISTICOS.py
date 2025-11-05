#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
Gerador de Dados Sintéticos REALISTAS para Credit Risk
Com lógica de negócio correta: score baixo = alto risco
"""

import pandas as pd
import numpy as np
from pathlib import Path

print("=" * 80)
print("GERADOR DE DADOS SINTETICOS REALISTAS - CREDIT RISK")
print("=" * 80)

np.random.seed(42)
n_samples = 1000000

print(f"\n[1/4] Gerando {n_samples:,} registros com logica de negocio...")

# Gerar features base
data = {
    'id': range(1, n_samples + 1),
    'score': np.random.randint(300, 950, n_samples),
    'renda': np.random.choice(
        [500, 1000, 2000, 3000, 5000, 8000, 12000, 20000],
        n_samples,
        p=[0.05, 0.10, 0.15, 0.20, 0.25, 0.15, 0.07, 0.03]
    ),
    'idade': np.random.randint(18, 70, n_samples),
    'tempo_cliente_meses': np.random.randint(1, 120, n_samples),
    'qtd_produtos': np.random.randint(1, 6, n_samples),
    'ticket': np.random.choice(
        [1000, 5000, 10000, 20000, 50000, 100000, 200000],
        n_samples,
        p=[0.20, 0.30, 0.25, 0.15, 0.07, 0.02, 0.01]
    ),
    'prazo_meses': np.random.choice([6, 12, 24, 36, 48, 60, 84, 120], n_samples),
    'taxa_juros_aa': np.random.uniform(8, 20, n_samples),
    'tipo_credito': np.random.choice(['CDC', 'Imobiliário', 'Cartão', 'Pessoal'], n_samples),
    'regiao': np.random.choice(['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul'], n_samples),
    'genero': np.random.choice(['Masculino', 'Feminino'], n_samples),
    'estado_civil': np.random.choice(['Solteiro', 'Casado', 'Divorciado', 'Viúvo'], n_samples),
    'escolaridade': np.random.choice(['Fundamental', 'Médio', 'Superior', 'Pós-Graduação'], n_samples),
    'uf': np.random.choice(['SP', 'RJ', 'MG', 'RS', 'BA', 'PR'], n_samples),
    'porte_municipio': np.random.choice(['Pequeno', 'Médio', 'Grande', 'Metrópole'], n_samples),
}

df = pd.DataFrame(data)

# Calcular features derivadas
print("\n[2/4] Calculando features derivadas...")
taxa_mensal = df['taxa_juros_aa'] / 12 / 100
df['parcela_mensal'] = np.where(
    taxa_mensal > 0,
    df['ticket'] * (taxa_mensal * (1 + taxa_mensal) ** df['prazo_meses']) / ((1 + taxa_mensal) ** df['prazo_meses'] - 1),
    df['ticket'] / df['prazo_meses']
)

df['perc_comprometimento_renda'] = (df['parcela_mensal'] / df['renda']) * 100
df['alto_comprometimento'] = (df['perc_comprometimento_renda'] > 30).astype(int)
df['fator_risco'] = (950 - df['score']) / 650

# Gerar atrasos baseado no score
df['qtd_atrasos_12m'] = np.where(
    df['score'] < 500, np.random.choice([0, 1, 2, 3, 4, 5], n_samples, p=[0.2, 0.2, 0.2, 0.2, 0.1, 0.1]),
    np.where(
        df['score'] < 700, np.random.choice([0, 1, 2], n_samples, p=[0.6, 0.3, 0.1]),
        np.random.choice([0, 0, 0, 1], n_samples, p=[0.85, 0.10, 0.04, 0.01])
    )
)

# LOGICA DE NEGOCIO REALISTA: Calcular probabilidade de inadimplencia
print("\n[3/4] Calculando inadimplencia com logica de negocio REALISTA...")

# Fatores de risco (quanto maior, mais risco)
risco_score = (950 - df['score']) / 650  # 0 a 1 (score baixo = alto risco)
risco_comprometimento = np.clip(df['perc_comprometimento_renda'] / 100, 0, 1)  # 0 a 1
risco_atrasos = np.clip(df['qtd_atrasos_12m'] / 5, 0, 1)  # 0 a 1
risco_tempo_cliente = np.clip((60 - df['tempo_cliente_meses']) / 60, 0, 1)  # Cliente novo = mais risco

# Probabilidade base de inadimplencia (combinacao ponderada)
prob_inadimplencia = (
    0.40 * risco_score +  # Score e o fator mais importante
    0.30 * risco_comprometimento +  # Comprometimento de renda
    0.20 * risco_atrasos +  # Historico de atrasos
    0.10 * risco_tempo_cliente  # Tempo de relacionamento
)

# Ajustar para ter taxa de inadimplencia realista (~6-8%)
prob_inadimplencia = np.clip(prob_inadimplencia ** 2, 0, 1)  # Reduzir probabilidades

# Gerar inadimplencia baseado na probabilidade
df['inadimplente'] = (np.random.random(n_samples) < prob_inadimplencia).astype(int)

taxa_inadimplencia = df['inadimplente'].mean() * 100
print(f"[OK] Taxa de inadimplencia: {taxa_inadimplencia:.2f}%")

# Validar logica
print("\n[INFO] Validacao da logica de negocio:")
print(f"   Inadimplencia (score < 400): {df[df['score'] < 400]['inadimplente'].mean()*100:.1f}%")
print(f"   Inadimplencia (score > 850): {df[df['score'] > 850]['inadimplente'].mean()*100:.1f}%")
print(f"   Inadimplencia (comprometimento > 50%): {df[df['perc_comprometimento_renda'] > 50]['inadimplente'].mean()*100:.1f}%")
print(f"   Inadimplencia (comprometimento < 20%): {df[df['perc_comprometimento_renda'] < 20]['inadimplente'].mean()*100:.1f}%")

# Salvar
print("\n[4/4] Salvando dataset...")
BASE_DIR = Path(__file__).resolve().parent.parent
output_dir = BASE_DIR / "data" / "processed"
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / 'dataset_realista_1m.parquet'
df.to_parquet(output_file, index=False)
print(f"[OK] Dataset salvo: {output_file}")
print(f"   Tamanho: {output_file.stat().st_size / 1024 / 1024:.1f} MB")

print("\n" + "=" * 80)
print("[OK] GERACAO DE DADOS CONCLUIDA!")
print("=" * 80)
print(f"\nDataset: {output_file}")
print(f"Registros: {len(df):,}")
print(f"Taxa inadimplencia: {taxa_inadimplencia:.2f}%")
print("\nProximo passo: Treinar modelo com os dados realistas")
