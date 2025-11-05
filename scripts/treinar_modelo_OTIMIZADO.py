#!/usr/bin/env python3
"""
Treinamento Otimizado do Modelo LightGBM com Optuna
Meta: AUC-ROC >= 0.95
"""

import pandas as pd
import numpy as np
import joblib
import optuna
from pathlib import Path
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
from lightgbm import LGBMClassifier
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("TREINAMENTO OTIMIZADO - LIGHTGBM COM OPTUNA")
print("Meta: AUC-ROC >= 0.95")
print("=" * 80)

# Determinar caminhos base
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"
API_DIR = BASE_DIR / "api"

# Carregar dataset
print("\n[1/8] Carregando dataset...")
dataset_files = list(DATA_DIR.glob("*.parquet"))
if not dataset_files:
    raise FileNotFoundError(f"Nenhum arquivo .parquet encontrado em {DATA_DIR}")

# Usar o maior dataset disponível
dataset_file = max(dataset_files, key=lambda x: x.stat().st_size)
print(f"   Usando: {dataset_file.name}")
df_full = pd.read_parquet(dataset_file, engine='pyarrow')
print(f"   [OK] {len(df_full):,} registros carregados")

# Usar amostra estratificada para otimização rápida
target_col_temp = None
for col in ['inadimplente', 'TARGET', 'default', 'bad']:
    if col in df_full.columns:
        target_col_temp = col
        break

if len(df_full) > 500000:
    print(f"   Usando amostra estratificada de 500K para otimização...")
    df = df_full.groupby(target_col_temp, group_keys=False).apply(
        lambda x: x.sample(min(len(x), 250000), random_state=42)
    ).sample(frac=1, random_state=42).reset_index(drop=True)
    print(f"   [OK] Amostra: {len(df):,} registros")
else:
    df = df_full

# Identificar coluna target
target_cols = ['inadimplente', 'TARGET', 'default', 'bad']
target_col = None
for col in target_cols:
    if col in df.columns:
        target_col = col
        break

if target_col is None:
    raise ValueError(f"Coluna target não encontrada. Colunas disponíveis: {df.columns.tolist()}")

print(f"   Target: {target_col} | Taxa: {df[target_col].mean() * 100:.2f}%")

# Preparar features
print("\n[2/8] Preparando features...")

# Features numéricas
numeric_features = []
for col in ['score', 'renda', 'idade', 'tempo_relacionamento', 'tempo_cliente_meses',
            'qtd_produtos_ativos', 'qtd_produtos', 'prazo', 'prazo_meses', 'taxa', 
            'taxa_juros_aa', 'ticket', 'valor', 'parcela_mensal', 
            'perc_comprometimento_renda', 'valor_renda_ratio', 'qtd_atrasos_12m']:
    if col in df.columns:
        numeric_features.append(col)

# Features categóricas
categorical_features = []
for col in ['tipo_produto', 'tipo_credito', 'regiao', 'canal', 'genero', 
            'estado_civil', 'escolaridade', 'uf', 'porte_municipio', 'faixa_etaria']:
    if col in df.columns:
        categorical_features.append(col)

# Criar faixa etaria se não existir
if 'faixa_etaria' not in df.columns and 'idade' in df.columns:
    df['faixa_etaria'] = pd.cut(df['idade'], 
                                 bins=[0, 25, 35, 45, 55, 65, 100],
                                 labels=['18-25', '26-35', '36-45', '46-55', '56-65', '66+'])
    categorical_features.append('faixa_etaria')

# Criar features derivadas
if 'score' in df.columns and 'score_alto' not in df.columns:
    df['score_alto'] = (df['score'] > 700).astype(int)
    numeric_features.append('score_alto')

if 'renda' in df.columns and 'ticket' in df.columns and 'renda_ticket_ratio' not in df.columns:
    df['renda_ticket_ratio'] = (df['ticket'] / df['renda']).clip(0, 10)
    numeric_features.append('renda_ticket_ratio')

# Encodar categóricas
label_encoders = {}
for col in categorical_features:
    le = LabelEncoder()
    df[f'{col}_encoded'] = le.fit_transform(df[col].astype(str))
    label_encoders[col] = le

# Montar feature set
feature_cols = numeric_features + [f'{col}_encoded' for col in categorical_features]
feature_cols = [col for col in feature_cols if col in df.columns]

print(f"   [OK] {len(feature_cols)} features preparadas")
print(f"      Numericas: {len(numeric_features)}")
print(f"      Categoricas: {len(categorical_features)}")

# Preparar dados
X = df[feature_cols].fillna(0)
y = df[target_col]

# Split estratificado
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\n[3/8] Split de dados:")
print(f"   Treino: {len(X_train):,} ({y_train.mean()*100:.2f}% inadimplencia)")
print(f"   Teste:  {len(X_test):,} ({y_test.mean()*100:.2f}% inadimplencia)")

# Função objetivo para Optuna
def objective(trial):
    """Função objetivo para otimização de hiperparametros"""
    params = {
        'objective': 'binary',
        'metric': 'auc',
        'boosting_type': 'gbdt',
        'verbosity': -1,
        'random_state': 42,
        'n_estimators': trial.suggest_int('n_estimators', 100, 500),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'num_leaves': trial.suggest_int('num_leaves', 20, 150),
        'max_depth': trial.suggest_int('max_depth', 3, 15),
        'min_child_samples': trial.suggest_int('min_child_samples', 10, 100),
        'subsample': trial.suggest_float('subsample', 0.5, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
        'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 10.0, log=True),
        'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 10.0, log=True),
        'scale_pos_weight': len(y_train[y_train == 0]) / len(y_train[y_train == 1])
    }
    
    # Cross-validation
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    auc_scores = []
    
    for train_idx, val_idx in cv.split(X_train, y_train):
        X_cv_train, X_cv_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
        y_cv_train, y_cv_val = y_train.iloc[train_idx], y_train.iloc[val_idx]
        
        model = LGBMClassifier(**params)
        model.fit(X_cv_train, y_cv_train, eval_set=[(X_cv_val, y_cv_val)])
        
        y_pred_proba = model.predict_proba(X_cv_val)[:, 1]
        auc = roc_auc_score(y_cv_val, y_pred_proba)
        auc_scores.append(auc)
    
    return np.mean(auc_scores)

# Otimização com Optuna
print("\n[4/8] Otimizando hiperparametros com Optuna...")
print("   Isso pode levar alguns minutos...")

study = optuna.create_study(direction='maximize', study_name='lightgbm_optimization')
study.optimize(objective, n_trials=20, show_progress_bar=True, n_jobs=1)

print(f"\n   [OK] Otimização concluída!")
print(f"   Melhor AUC (CV): {study.best_value:.4f}")
print(f"   Melhores parâmetros:")
for key, value in study.best_params.items():
    print(f"      {key}: {value}")

# Treinar modelo final com melhores parâmetros
print("\n[5/8] Treinando modelo final...")
best_params = study.best_params.copy()
best_params.update({
    'objective': 'binary',
    'metric': 'auc',
    'boosting_type': 'gbdt',
    'verbosity': -1,
    'random_state': 42,
    'scale_pos_weight': len(y_train[y_train == 0]) / len(y_train[y_train == 1])
})

model = LGBMClassifier(**best_params)
model.fit(X_train, y_train, eval_set=[(X_test, y_test)])

# Avaliar modelo
print("\n[6/8] Avaliando modelo...")
y_pred_proba = model.predict_proba(X_test)[:, 1]
y_pred = model.predict(X_test)

auc_score = roc_auc_score(y_test, y_pred_proba)
cm = confusion_matrix(y_test, y_pred)

print(f"\n   [META] AUC-ROC: {auc_score:.4f}")
print(f"\n   Matriz de Confusão:")
print(f"      TN: {cm[0,0]:,} | FP: {cm[0,1]:,}")
print(f"      FN: {cm[1,0]:,} | TP: {cm[1,1]:,}")

if auc_score >= 0.95:
    print(f"\n   [OK] META ATINGIDA! AUC >= 0.95")
else:
    print(f"\n   [AVISO]  AUC abaixo da meta (0.95). Considere mais trials ou feature engineering.")

# Feature importance
print("\n[7/8] Feature Importance (Top 15):")
feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False).head(15)

for idx, row in feature_importance.iterrows():
    print(f"   {row['feature']:30s}: {row['importance']:,.0f}")

# Salvar modelo e artefatos
print("\n[8/8] Salvando modelo e artefatos...")
API_DIR.mkdir(parents=True, exist_ok=True)

# Salvar modelo
joblib.dump(model, API_DIR / 'modelo_lgbm.pkl')
print(f"   [OK] Modelo: {API_DIR / 'modelo_lgbm.pkl'}")

# Salvar encoders
joblib.dump(label_encoders, API_DIR / 'label_encoders.pkl')
print(f"   [OK] Encoders: {API_DIR / 'label_encoders.pkl'}")

# Salvar feature cols
joblib.dump(feature_cols, API_DIR / 'feature_cols.pkl')
print(f"   [OK] Features: {API_DIR / 'feature_cols.pkl'}")

# Salvar métricas
metricas = {
    'model_type': 'LGBMClassifier',
    'version': '2.0.0-optimized',
    'train_date': datetime.now().isoformat(),
    'n_features': len(feature_cols),
    'feature_names': feature_cols,
    'auc_roc': float(auc_score),
    'confusion_matrix': cm.tolist(),
    'feature_importance': feature_importance.to_dict('records'),
    'best_params': best_params,
    'optuna_trials': len(study.trials),
    'optuna_best_value': float(study.best_value)
}

joblib.dump(metricas, API_DIR / 'metricas_modelo.pkl')
print(f"   [OK] Métricas: {API_DIR / 'metricas_modelo.pkl'}")

print("\n" + "=" * 80)
print("[OK] TREINAMENTO CONCLUÍDO COM SUCESSO!")
print("=" * 80)
print(f"[META] AUC-ROC Final: {auc_score:.4f}")
print(f"[INFO] Features: {len(feature_cols)}")
print(f" Optuna Trials: {len(study.trials)}")
print(f" Artefatos salvos em: {API_DIR}")
print("=" * 80)
