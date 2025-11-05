import pandas as pd
import numpy as np
from pathlib import Path

print("=" * 80)
print("CRIANDO DATASET DEMO - SANTANDER CREDIT RISK")
print("=" * 80)

np.random.seed(42)
n = 1_000_000

print(f"\n[1/5] Gerando {n:,} registros base...")
df = pd.DataFrame({
    'id': range(10000000, 10000000 + n),
    'mes': np.random.choice([202201, 202202, 202203, 202204, 202205, 202206], n),
    'score': np.clip(np.random.normal(680, 80, n), 300, 950).round().astype(int),
    'renda': np.random.lognormal(np.log(3500), 0.8, n).round(2)
})

print("[2/5] Adicionando features demográficas...")
df['idade'] = np.clip(np.random.normal(40, 15, n), 18, 80).astype(int)
df['score'] = (df['score'] + (df['idade'] - 40) * 1.5).clip(300, 950).astype(int)
df['tempo_relacionamento'] = np.clip((df['idade'] - 18) * 0.6 + np.random.exponential(3, n), 0, 40).astype(int)
prob_produtos = (df['tempo_relacionamento'] / 40 * 0.5 + df['score'] / 950 * 0.5)
df['qtd_produtos_ativos'] = np.random.binomial(10, prob_produtos).clip(1, 10)

print("[3/5] Adicionando features de produto...")
df['tipo_produto'] = np.random.choice(['CDC', 'Cartão', 'Imobiliário', 'Pessoal'], n, p=[0.35, 0.25, 0.10, 0.30])
df['regiao'] = np.random.choice(['Sudeste', 'Sul', 'Nordeste', 'Centro-Oeste', 'Norte'], n, p=[0.42, 0.15, 0.28, 0.08, 0.07])
df['canal'] = np.random.choice(['App', 'Agência', 'Parceiro', 'Internet Banking'], n, p=[0.40, 0.30, 0.15, 0.15])

prazo_map = {'CDC': 36, 'Cartão': 6, 'Imobiliário': 240, 'Pessoal': 24}
df['prazo'] = df['tipo_produto'].map(prazo_map) + np.random.randint(-6, 7, n)
df['prazo'] = df['prazo'].clip(1, 420)

taxa_map = {'CDC': 2.5, 'Cartão': 8.0, 'Imobiliário': 0.8, 'Pessoal': 2.8}
df['taxa'] = df['tipo_produto'].map(taxa_map) + np.random.normal(0, 0.3, n)
df['taxa'] = df['taxa'].clip(0.5, 15.0).round(2)

print("[4/5] Calculando valores financeiros...")
df['valor_renda_ratio'] = np.random.uniform(0.3, 1.5, n)
ajuste_prod = df['tipo_produto'].map({'CDC': 0.5, 'Cartão': 0.2, 'Imobiliário': 3.0, 'Pessoal': 0.5})
df['ticket'] = (df['renda'] * df['prazo'] * df['valor_renda_ratio'] * ajuste_prod).clip(1000, 500000).round(2)

print("[5/5] Calculando inadimplência e risco...")
fator_score = (950 - df['score']) / 650 * 0.5
fator_renda = np.where(df['renda'] < 2000, 0.3, 0)
fator_vr = np.where(df['valor_renda_ratio'] > 1.0, 0.2, 0)
fator_prod = df['tipo_produto'].map({'CDC': 0.75, 'Cartão': 1.25, 'Imobiliário': 0.21, 'Pessoal': 0.80})
prob_inad = (0.068 * (1 + fator_score + fator_renda + fator_vr) * fator_prod).clip(0.01, 0.95)
df['inadimplente'] = np.random.binomial(1, prob_inad)
df['dias_atraso'] = np.where(df['inadimplente'] == 1, np.random.randint(91, 360, n), 0)

lgd_map = {'CDC': 0.55, 'Cartão': 0.70, 'Imobiliário': 0.35, 'Pessoal': 0.60}
df['lgd'] = df['tipo_produto'].map(lgd_map) + np.random.normal(0, 0.05, n)
df['lgd'] = df['lgd'].clip(0.2, 0.9).round(3)
df['perda_esperada'] = df['ticket'] * df['inadimplente'] * df['lgd']

df['provisao_stage'] = 'Stage 1'
df.loc[(df['score'] < 600) | ((df['dias_atraso'] > 0) & (df['dias_atraso'] <= 90)), 'provisao_stage'] = 'Stage 2'
df.loc[df['dias_atraso'] > 90, 'provisao_stage'] = 'Stage 3'

print("\nSalvando dataset...")
output_dir = Path('data/processed')
output_dir.mkdir(parents=True, exist_ok=True)
output = output_dir / 'dataset_demo_1m.parquet'
df.to_parquet(output, index=False)

print("\n" + "=" * 80)
print("[OK] DATASET CRIADO COM SUCESSO!")
print("=" * 80)
print(f"\nArquivo: {output}")
print(f"Tamanho: {output.stat().st_size / 1024 / 1024:.1f} MB")
print(f"Registros: {len(df):,}")
print(f"Colunas: {len(df.columns)}")
print(f"\nMétricas:")
print(f"  Taxa Inadimplência: {df['inadimplente'].mean() * 100:.2f}%")
print(f"  Valor Total: R$ {df['ticket'].sum() / 1e9:.2f} bilhões")
print(f"  Perda Esperada: R$ {df['perda_esperada'].sum() / 1e9:.2f} bilhões")
