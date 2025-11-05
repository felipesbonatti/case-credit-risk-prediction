import argparse
import logging
import numpy as np
import pandas as pd

def gerar_base_sintetica(n, seed):
    np.random.seed(seed)
    # IDs e Temporalidade
    ids = np.arange(10_000_000, 10_000_000 + n)
    meses = np.random.choice(
        ["202201", "202202", "202203", "202204", "202205", "202206",
         "202207", "202208", "202209", "202210", "202211", "202212"], n)
    score = np.clip(np.random.normal(650, 80, n), 300, 950)
    renda = np.clip(np.random.normal(10500, 3500, n), 800, 150000)
    inadimplente = np.random.binomial(1, 0.0639, n)
    ticket = np.clip(np.random.normal(60224, 22000, n), 1000, 500000)
    # Outliers e missing
    mask_outlier = np.random.rand(n) < 0.02
    renda[mask_outlier] *= 4
    mask_missing = np.random.rand(n) < 0.05
    score[mask_missing] = np.nan
    df = pd.DataFrame({
        "id": ids,
        "mes": meses,
        "score": score,
        "renda": renda,
        "inadimplente": inadimplente,
        "ticket": ticket
    })
    return df

def main():
    parser = argparse.ArgumentParser(description="Gerador de base sintética executiva")
    parser.add_argument('--n', type=int, default=5_000_000, help='Número de registros')
    parser.add_argument('--seed', type=int, default=42, help='Seed para aleatoriedade')
    parser.add_argument('--output', type=str, default='data/processed/dataset_modelo_sintetico_v3.parquet', help='Caminho de saída')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    df = gerar_base_sintetica(args.n, args.seed)
    df.to_parquet(args.output, compression='snappy')
    logging.info(f"Base gerada: {args.n} registros em {args.output}")
    logging.info(f"Score: {df['score'].describe()}")
    logging.info(f"Inadimplência: {df['inadimplente'].mean():.2%}")
    logging.info(f"Renda: {df['renda'].mean():.2f}")
    logging.info(f"Ticket: {df['ticket'].mean():.2f}")
    # Relatório rápido em txt
    with open(args.output.replace('.parquet', '_stats.txt'), 'w') as f:
        f.write(df.describe(include='all').to_string())
        f.write(f"\nTaxa de inadimplência: {df['inadimplente'].mean():.2%}\n")
        f.write(f"Registros nulos (score): {(df['score'].isna().sum())} / {args.n}\n")
    print("Base sintética 100% pronta para demo executiva.")

if __name__ == "__main__":
    main()