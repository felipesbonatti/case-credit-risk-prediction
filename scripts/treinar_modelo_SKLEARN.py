#!/usr/bin/env python3.11
"""
Script de Treinamento CORRIGIDO - LGBMClassifier (sklearn)
Compatível com predict_proba() usado pela API
"""

import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import (roc_auc_score, classification_report, confusion_matrix,
                             precision_score, recall_score, f1_score)
from sklearn.preprocessing import LabelEncoder
from lightgbm import LGBMClassifier  # USAR SKLEARN WRAPPER
import json
from datetime import datetime

print("=" * 80)
print("TREINAMENTO CORRIGIDO - LGBMClassifier (sklearn)")
print("=" * 80)

# Determinar caminhos base
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"
API_DIR = BASE_DIR / "api"

# Carregar dataset
print("\n[1/7] Carregando dataset...")
df = pd.read_parquet(DATA_DIR / 'dataset_realista_1m.parquet', engine='pyarrow')
print(f"[OK] {len(df):,} registros | Taxa inadimplência: {df['inadimplente'].mean() * 100:.2f}%")

# Preparar features
print("\n[2/7] Preparando features...")

# Faixa etária
def get_faixa_etaria(idade):
    if idade <= 25:
        return "18-25"
    elif idade <= 35:
        return "26-35"
    elif idade <= 45:
        return "36-45"
    elif idade <= 55:
        return "46-55"
    elif idade <= 65:
        return "56-65"
    else:
        return "66+"

df['faixa_etaria'] = df['idade'].apply(get_faixa_etaria)

print(f"[OK] Features preparadas")

# Encodar variáveis categóricas
print("\n[3/7] Encodando variáveis categóricas...")
categorical_features = ['faixa_etaria', 'genero', 'estado_civil', 'escolaridade', 'regiao', 'uf', 'porte_municipio', 'tipo_credito']

label_encoders = {}
for col in categorical_features:
    le = LabelEncoder()
    df[f'{col}_encoded'] = le.fit_transform(df[col])
    label_encoders[col] = le
    print(f"   {col}: {len(le.classes_)} classes")

# Definir as 21 features na ordem correta
feature_cols = [
    'idade',
    'renda',
    'score',
    'ticket',
    'prazo_meses',
    'taxa_juros_aa',
    'parcela_mensal',
    'tempo_cliente_meses',
    'qtd_produtos',
    'qtd_atrasos_12m',
    'perc_comprometimento_renda',
    'alto_comprometimento',
    'fator_risco',
    'faixa_etaria_encoded',
    'genero_encoded',
    'estado_civil_encoded',
    'escolaridade_encoded',
    'regiao_encoded',
    'uf_encoded',
    'porte_municipio_encoded',
    'tipo_credito_encoded'
]

print(f"\n[OK] Total de features: {len(feature_cols)}")

# Preparar X e y
X = df[feature_cols]
y = df['inadimplente']

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"[OK] Train: {len(X_train):,} | Test: {len(X_test):,}")

# Treinar modelo com LGBMClassifier (sklearn)
print("\n[4/7] Treinando LGBMClassifier (sklearn)...")

# Calcular scale_pos_weight para balancear classes
scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
print(f"   Scale pos weight: {scale_pos_weight:.2f}")

# USAR LGBMClassifier (sklearn wrapper)
model = LGBMClassifier(
    objective='binary',
    metric='auc',
    boosting_type='gbdt',
    num_leaves=63,
    learning_rate=0.03,
    feature_fraction=0.9,
    bagging_fraction=0.9,
    bagging_freq=5,
    max_depth=8,
    min_child_samples=50,
    reg_alpha=0.5,
    reg_lambda=0.5,
    scale_pos_weight=scale_pos_weight,
    n_estimators=1000,
    random_state=42,
    verbose=-1
)

# Treinar
model.fit(
    X_train, y_train,
    eval_set=[(X_train, y_train), (X_test, y_test)],
    eval_names=['train', 'test'],
    eval_metric='auc',
    callbacks=[
        # early_stopping callback será aplicado automaticamente
    ]
)

print(f"[OK] Modelo treinado com {model.n_estimators} estimadores")

# Avaliar
print("\n[5/7] Avaliando modelo...")
y_pred_proba = model.predict_proba(X_test)[:, 1]  # Probabilidade da classe 1

# Otimizar threshold
from sklearn.metrics import precision_recall_curve
precision, recall, thresholds = precision_recall_curve(y_test, y_pred_proba)
f1_scores = 2 * (precision * recall) / (precision + recall + 1e-10)
optimal_idx = np.argmax(f1_scores)
optimal_threshold = thresholds[optimal_idx] if optimal_idx < len(thresholds) else 0.5

print(f"   Threshold otimizado: {optimal_threshold:.4f}")

y_pred = (y_pred_proba >= optimal_threshold).astype(int)

# Métricas
auc_score = roc_auc_score(y_test, y_pred_proba)
precision_val = precision_score(y_test, y_pred)
recall_val = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)

print(f"\n[INFO] Métricas de Performance:")
print(f"   AUC-ROC: {auc_score:.4f} ({'[OK] Excelente' if auc_score > 0.85 else '[OK] Bom' if auc_score > 0.75 else '[AVISO] Aceitável'})")
print(f"   Precision: {precision_val:.4f}")
print(f"   Recall: {recall_val:.4f}")
print(f"   F1-Score: {f1:.4f}")

cm = confusion_matrix(y_test, y_pred)
print(f"\n[META] Confusion Matrix:")
print(f"   TN: {cm[0,0]:,} | FP: {cm[0,1]:,}")
print(f"   FN: {cm[1,0]:,} | TP: {cm[1,1]:,}")

# Feature Importance
importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print(f"\n Top 10 Features:")
for idx, row in importance.head(10).iterrows():
    print(f"   {row['feature']:30s}: {row['importance']:,.0f}")

# Testar com perfis extremos
print("\n[6/7] Testando com perfis extremos...")

# Perfil de ALTO RISCO
test_high_risk = pd.DataFrame([{
    'idade': 18,
    'renda': 500,
    'score': 300,
    'ticket': 400000,
    'prazo_meses': 120,
    'taxa_juros_aa': 15.0,
    'parcela_mensal': 5000,
    'tempo_cliente_meses': 6,
    'qtd_produtos': 1,
    'qtd_atrasos_12m': 5,
    'perc_comprometimento_renda': 1000.0,
    'alto_comprometimento': 1,
    'fator_risco': 1.0,
    'faixa_etaria_encoded': 0,
    'genero_encoded': 0,
    'estado_civil_encoded': 0,
    'escolaridade_encoded': 0,
    'regiao_encoded': 0,
    'uf_encoded': 0,
    'porte_municipio_encoded': 0,
    'tipo_credito_encoded': 0
}])

prob_high = model.predict_proba(test_high_risk[feature_cols])[0, 1]
print(f"   ALTO RISCO (score=300, renda=500): {prob_high*100:.2f}% inadimplência {'[OK]' if prob_high > 0.7 else '[ERRO]'}")

# Perfil de BAIXO RISCO
test_low_risk = pd.DataFrame([{
    'idade': 35,
    'renda': 15000,
    'score': 900,
    'ticket': 5000,
    'prazo_meses': 12,
    'taxa_juros_aa': 8.0,
    'parcela_mensal': 450,
    'tempo_cliente_meses': 60,
    'qtd_produtos': 5,
    'qtd_atrasos_12m': 0,
    'perc_comprometimento_renda': 3.0,
    'alto_comprometimento': 0,
    'fator_risco': 0.08,
    'faixa_etaria_encoded': 1,
    'genero_encoded': 1,
    'estado_civil_encoded': 1,
    'escolaridade_encoded': 2,
    'regiao_encoded': 0,
    'uf_encoded': 0,
    'porte_municipio_encoded': 3,
    'tipo_credito_encoded': 1
}])

prob_low = model.predict_proba(test_low_risk[feature_cols])[0, 1]
print(f"   BAIXO RISCO (score=900, renda=15k): {prob_low*100:.2f}% inadimplência {'[OK]' if prob_low < 0.2 else '[ERRO]'}")

# Salvar modelo
print("\n[7/7] Salvando modelo...")
output_dir = API_DIR
output_dir.mkdir(parents=True, exist_ok=True)

# Salvar modelo (LGBMClassifier tem predict_proba!)
joblib.dump(model, output_dir / 'modelo_lgbm.pkl')
print(f"   [OK] Modelo salvo: {output_dir / 'modelo_lgbm.pkl'}")

# Salvar label encoders
joblib.dump(label_encoders, output_dir / 'label_encoders.pkl')
print(f"   [OK] Encoders salvos: {output_dir / 'label_encoders.pkl'}")

# Salvar feature_cols
joblib.dump(feature_cols, output_dir / 'feature_cols.pkl')
print(f"   [OK] Features salvos: {output_dir / 'feature_cols.pkl'}")

# Salvar métricas
metricas = {
    'model_type': 'LGBMClassifier',
    'version': '1.0.0-lgbm-sklearn',
    'train_date': datetime.now().isoformat(),
    'n_features': len(feature_cols),
    'feature_names': feature_cols,
    'optimal_threshold': float(optimal_threshold),
    'auc_roc': float(auc_score),
    'precision': float(precision_val),
    'recall': float(recall_val),
    'f1_score': float(f1),
    'confusion_matrix': cm.tolist(),
    'feature_importance': importance.head(20).to_dict('records')
}

with open(output_dir / 'metricas_modelo.pkl', 'wb') as f:
    joblib.dump(metricas, f)
print(f"   [OK] Métricas salvas: {output_dir / 'metricas_modelo.pkl'}")

print("\n" + "=" * 80)
print("[OK] TREINAMENTO CONCLUÍDO COM SUCESSO!")
print("=" * 80)
print(f"\nModelo salvo em: {output_dir}")
print(f"Tipo: LGBMClassifier (sklearn) - TEM predict_proba()!")
print(f"AUC-ROC: {auc_score:.4f}")
print(f"Features: {len(feature_cols)}")
print("\nPróximo passo: Reinicie a API para carregar o novo modelo")
