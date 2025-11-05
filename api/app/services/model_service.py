"""
Model service CORRIGIDO para ML predictions
Integração real com modelo LightGBM treinado
"""

import joblib
import pandas as pd
from typing import Dict, List
from datetime import datetime
from pathlib import Path
import structlog

from app.models.schemas_fixed import PredictRequest, PredictResponse
from app.utils.config import settings

logger = structlog.get_logger()


class ModelService:
    """
    Service CORRIGIDO para operações do modelo ML
    Compatível com modelo LightGBM de 21 features
    """

    def __init__(self):
        self.model = None
        self.label_encoders = None
        self.feature_cols = None
        self.metricas = None
        self.model_version = "1.0.0-lgbm"
        self.threshold = 0.50
        self.model_loaded = False

    async def load_model(self):
        """
        Carrega modelo ML real do disco
        """
        try:
            # Determinar caminho base (API root)
            api_root = Path(__file__).parent.parent.parent

            # Carregar modelo LightGBM
            model_path = api_root / "modelo_lgbm.pkl"
            if not model_path.exists():
                raise FileNotFoundError(f"Modelo não encontrado: {model_path}")

            self.model = joblib.load(model_path)
            logger.info(f"Modelo LightGBM carregado: {model_path}")

            # Carregar label encoders
            encoders_path = api_root / "label_encoders.pkl"
            if encoders_path.exists():
                self.label_encoders = joblib.load(encoders_path)
                logger.info(f"Label encoders carregados: {list(self.label_encoders.keys())}")
            else:
                logger.warning("Label encoders não encontrados, usando mapeamento padrão")
                self._create_default_encoders()

            # Carregar features
            features_path = api_root / "feature_cols.pkl"
            if features_path.exists():
                self.feature_cols = joblib.load(features_path)
                logger.info(f"Features carregadas: {len(self.feature_cols)} features")
            else:
                logger.warning("Features não encontradas, usando ordem padrão")
                self.feature_cols = self._get_default_features()

            # Carregar métricas
            metricas_path = api_root / "metricas_modelo.pkl"
            if metricas_path.exists():
                self.metricas = joblib.load(metricas_path)
                logger.info(f"Métricas carregadas: AUC-ROC={self.metricas.get('auc_roc', 'N/A')}")

            # Validar modelo
            if hasattr(self.model, "n_features_in_"):
                expected_features = self.model.n_features_in_
                if len(self.feature_cols) != expected_features:
                    raise ValueError(
                        f"Incompatibilidade de features: modelo espera {expected_features}, "
                        f"mas temos {len(self.feature_cols)}"
                    )

            self.model_loaded = True
            logger.info(" Modelo carregado com sucesso e validado")

        except Exception as e:
            logger.error(f" Falha ao carregar modelo: {e}", exc_info=True)
            raise

    def _create_default_encoders(self):
        """
        Cria encoders padrão caso não existam
        """
        self.label_encoders = {
            "faixa_etaria": {"18-25": 0, "26-35": 1, "36-45": 2, "46-55": 3, "56-65": 4, "66+": 5},
            "genero": {"Masculino": 0, "Feminino": 1, "Outro": 2},
            "estado_civil": {"Solteiro": 0, "Casado": 1, "Divorciado": 2, "Viúvo": 3},
            "escolaridade": {"Fundamental": 0, "Médio": 1, "Superior": 2, "Pós-Graduação": 3},
            "regiao": {"Sudeste": 0, "Sul": 1, "Nordeste": 2, "Centro-Oeste": 3, "Norte": 4},
            "uf": {
                "SP": 0,
                "RJ": 1,
                "MG": 2,
                "ES": 3,
                "PR": 4,
                "SC": 5,
                "RS": 6,
                "BA": 7,
                "CE": 8,
                "PE": 9,
                "AL": 10,
                "PB": 11,
                "RN": 12,
                "SE": 13,
                "MA": 14,
                "PI": 15,
                "GO": 16,
                "MT": 17,
                "MS": 18,
                "DF": 19,
                "AM": 20,
                "PA": 21,
                "RO": 22,
                "AC": 23,
                "RR": 24,
                "AP": 25,
                "TO": 26,
            },
            "porte_municipio": {"Pequeno": 0, "Médio": 1, "Grande": 2, "Metrópole": 3},
            "tipo_credito": {"CDC": 0, "Imobiliário": 1, "Cartão": 2, "Pessoal": 3},
        }

    def _get_default_features(self) -> List[str]:
        """
        Retorna ordem padrão das features
        """
        return [
            "idade",
            "renda",
            "score",
            "ticket",
            "prazo_meses",
            "taxa_juros_aa",
            "parcela_mensal",
            "tempo_cliente_meses",
            "qtd_produtos",
            "qtd_atrasos_12m",
            "perc_comprometimento_renda",
            "alto_comprometimento",
            "fator_risco",
            "faixa_etaria_encoded",
            "genero_encoded",
            "estado_civil_encoded",
            "escolaridade_encoded",
            "regiao_encoded",
            "uf_encoded",
            "porte_municipio_encoded",
            "tipo_credito_encoded",
        ]

    def _calculate_derived_features(self, request: PredictRequest) -> Dict:
        """
        Calcula features derivadas necessárias para o modelo
        """
        # Parcela mensal (usando Price)
        taxa_mensal = request.taxa_juros_aa / 12 / 100
        if taxa_mensal > 0:
            parcela_mensal = (
                request.ticket
                * (taxa_mensal * (1 + taxa_mensal) ** request.prazo_meses)
                / ((1 + taxa_mensal) ** request.prazo_meses - 1)
            )
        else:
            parcela_mensal = request.ticket / request.prazo_meses

        # Percentual de comprometimento de renda
        perc_comprometimento_renda = (parcela_mensal / request.renda) * 100

        # Alto comprometimento (>30%)
        alto_comprometimento = 1 if perc_comprometimento_renda > 30 else 0

        # Fator de risco (score normalizado invertido)
        fator_risco = (950 - request.score) / 650

        # Faixa etária (ajustada para classes do modelo)
        if request.idade <= 25:
            faixa_etaria = "18-25"
        elif request.idade <= 35:
            faixa_etaria = "26-35"
        elif request.idade <= 45:
            faixa_etaria = "36-45"
        elif request.idade <= 55:
            faixa_etaria = "46-55"
        elif request.idade <= 65:
            faixa_etaria = "56-65"
        else:
            faixa_etaria = "66+"

        return {
            "parcela_mensal": parcela_mensal,
            "perc_comprometimento_renda": perc_comprometimento_renda,
            "alto_comprometimento": alto_comprometimento,
            "fator_risco": fator_risco,
            "faixa_etaria": faixa_etaria,
        }

    def _encode_categorical(self, encoder, value):
        """
        Codifica valor categórico usando LabelEncoder
        """
        try:
            # Se o valor é um Enum, extrair o valor string
            if hasattr(value, "value"):
                value = value.value
            
            # Normalizar acentos para compatibilidade com modelo treinado
            # O modelo foi treinado com valores sem acentos
            if isinstance(value, str):
                value = value.replace("á", "a").replace("ã", "a").replace("â", "a")
                value = value.replace("é", "e").replace("ê", "e")
                value = value.replace("í", "i")
                value = value.replace("ó", "o").replace("õ", "o").replace("ô", "o")
                value = value.replace("ú", "u")
                value = value.replace("Á", "A").replace("Ã", "A").replace("Â", "A")
                value = value.replace("É", "E").replace("Ê", "E")
                value = value.replace("Í", "I")
                value = value.replace("Ó", "O").replace("Õ", "O").replace("Ô", "O")
                value = value.replace("Ú", "U")

            if hasattr(encoder, "transform"):
                # É um sklearn LabelEncoder
                return int(encoder.transform([value])[0])
            else:
                # É um dicionário
                return encoder.get(value, 0)
        except (KeyError, AttributeError, TypeError, ValueError):
            # Valor não encontrado, retorna 0
            return 0

    def _prepare_features(self, request: PredictRequest) -> pd.DataFrame:
        """
        Prepara features no formato exato esperado pelo modelo
        """
        # Calcular features derivadas
        derived = self._calculate_derived_features(request)

        # Encodar variáveis categóricas
        faixa_etaria_encoded = self._encode_categorical(self.label_encoders["faixa_etaria"], derived["faixa_etaria"])
        genero_encoded = self._encode_categorical(self.label_encoders["genero"], request.genero)
        estado_civil_encoded = self._encode_categorical(self.label_encoders["estado_civil"], request.estado_civil)
        escolaridade_encoded = self._encode_categorical(self.label_encoders["escolaridade"], request.escolaridade)
        regiao_encoded = self._encode_categorical(self.label_encoders["regiao"], request.regiao)
        uf_encoded = self._encode_categorical(self.label_encoders["uf"], request.uf)
        porte_municipio_encoded = self._encode_categorical(
            self.label_encoders["porte_municipio"], request.porte_municipio
        )
        tipo_credito_encoded = self._encode_categorical(self.label_encoders["tipo_credito"], request.tipo_credito)

        # Criar dicionário com todas as features
        features_dict = {
            "idade": request.idade,
            "renda": request.renda,
            "score": request.score,
            "ticket": request.ticket,
            "prazo_meses": request.prazo_meses,
            "taxa_juros_aa": request.taxa_juros_aa,
            "parcela_mensal": derived["parcela_mensal"],
            "tempo_cliente_meses": request.tempo_cliente_meses,
            "qtd_produtos": request.qtd_produtos,
            "qtd_atrasos_12m": request.qtd_atrasos_12m,
            "perc_comprometimento_renda": derived["perc_comprometimento_renda"],
            "alto_comprometimento": derived["alto_comprometimento"],
            "fator_risco": derived["fator_risco"],
            "faixa_etaria_encoded": faixa_etaria_encoded,
            "genero_encoded": genero_encoded,
            "estado_civil_encoded": estado_civil_encoded,
            "escolaridade_encoded": escolaridade_encoded,
            "regiao_encoded": regiao_encoded,
            "uf_encoded": uf_encoded,
            "porte_municipio_encoded": porte_municipio_encoded,
            "tipo_credito_encoded": tipo_credito_encoded,
        }

        # Criar DataFrame com ordem correta das features
        df = pd.DataFrame([features_dict])
        df = df[self.feature_cols]  # Garantir ordem correta

        return df

    def _calculate_risk_score(self, probability: float) -> float:
        """
        Calcula score de risco de 0-100
        """
        return probability * 100

    def _get_recommendation(self, probability: float) -> str:
        """
        Recomendação baseada em BACEN 2682/1999 e Santander

        0-10%: Aprovar (Níveis BACEN AA, A, B, C)
        10-30%: Revisar (Nível BACEN D)
        >30%: Negar (Níveis BACEN E, F, G, H)
        """
        if probability <= 0.10:
            return "Aprovar"
        elif probability <= 0.30:
            return "Revisar"
        else:
            return "Negar"

    def _calculate_confidence(self, probability: float) -> float:
        """
        Calcula confiança da predição
        """
        # Confiança maior quando longe dos limites de decisão
        if probability < 0.20:
            confidence = 0.80 + (0.20 - probability)
        elif probability > 0.50:
            confidence = 0.80 + (probability - 0.50)
        else:
            confidence = 0.60 + abs(probability - 0.35) * 0.5

        return min(confidence, 1.0)

    def _get_feature_importance(self) -> Dict[str, float]:
        """
        Retorna importância das features do modelo
        """
        if self.metricas and "feature_importance" in self.metricas:
            importance_list = self.metricas["feature_importance"][:10]  # Top 10
            return {item["feature"]: item["importance"] for item in importance_list}
        return {}

    async def predict(self, request: PredictRequest) -> PredictResponse:
        """
        Faz predição REAL usando modelo LightGBM carregado
        """
        try:
            if not self.model_loaded or self.model is None:
                raise RuntimeError("Modelo não carregado. Execute load_model() primeiro.")

            # Preparar features
            features_df = self._prepare_features(request)

            # Fazer predição REAL
            probability = float(self.model.predict_proba(features_df)[0][1])
            prediction = int(probability >= self.threshold)

            # Calcular métricas
            risk_score = self._calculate_risk_score(probability)
            recommendation = self._get_recommendation(probability)
            confidence = self._calculate_confidence(probability)

            # Explicabilidade (feature importance do modelo)
            explainability = None
            if settings.FEATURE_EXPLAINABILITY:
                explainability = self._get_feature_importance()

            logger.info(
                "Predição realizada",
                cliente_id=request.cliente_id,
                prediction=prediction,
                probability=probability,
                recommendation=recommendation,
            )

            return PredictResponse(
                cliente_id=request.cliente_id,
                prediction=prediction,
                probability=round(probability, 4),
                risk_score=round(risk_score, 2),
                recommendation=recommendation,
                confidence=round(confidence, 4),
                threshold=self.threshold,
                model_version=self.model_version,
                timestamp=datetime.utcnow(),
                explainability=explainability,
            )

        except Exception as e:
            logger.error(f"Predição falhou: {e}", exc_info=True)
            raise

    def get_model_info(self) -> Dict:
        """
        Retorna informações sobre o modelo carregado
        """
        return {
            "loaded": self.model_loaded,
            "type": type(self.model).__name__ if self.model else None,
            "version": self.model_version,
            "features": len(self.feature_cols) if self.feature_cols else 0,
            "feature_names": self.feature_cols if self.feature_cols else [],
            "metrics": self.metricas if self.metricas else {},
            "threshold": self.threshold,
        }
