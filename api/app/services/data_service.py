"""
Data Service - Carrega e processa base de 1 milhão de clientes
OTIMIZADO para performance máxima
"""

import pandas as pd
import numpy as np
from pathlib import Path
import structlog
from functools import lru_cache
import hashlib
import json

logger = structlog.get_logger()


class DataService:
    def __init__(self):
        self.df = None
        self.df_preprocessed = None  # DataFrame pré-processado
        self._metrics_cache = {}  # Cache de métricas
        self._cache_ttl = 300  # 5 minutos
        self.load_data()

    def load_data(self):
        """Carrega a base de dados do arquivo parquet"""
        try:
            # Caminho relativo ao projeto
            base_path = Path(__file__).parent.parent.parent.parent / "data" / "processed"
            file_path = base_path / "dataset_realista_1m.parquet"

            if not file_path.exists():
                logger.error(f" Arquivo não encontrado: {file_path}")
                return

            # Carregar apenas colunas necessárias
            self.df = pd.read_parquet(
                file_path, 
                engine='pyarrow',
                columns=['score', 'inadimplente', 'ticket']  # Apenas o necessário
            )
            
            # Pré-processar dados uma única vez
            self._preprocess_data()
            
            logger.info(f" Base de dados carregada e otimizada: {len(self.df):,} registros")

        except Exception as e:
            logger.error(f" Erro ao carregar base de dados: {str(e)}")
            self.df = None

    def _preprocess_data(self):
        """Pré-processa dados que não mudam"""
        if self.df is None:
            return
        
        # Criar DataFrame pré-processado (evita cópias futuras)
        self.df_preprocessed = self.df.copy()
        
        # Normalizar score uma única vez (não precisa recalcular)
        self.df_preprocessed["score_normalizado"] = (
            (self.df_preprocessed["score"] - 300) / (950 - 300)
        )
        
        # Pré-calcular valores que não dependem do threshold
        self.total_clientes = len(self.df_preprocessed)
        self.valor_medio = float(self.df_preprocessed["ticket"].mean())
        
        logger.info(" Dados pré-processados com sucesso")

    def _get_cache_key(self, method: str, **kwargs) -> str:
        """Gera chave de cache baseada no método e parâmetros"""
        params_str = json.dumps(kwargs, sort_keys=True)
        return hashlib.md5(f"{method}:{params_str}".encode()).hexdigest()

    def _get_from_cache(self, key: str):
        """Obtém valor do cache se válido"""
        if key in self._metrics_cache:
            cached_data, timestamp = self._metrics_cache[key]
            import time
            if time.time() - timestamp < self._cache_ttl:
                logger.info(f"Cache hit para {key[:8]}...")
                return cached_data
        return None

    def _save_to_cache(self, key: str, data):
        """Salva valor no cache"""
        import time
        self._metrics_cache[key] = (data, time.time())

    def get_metrics(self, threshold: float = 0.5):
        """
        Calcula métricas baseadas no threshold (OTIMIZADO)

        Args:
            threshold: Limite de score normalizado para aprovação (0-1)
        """
        # Verificar cache
        cache_key = self._get_cache_key('metrics', threshold=round(threshold, 2))
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        if self.df_preprocessed is None or len(self.df_preprocessed) == 0:
            return self._get_empty_metrics()

        # Usar DataFrame pré-processado (sem cópia!)
        df = self.df_preprocessed
        
        # Aplicar threshold (operação vetorizada rápida)
        aprovado_mask = df["score_normalizado"] >= threshold
        
        # Calcular métricas usando máscaras (muito mais rápido)
        clientes_aprovados = int(aprovado_mask.sum())
        clientes_rejeitados = self.total_clientes - clientes_aprovados
        taxa_aprovacao = (clientes_aprovados / self.total_clientes * 100) if self.total_clientes > 0 else 0

        # Inadimplência entre aprovados (usando máscaras)
        if clientes_aprovados > 0:
            inadimplentes_aprovados = df.loc[aprovado_mask, "inadimplente"].sum()
            taxa_inadimplencia = inadimplentes_aprovados / clientes_aprovados * 100
        else:
            taxa_inadimplencia = 0

        # Cálculos financeiros (operações vetorizadas)
        receita_aprovados = float(df.loc[aprovado_mask, "ticket"].sum()) if clientes_aprovados > 0 else 0
        
        # Perdas com inadimplentes aprovados
        inadimplentes_aprovados_mask = aprovado_mask & (df["inadimplente"] == 1)
        perdas_inadimplentes = float(df.loc[inadimplentes_aprovados_mask, "ticket"].sum())
        
        saldo_liquido = receita_aprovados - perdas_inadimplentes

        # Oportunidades perdidas (bons clientes rejeitados)
        rejeitados_bons_mask = ~aprovado_mask & (df["inadimplente"] == 0)
        oportunidades_perdidas = float(df.loc[rejeitados_bons_mask, "ticket"].sum())

        # Perdas evitadas (maus clientes rejeitados)
        rejeitados_maus_mask = ~aprovado_mask & (df["inadimplente"] == 1)
        perdas_evitadas = float(df.loc[rejeitados_maus_mask, "ticket"].sum())

        result = {
            "saldoLiquido": float(saldo_liquido),
            "taxaAprovacao": round(taxa_aprovacao, 1),
            "taxaInadimplencia": round(taxa_inadimplencia, 1),
            "totalClientes": int(self.total_clientes),
            "clientesAprovados": int(clientes_aprovados),
            "clientesRejeitados": int(clientes_rejeitados),
            "receitaTotal": float(receita_aprovados),
            "perdasInadimplencia": float(perdas_inadimplentes),
            "oportunidadesPerdidas": float(oportunidades_perdidas),
            "perdasEvitadas": float(perdas_evitadas),
            "valorMedio": float(self.valor_medio),
            "threshold": threshold,
        }

        # Salvar no cache
        self._save_to_cache(cache_key, result)
        
        return result

    def _get_empty_metrics(self):
        """Retorna métricas vazias quando não há dados"""
        return {
            "saldoLiquido": 0,
            "taxaAprovacao": 0,
            "taxaInadimplencia": 0,
            "totalClientes": 0,
            "clientesAprovados": 0,
            "clientesRejeitados": 0,
            "receitaTotal": 0,
            "perdasInadimplencia": 0,
            "oportunidadesPerdidas": 0,
            "perdasEvitadas": 0,
            "valorMedio": 0,
            "threshold": 0.5,
        }

    @lru_cache(maxsize=1)
    def get_distribution_data(self):
        """Retorna dados de distribuição para gráficos (com cache)"""
        if self.df is None:
            return {}

        return {"score_distribution": self.df["score"].value_counts().to_dict()}

    @lru_cache(maxsize=1)
    def get_roc_curve_data(self):
        """
        Gera dados para curva ROC CORRIGIDA (OTIMIZADO)
        """
        # Verificar cache
        cache_key = self._get_cache_key('roc_curve')
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        if self.df_preprocessed is None:
            return {"fpr": [], "tpr": [], "thresholds": [], "auc": 0}

        df = self.df_preprocessed
        
        # Gerar thresholds de 0 a 1 (reduzir para 50 pontos para performance)
        thresholds = np.linspace(0, 1, 50)
        fpr_list = []
        tpr_list = []

        # Pré-calcular máscaras de inadimplentes
        inadimplente_mask = df["inadimplente"] == 1
        adimplente_mask = df["inadimplente"] == 0
        
        total_inadimplentes = inadimplente_mask.sum()
        total_adimplentes = adimplente_mask.sum()

        for threshold in thresholds:
            # Máscaras de aprovação/rejeição
            rejeitado_mask = df["score_normalizado"] < threshold

            # TP = Inadimplentes corretamente identificados (rejeitados)
            tp = (rejeitado_mask & inadimplente_mask).sum()
            # FP = Adimplentes incorretamente rejeitados
            fp = (rejeitado_mask & adimplente_mask).sum()

            # True Positive Rate (Sensibilidade/Recall)
            tpr = tp / total_inadimplentes if total_inadimplentes > 0 else 0
            
            # False Positive Rate
            fpr = fp / total_adimplentes if total_adimplentes > 0 else 0

            fpr_list.append(float(fpr))
            tpr_list.append(float(tpr))

        # Calcular AUC usando integração trapezoidal
        sorted_indices = np.argsort(fpr_list)
        fpr_sorted = [fpr_list[i] for i in sorted_indices]
        tpr_sorted = [tpr_list[i] for i in sorted_indices]
        
        auc = np.trapz(tpr_sorted, fpr_sorted)

        result = {
            "fpr": fpr_list,
            "tpr": tpr_list,
            "thresholds": thresholds.tolist(),
            "auc": abs(float(auc))
        }

        # Salvar no cache
        self._save_to_cache(cache_key, result)

        return result

    def get_confusion_matrix(self, threshold: float = 0.5):
        """
        Retorna matriz de confusão CORRIGIDA para um threshold específico (OTIMIZADO)
        """
        # Verificar cache
        cache_key = self._get_cache_key('confusion_matrix', threshold=round(threshold, 2))
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        if self.df_preprocessed is None:
            return {"tp": 0, "fp": 0, "tn": 0, "fn": 0}

        df = self.df_preprocessed
        
        # Máscaras (operações vetorizadas)
        aprovado_mask = df["score_normalizado"] >= threshold
        rejeitado_mask = ~aprovado_mask
        inadimplente_mask = df["inadimplente"] == 1
        adimplente_mask = df["inadimplente"] == 0

        # Calcular matriz de confusão usando máscaras (muito mais rápido)
        tp = int((rejeitado_mask & inadimplente_mask).sum())
        fp = int((rejeitado_mask & adimplente_mask).sum())
        tn = int((aprovado_mask & adimplente_mask).sum())
        fn = int((aprovado_mask & inadimplente_mask).sum())

        # Calcular métricas
        total = tp + fp + tn + fn
        accuracy = (tp + tn) / total if total > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        result = {
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn,
            "accuracy": round(accuracy * 100, 2),
            "precision": round(precision * 100, 2),
            "recall": round(recall * 100, 2),
            "f1_score": round(f1_score * 100, 2),
            "threshold": threshold,
        }

        # Salvar no cache
        self._save_to_cache(cache_key, result)

        return result

    def get_threshold_sensitivity(self):
        """Retorna análise de sensibilidade do threshold (OTIMIZADO)"""
        # Verificar cache
        cache_key = self._get_cache_key('threshold_sensitivity')
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        if self.df_preprocessed is None:
            return {"thresholds": [], "metrics": []}

        # Reduzir pontos de 17 para 9 (mais rápido)
        thresholds = np.linspace(0.1, 0.9, 9)
        results = []

        for threshold in thresholds:
            metrics = self.get_metrics(threshold=float(threshold))
            results.append(
                {
                    "threshold": round(float(threshold), 2),
                    "taxaAprovacao": metrics["taxaAprovacao"],
                    "taxaInadimplencia": metrics["taxaInadimplencia"],
                    "saldoLiquido": metrics["saldoLiquido"],
                    "perdasEvitadas": metrics["perdasEvitadas"],
                    "oportunidadesPerdidas": metrics["oportunidadesPerdidas"],
                }
            )

        result = {"data": results}

        # Salvar no cache
        self._save_to_cache(cache_key, result)

        return result

    def optimize_threshold(self, objective: str = "profit"):
        """Otimiza o threshold baseado em diferentes objetivos (OTIMIZADO)"""
        if self.df_preprocessed is None:
            return {"optimal_threshold": 0.5, "objective": objective}

        # Reduzir pontos de 17 para 9
        thresholds = np.linspace(0.1, 0.9, 9)
        best_threshold = 0.5
        best_value = float("-inf")

        results = []

        for threshold in thresholds:
            metrics = self.get_metrics(threshold=float(threshold))

            if objective == "profit":
                value = metrics["saldoLiquido"]
            elif objective == "risk":
                value = -metrics["taxaInadimplencia"]
            elif objective == "balanced":
                value = metrics["taxaAprovacao"] - (metrics["taxaInadimplencia"] * 10)
            else:
                value = metrics["saldoLiquido"]

            results.append({"threshold": round(float(threshold), 2), "value": float(value), "metrics": metrics})

            if value > best_value:
                best_value = value
                best_threshold = float(threshold)

        best_metrics = self.get_metrics(threshold=best_threshold)

        return {
            "optimal_threshold": round(best_threshold, 2),
            "objective": objective,
            "best_value": float(best_value),
            "metrics": best_metrics,
            "all_results": results,
        }

    def clear_cache(self):
        """Limpa o cache de métricas"""
        self._metrics_cache.clear()
        logger.info("Cache de métricas limpo")


# Instância global do serviço
data_service = DataService()
