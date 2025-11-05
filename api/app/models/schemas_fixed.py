"""
Pydantic schemas CORRIGIDOS para compatibilidade com modelo LightGBM
Features alinhadas com modelo_lgbm.pkl (21 features)
Atualizado para Pydantic V2
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class TipoProduto(str, Enum):
    """Tipos de produto"""

    CDC = "CDC"
    IMOBILIARIO = "Imobiliario"  # Sem acento para compatibilidade com modelo
    CARTAO = "Cartao"  # Sem til para compatibilidade com modelo
    PESSOAL = "Pessoal"


class CanalAquisicao(str, Enum):
    """Canais de aquisição"""

    APP = "App"
    AGENCIA = "Agência"
    PARCEIRO = "Parceiro"
    INTERNET_BANKING = "Internet Banking"


class Regiao(str, Enum):
    """Regiões do Brasil"""

    SUDESTE = "Sudeste"
    SUL = "Sul"
    NORDESTE = "Nordeste"
    CENTRO_OESTE = "Centro-Oeste"
    NORTE = "Norte"


class Genero(str, Enum):
    """Gênero"""

    MASCULINO = "Masculino"
    FEMININO = "Feminino"
    OUTRO = "Outro"


class EstadoCivil(str, Enum):
    """Estado civil"""

    SOLTEIRO = "Solteiro"
    CASADO = "Casado"
    DIVORCIADO = "Divorciado"
    VIUVO = "Viúvo"


class Escolaridade(str, Enum):
    """Escolaridade"""

    FUNDAMENTAL = "Fundamental"
    MEDIO = "Médio"
    SUPERIOR = "Superior"
    POS_GRADUACAO = "Pós-Graduação"


class PorteMunicipio(str, Enum):
    """Porte do município"""

    PEQUENO = "Pequeno"
    MEDIO = "Médio"
    GRANDE = "Grande"
    METROPOLE = "Metrópole"


class PredictRequest(BaseModel):
    """
    Request schema CORRIGIDO para credit risk prediction
    Compatível com 21 features do modelo LightGBM
    """

    # Identificação
    cliente_id: Optional[str] = Field(None, description="ID do cliente (opcional)")

    # Features básicas (já existiam)
    idade: int = Field(..., ge=18, le=100, description="Idade do cliente")
    renda: float = Field(..., gt=0, le=1000000, description="Renda mensal em R$", alias="renda_mensal")
    score: int = Field(..., ge=300, le=950, description="Score de crédito (300-950)", alias="score_credito")
    ticket: float = Field(..., gt=0, le=1000000, description="Valor solicitado em R$", alias="valor")
    prazo_meses: int = Field(..., ge=1, le=360, description="Prazo em meses", alias="prazo")
    taxa_juros_aa: float = Field(..., ge=0, le=100, description="Taxa de juros anual (%)", alias="taxa")
    tempo_cliente_meses: int = Field(
        ..., ge=0, le=600, description="Tempo de relacionamento em meses", alias="tempo_relacionamento"
    )
    qtd_produtos: int = Field(
        ..., ge=0, le=10, description="Quantidade de produtos ativos", alias="qtd_produtos_ativos"
    )

    # Features NOVAS (necessárias para o modelo)
    qtd_atrasos_12m: int = Field(0, ge=0, le=100, description="Quantidade de atrasos nos últimos 12 meses")

    # Features demográficas
    genero: Genero = Field(..., description="Gênero do cliente")
    estado_civil: EstadoCivil = Field(..., description="Estado civil")
    escolaridade: Escolaridade = Field(..., description="Escolaridade")

    # Features geográficas
    regiao: Regiao = Field(..., description="Região do cliente")
    uf: str = Field(..., min_length=2, max_length=2, description="UF do cliente (ex: SP, RJ)")
    porte_municipio: PorteMunicipio = Field(..., description="Porte do município")

    # Features de produto
    tipo_credito: TipoProduto = Field(..., description="Tipo de crédito solicitado", alias="tipo_produto")

    # Features opcionais para contexto
    canal_aquisicao: Optional[CanalAquisicao] = Field(None, description="Canal de aquisição")

    @field_validator("score")
    @classmethod
    def validate_score(cls, v):
        if v < 300 or v > 950:
            raise ValueError("Score de crédito deve estar entre 300 e 950")
        return v

    @field_validator("renda")
    @classmethod
    def validate_renda(cls, v):
        if v <= 0:
            raise ValueError("Renda mensal deve ser maior que zero")
        return v

    @field_validator("uf")
    @classmethod
    def validate_uf(cls, v):
        ufs_validas = [
            "AC",
            "AL",
            "AP",
            "AM",
            "BA",
            "CE",
            "DF",
            "ES",
            "GO",
            "MA",
            "MT",
            "MS",
            "MG",
            "PA",
            "PB",
            "PR",
            "PE",
            "PI",
            "RJ",
            "RN",
            "RS",
            "RO",
            "RR",
            "SC",
            "SP",
            "SE",
            "TO",
        ]
        if v.upper() not in ufs_validas:
            raise ValueError(f'UF inválida. Deve ser uma das: {", ".join(ufs_validas)}')
        return v.upper()

    model_config = ConfigDict(
        populate_by_name=True,
        protected_namespaces=(),
        json_schema_extra={
            "example": {
                "cliente_id": "12345678901",
                "idade": 35,
                "renda_mensal": 5000.00,
                "score_credito": 650,
                "valor": 15000.00,
                "prazo": 24,
                "taxa": 12.5,
                "tempo_relacionamento": 24,
                "qtd_produtos_ativos": 2,
                "qtd_atrasos_12m": 0,
                "genero": "Masculino",
                "estado_civil": "Casado",
                "escolaridade": "Superior",
                "regiao": "Sudeste",
                "uf": "SP",
                "porte_municipio": "Metrópole",
                "tipo_produto": "CDC",
                "canal_aquisicao": "App",
            }
        },
    )


class PredictResponse(BaseModel):
    """
    Response schema for credit risk prediction
    """

    cliente_id: Optional[str] = Field(None, description="ID do cliente")
    prediction: int = Field(..., description="Predição (0=Adimplente, 1=Inadimplente)")
    probability: float = Field(..., ge=0, le=1, description="Probabilidade de inadimplência")
    risk_score: float = Field(..., ge=0, le=100, description="Score de risco (0-100)")
    recommendation: str = Field(..., description="Recomendação (Aprovar/Negar/Revisar)")
    confidence: float = Field(..., ge=0, le=1, description="Confiança da predição")
    threshold: float = Field(..., description="Threshold utilizado")
    model_version: str = Field(..., description="Versão do modelo")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp da predição")
    explainability: Optional[Dict[str, float]] = Field(None, description="Feature importance")

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={
            "example": {
                "cliente_id": "12345678901",
                "prediction": 0,
                "probability": 0.05,
                "risk_score": 5.0,
                "recommendation": "Aprovar",
                "confidence": 0.95,
                "threshold": 0.50,
                "model_version": "1.0.0-lgbm",
                "timestamp": "2025-10-28T12:00:00Z",
                "explainability": {
                    "score": -0.35,
                    "tempo_cliente_meses": -0.25,
                    "fator_risco": 0.15,
                    "parcela_mensal": 0.10,
                },
            }
        },
    )


class BatchPredictRequest(BaseModel):
    """
    Request schema for batch prediction
    """

    requests: List[PredictRequest] = Field(..., max_length=1000, description="Lista de requisições (máx 1000)")

    @field_validator("requests")
    @classmethod
    def validate_batch_size(cls, v):
        if len(v) > 1000:
            raise ValueError("Máximo de 1000 requisições por batch")
        if len(v) == 0:
            raise ValueError("Batch não pode estar vazio")
        return v


class BatchPredictResponse(BaseModel):
    """
    Response schema for batch prediction
    """

    predictions: List[PredictResponse] = Field(..., description="Lista de predições")
    total: int = Field(..., description="Total de predições")
    success: int = Field(..., description="Predições bem-sucedidas")
    failed: int = Field(..., description="Predições que falharam")
    processing_time: float = Field(..., description="Tempo de processamento em segundos")


class HealthResponse(BaseModel):
    """
    Response schema for health check
    """

    status: str = Field(..., description="Status da API")
    version: str = Field(..., description="Versão da API")
    model_loaded: bool = Field(..., description="Modelo carregado")
    model_type: Optional[str] = Field(None, description="Tipo do modelo")
    model_features: Optional[int] = Field(None, description="Número de features")
    database: str = Field(..., description="Status do banco de dados")
    redis: str = Field(..., description="Status do Redis")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    model_config = ConfigDict(protected_namespaces=())


class ModelInfoResponse(BaseModel):
    """
    Response schema for model information
    """

    name: str = Field(..., description="Nome do modelo")
    version: str = Field(..., description="Versão do modelo")
    algorithm: str = Field(..., description="Algoritmo utilizado")
    features: List[str] = Field(..., description="Features utilizadas")
    metrics: Dict[str, float] = Field(..., description="Métricas do modelo")
    trained_at: Optional[datetime] = Field(None, description="Data de treinamento")
    threshold: float = Field(..., description="Threshold padrão")

    model_config = ConfigDict(protected_namespaces=())


class MetricsResponse(BaseModel):
    """
    Response schema for metrics
    """

    total_predictions: int = Field(..., description="Total de predições")
    approval_rate: float = Field(..., ge=0, le=1, description="Taxa de aprovação")
    avg_risk_score: float = Field(..., description="Score de risco médio")
    avg_processing_time: float = Field(..., description="Tempo médio de processamento (ms)")
    model_version: str = Field(..., description="Versão do modelo")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    model_config = ConfigDict(protected_namespaces=())
