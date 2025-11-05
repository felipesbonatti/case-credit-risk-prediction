#!/usr/bin/env python3.11
"""
Cria dataset demo com 1M de registros enriquecidos
Mantém distribuições estatísticas realistas
"""

import pandas as pd
import numpy as np
from pathlib import Path

print("Criando dataset demo enriquecido (1M registros)...")

# Determinar caminho base
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"

# Carregar amostra
df_original = pd.read_parquet(DATA_DIR / 'dataset_modelo_sintetico_v3.parquet', engine='pyarrow')
df = df_original.sample(n=1_000_000, random_state=42).reset_index(drop=True)
print(f"[OK] Amostra de {len(df):,} registros")

# Enriquecer (operações vetorizadas)
np.random.seed(42)

# Score
df['score'] = df['score'].fillna(df['score'].median()).round().clip(300, 950).astype(int)

# Demográficas
df['idade'] = np.clip(np.random.normal(40, 15, len(df)), 18, 80).astype(int)
df['score'] = (df['score'] + (df['idade'] - 40) * 1.5).clip(300, 950).astype(int)
df['tempo_relacionamento'] = np.clip((df['idade'] - 18) * 0.6 + np.random.exponential(3, len(df)), 0, 40).astype(int)
prob_produtos = (df['tempo_relacionamento'] / 40 * 0.5 + df['score'] / 950 * 0.5)
df['qtd_produtos_ativos'] = np.random.binomial(10, prob_produtos).clip(1, 10)

# Categorias
df['tipo_produto'] = np.random.choice(['CDC', 'Cartão', 'Imobiliário', 'Pessoal'], len(df), p=[0.35, 0.25, 0.10, 0.30])
df['regiao'] = np.random.choice(['Sudeste', 'Sul', 'Nordeste', 'Centro-Oeste', 'Norte'], len(df), p=[0.42, 0.15, 0.28, 0.08, 0.07])
df['canal'] = np.random.choice(['App', 'Agência', 'Parceiro', 'Internet Banking'], len(df), p=[0.40, 0.30, 0.15, 0.15])

# Prazo e taxa
prazo_ranges = {'CDC': (12, 60), 'Cartão': (1, 12), 'Imobiliário': (120, 420), 'Pessoal': (12, 48)}
df['prazo'] = df['tipo_produto'].apply(lambda x: np.random.randint(*prazo_ranges[x]))

taxa_base = df['tipo_produto'].map({'CDC': 2.5, 'Cartão': 8.0, 'Imobiliário': 0.8, 'Pessoal': 2.8})
ajuste = (950 - df['score']) / 650 * taxa_base * 0.5
df['taxa'] = (taxa_base + ajuste + np.random.normal(0, taxa_base * 0.1, len(df))).clip(0.5, 15.0).round(2)

# Ticket
df['valor_renda_ratio'] = np.random.uniform(0.3, 1.5, len(df))
ajuste_prod = df['tipo_produto'].map({'CDC': 0.5, 'Cartão': 0.2, 'Imobiliário': 3.0, 'Pessoal': 0.5})
df['ticket'] = (df['renda'] * df['prazo'] * df['valor_renda_ratio'] * ajuste_prod).clip(1000, 500000).round(2)

# Inadimplência
fator_score = (950 - df['score']) / 650 * 0.5
fator_renda = np.where(df['renda'] < 2000, 0.3, 0)
fator_vr = np.where(df['valor_renda_ratio'] > 1.0, 0.2, 0)
fator_prod = df['tipo_produto'].map({'CDC': 0.75, 'Cartão': 1.25, 'Imobiliário': 0.21, 'Pessoal': 0.80})
prob_inad = (0.068 * (1 + fator_score + fator_renda + fator_vr) * fator_prod).clip(0.01, 0.95)
df['inadimplente'] = np.random.binomial(1, prob_inad)
df['dias_atraso'] = 0
mask_inad = df['inadimplente'] == 1
df.loc[mask_inad, 'dias_atraso'] = np.random.randint(91, 360, mask_inad.sum())

# LGD e provisão
lgd_base = df['tipo_produto'].map({'CDC': 0.55, 'Cartão': 0.70, 'Imobiliário': 0.35, 'Pessoal': 0.60})
df['lgd'] = (lgd_base + np.random.normal(0, 0.05, len(df))).clip(0.2, 0.9).round(3)
df['perda_esperada'] = df['ticket'] * df['inadimplente'] * df['lgd']

df['provisao_stage'] = 'Stage 1'
df.loc[(df['score'] < 600) | ((df['dias_atraso'] > 0) & (df['dias_atraso'] <= 90)), 'provisao_stage'] = 'Stage 2'
df.loc[df['dias_atraso'] > 90, 'provisao_stage'] = 'Stage 3'

# Salvar
output = DATA_DIR / 'dataset_demo_1m.parquet'
df.to_parquet(output, index=False)

print(f"\n[OK] Dataset salvo: {output.name}")
print(f"   Tamanho: {output.stat().st_size / 1024 / 1024:.1f} MB")
print(f"   Taxa Inadimplência: {df['inadimplente'].mean() * 100:.2f}%")
print(f"   Valor Total: R$ {df['ticket'].sum() / 1e9:.2f} bi")
print(f"   Colunas: {list(df.columns)}")

