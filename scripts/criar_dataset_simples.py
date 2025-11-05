import pandas as pd
import numpy as np
from pathlib import Path

print("Criando dataset demo do zero...")

np.random.seed(42)
n = 1_000_000

# Criar dataset base
df = pd.DataFrame({
    'id': range(10000000, 10000000 + n),
    'mes': np.random.choice([202201, 202202, 202203, 202204, 202205, 202206], n),
    'score': np.clip(np.random.normal(680, 80, n), 300, 950).round().astype(int),
    'renda': np.random.lognormal(np.log(3500), 0.8, n).round(2)
})

# Enriquecer
df['idade'] = np.clip(np.random.normal(40, 15, n), 18, 80).astype(int)
df['tempo_relacionamento'] = np.clip((df['idade'] - 18) * 0.6 + np.random.exponential(3, n), 0, 40).astype(int)
df['qtd_produtos_ativos'] = np.random.randint(1, 11, n)
df['tipo_produto'] = np.random.choice(['CDC', 'Cartão', 'Imobiliário', 'Pessoal'], n, p=[0.35, 0.25, 0.10, 0.30])
df['regiao'] = np.random.choice(['Sudeste', 'Sul', 'Nordeste', 'Centro-Oeste', 'Norte'], n, p=[0.42, 0.15, 0.28, 0.08, 0.07])
df['canal'] = np.random.choice(['App', 'Agência', 'Parceiro', 'Internet Banking'], n, p=[0.40, 0.30, 0.15, 0.15])

prazo_map = {'CDC': 36, 'Cartão': 6, 'Imobiliário': 240, 'Pessoal': 24}
df['prazo'] = df['tipo_produto'].map(prazo_map)

taxa_map = {'CDC': 2.5, 'Cartão': 8.0, 'Imobiliário': 0.8, 'Pessoal': 2.8}
df['taxa'] = df['tipo_produto'].map(taxa_map)

df['valor_renda_ratio'] = np.random.uniform(0.3, 1.5, n)
ajuste_prod = df['tipo_produto'].map({'CDC': 0.5, 'Cartão': 0.2, 'Imobiliário': 3.0, 'Pessoal': 0.5})
df['ticket'] = (df['renda'] * df['prazo'] * df['valor_renda_ratio'] * ajuste_prod).clip(1000, 500000).round(2)

# Inadimplência
prob_inad = ((950 - df['score']) / 650 * 0.068).clip(0.01, 0.95)
df['inadimplente'] = np.random.binomial(1, prob_inad)
df['dias_atraso'] = np.where(df['inadimplente'] == 1, np.random.randint(91, 360, n), 0)

lgd_map = {'CDC': 0.55, 'Cartão': 0.70, 'Imobiliário': 0.35, 'Pessoal': 0.60}
df['lgd'] = df['tipo_produto'].map(lgd_map)
df['perda_esperada'] = df['ticket'] * df['inadimplente'] * df['lgd']
df['provisao_stage'] = np.where(df['dias_atraso'] > 90, 'Stage 3', np.where(df['score'] < 600, 'Stage 2', 'Stage 1'))

# Salvar
output_dir = Path('data/processed')
output_dir.mkdir(parents=True, exist_ok=True)
output = output_dir / 'dataset_demo_1m.parquet'
df.to_parquet(output, index=False)

print(f"[OK] Dataset criado: {output}")
print(f"   Registros: {len(df):,}")
print(f"   Colunas: {len(df.columns)}")
print(f"   Taxa Inadimplência: {df['inadimplente'].mean() * 100:.2f}%")
