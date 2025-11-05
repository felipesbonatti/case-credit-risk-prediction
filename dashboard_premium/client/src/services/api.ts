/**
 * Serviço de API para integração com o backend de inadimplência
 * Com cache e cancelamento de requisições
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface PredictRequest {
  cliente_id?: string;
  idade: number;
  renda_mensal: number;
  score_credito: number;
  valor: number;
  prazo: number;
  taxa: number;
  tempo_relacionamento: number;
  qtd_produtos_ativos: number;
  qtd_atrasos_12m: number;
  genero: string;
  estado_civil: string;
  escolaridade: string;
  regiao: string;
  uf: string;
  porte_municipio: string;
  tipo_produto: string;
  canal_aquisicao?: string;
}

export interface PredictResponse {
  cliente_id?: string;
  prediction: number;
  probability: number;
  risk_score: number;
  recommendation: string;
  confidence: number;
  threshold: number;
  model_version: string;
  timestamp: string;
  explainability?: Record<string, number>;
  feature_importance?: Array<{
    feature: string;
    importance: number;
  }>;
}

export interface BatchPredictRequest {
  requests: PredictRequest[];
}

export interface BatchPredictResponse {
  predictions: PredictResponse[];
  total: number;
  success: number;
  failed: number;
  processing_time: number;
}

export interface MetricsResponse {
  saldoLiquido: number;
  taxaAprovacao: number;
  taxaInadimplencia: number;
  totalClientes: number;
  clientesAprovados: number;
  clientesRejeitados: number;
  receitaTotal: number;
  perdasInadimplencia: number;
  oportunidadesPerdidas: number;
  perdasEvitadas: number;
  valorMedio: number;
  threshold: number;
}

export interface ConfusionMatrix {
  tp: number;
  fp: number;
  tn: number;
  fn: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  threshold: number;
}

export interface ROCCurveData {
  fpr: number[];
  tpr: number[];
  thresholds: number[];
  auc: number;
}

export interface ThresholdSensitivity {
  data: Array<{
    threshold: number;
    taxaAprovacao: number;
    taxaInadimplencia: number;
    saldoLiquido: number;
    perdasEvitadas: number;
    oportunidadesPerdidas: number;
  }>;
}

export interface OptimizationResult {
  optimal_threshold: number;
  objective: string;
  best_value: number;
  metrics: MetricsResponse;
  all_results: Array<{
    threshold: number;
    value: number;
    metrics: MetricsResponse;
  }>;
}

// Cache simples com TTL
interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

class ApiService {
  private baseUrl: string;
  private cache: Map<string, CacheEntry<any>>;
  private cacheTTL: number = 5 * 60 * 1000; // 5 minutos
  private abortControllers: Map<string, AbortController>;

  constructor() {
    this.baseUrl = API_BASE_URL;
    this.cache = new Map();
    this.abortControllers = new Map();
  }

  /**
   * Gera chave de cache
   */
  private getCacheKey(endpoint: string, params?: Record<string, any>): string {
    const paramStr = params ? JSON.stringify(params) : '';
    return `${endpoint}:${paramStr}`;
  }

  /**
   * Verifica se cache é válido
   */
  private isCacheValid(key: string): boolean {
    const entry = this.cache.get(key);
    if (!entry) return false;
    
    const now = Date.now();
    const age = now - entry.timestamp;
    return age < this.cacheTTL;
  }

  /**
   * Obtém dados do cache
   */
  private getFromCache<T>(key: string): T | null {
    if (this.isCacheValid(key)) {
      return this.cache.get(key)!.data as T;
    }
    return null;
  }

  /**
   * Salva dados no cache
   */
  private saveToCache<T>(key: string, data: T): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
    });
  }

  /**
   * Limpa cache
   */
  clearCache(): void {
    this.cache.clear();
  }

  /**
   * Cancela requisição em andamento
   */
  cancelRequest(requestId: string): void {
    const controller = this.abortControllers.get(requestId);
    if (controller) {
      controller.abort();
      this.abortControllers.delete(requestId);
    }
  }

  /**
   * Cancela todas as requisições
   */
  cancelAllRequests(): void {
    this.abortControllers.forEach((controller) => controller.abort());
    this.abortControllers.clear();
  }

  /**
   * Fazer requisição com timeout e cancelamento
   */
  private async fetchWithTimeout(
    url: string,
    options: RequestInit = {},
    timeout: number = 30000,
    requestId?: string
  ): Promise<Response> {
    const controller = new AbortController();
    
    if (requestId) {
      // Cancelar requisição anterior com mesmo ID
      this.cancelRequest(requestId);
      this.abortControllers.set(requestId, controller);
    }

    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      
      if (requestId) {
        this.abortControllers.delete(requestId);
      }

      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (requestId) {
        this.abortControllers.delete(requestId);
      }

      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Requisição cancelada');
      }
      throw error;
    }
  }

  /**
   * Fazer predição individual
   */
  async predict(request: PredictRequest): Promise<PredictResponse> {
    const response = await this.fetchWithTimeout(
      `${this.baseUrl}/api/v1/predict`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      },
      30000,
      'predict'
    );

    if (!response.ok) {
      throw new Error(`Erro na predição: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Fazer predição em lote
   */
  async predictBatch(request: BatchPredictRequest): Promise<BatchPredictResponse> {
    const response = await this.fetchWithTimeout(
      `${this.baseUrl}/api/v1/predict/batch`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      },
      60000, // 1 minuto para batch
      'predictBatch'
    );

    if (!response.ok) {
      throw new Error(`Erro na predição em lote: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Obter métricas do modelo (com cache)
   */
  async getMetrics(threshold: number = 0.5, useCache: boolean = true): Promise<MetricsResponse> {
    const cacheKey = this.getCacheKey('metrics', { threshold: threshold.toFixed(2) });

    // Verificar cache
    if (useCache) {
      const cached = this.getFromCache<MetricsResponse>(cacheKey);
      if (cached) {
        console.log('📦 Métricas carregadas do cache');
        return cached;
      }
    }

    console.log('🌐 Carregando métricas da API...');
    
    const response = await this.fetchWithTimeout(
      `${this.baseUrl}/api/v1/metrics?threshold=${threshold}`,
      {},
      30000,
      'metrics'
    );

    if (!response.ok) {
      throw new Error(`Erro ao obter métricas: ${response.statusText}`);
    }

    const data = await response.json();
    
    // Salvar no cache
    this.saveToCache(cacheKey, data);
    
    return data;
  }

  /**
   * Obter matriz de confusão (com cache)
   */
  async getConfusionMatrix(threshold: number = 0.5, useCache: boolean = true): Promise<ConfusionMatrix> {
    const cacheKey = this.getCacheKey('confusion_matrix', { threshold: threshold.toFixed(2) });

    if (useCache) {
      const cached = this.getFromCache<ConfusionMatrix>(cacheKey);
      if (cached) {
        console.log('📦 Matriz de confusão carregada do cache');
        return cached;
      }
    }

    console.log('🌐 Carregando matriz de confusão da API...');
    
    const response = await this.fetchWithTimeout(
      `${this.baseUrl}/api/v1/analysis/confusion_matrix?threshold=${threshold}`,
      {},
      30000,
      'confusionMatrix'
    );

    if (!response.ok) {
      throw new Error(`Erro ao obter matriz de confusão: ${response.statusText}`);
    }

    const data = await response.json();
    this.saveToCache(cacheKey, data);
    
    return data;
  }

  /**
   * Obter dados da curva ROC (com cache)
   */
  async getROCCurve(useCache: boolean = true): Promise<ROCCurveData> {
    const cacheKey = this.getCacheKey('roc_curve');

    if (useCache) {
      const cached = this.getFromCache<ROCCurveData>(cacheKey);
      if (cached) {
        console.log('📦 Curva ROC carregada do cache');
        return cached;
      }
    }

    console.log('🌐 Carregando curva ROC da API...');
    
    const response = await this.fetchWithTimeout(
      `${this.baseUrl}/api/v1/analysis/roc_curve`,
      {},
      30000,
      'rocCurve'
    );

    if (!response.ok) {
      throw new Error(`Erro ao obter curva ROC: ${response.statusText}`);
    }

    const data = await response.json();
    this.saveToCache(cacheKey, data);
    
    return data;
  }

  /**
   * Obter análise de sensibilidade do threshold (com cache)
   */
  async getThresholdSensitivity(useCache: boolean = true): Promise<ThresholdSensitivity> {
    const cacheKey = this.getCacheKey('threshold_sensitivity');

    if (useCache) {
      const cached = this.getFromCache<ThresholdSensitivity>(cacheKey);
      if (cached) {
        console.log('📦 Sensibilidade do threshold carregada do cache');
        return cached;
      }
    }

    console.log('🌐 Carregando sensibilidade do threshold da API...');
    
    const response = await this.fetchWithTimeout(
      `${this.baseUrl}/api/v1/analysis/threshold_sensitivity`,
      {},
      30000,
      'thresholdSensitivity'
    );

    if (!response.ok) {
      throw new Error(`Erro ao obter sensibilidade do threshold: ${response.statusText}`);
    }

    const data = await response.json();
    this.saveToCache(cacheKey, data);
    
    return data;
  }

  /**
   * Otimizar threshold
   */
  async optimizeThreshold(objective: 'profit' | 'risk' | 'balanced' = 'profit'): Promise<OptimizationResult> {
    const response = await this.fetchWithTimeout(
      `${this.baseUrl}/api/v1/analysis/optimize_threshold?objective=${objective}`,
      {},
      30000,
      'optimizeThreshold'
    );

    if (!response.ok) {
      throw new Error(`Erro ao otimizar threshold: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Verificar saúde da API
   */
  async healthCheck(): Promise<any> {
    const response = await this.fetchWithTimeout(
      `${this.baseUrl}/health`,
      {},
      5000
    );

    if (!response.ok) {
      throw new Error(`Erro ao verificar saúde da API: ${response.statusText}`);
    }

    return response.json();
  }
}

export const apiService = new ApiService();
