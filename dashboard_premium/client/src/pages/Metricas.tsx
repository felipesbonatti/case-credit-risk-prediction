import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useEffect, useState } from 'react';
import { apiService, ROCCurveData, ConfusionMatrix, ThresholdSensitivity } from '@/services/api';
import { RefreshCw } from 'lucide-react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine
} from 'recharts';

export default function Metricas() {
  const [rocData, setRocData] = useState<ROCCurveData | null>(null);
  const [confusionMatrix, setConfusionMatrix] = useState<ConfusionMatrix | null>(null);
  const [sensitivityData, setSensitivityData] = useState<ThresholdSensitivity | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Carregar threshold do localStorage
  const [threshold, setThreshold] = useState(() => {
    const saved = localStorage.getItem('creditRiskThreshold');
    return saved ? parseFloat(saved) : 0.5;
  });

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [roc, confusion, sensitivity] = await Promise.all([
        apiService.getROCCurve(),
        apiService.getConfusionMatrix(threshold),
        apiService.getThresholdSensitivity(),
      ]);

      setRocData(roc);
      setConfusionMatrix(confusion);
      setSensitivityData(sensitivity);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar métricas');
      console.error('Erro ao carregar métricas:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (confusionMatrix) {
      apiService.getConfusionMatrix(threshold).then(setConfusionMatrix);
    }
  }, [threshold]);

  // Cancelar requisições ao sair da página
  useEffect(() => {
    return () => {
      console.log('🚫 Cancelando requisições ao sair da página Métricas');
      apiService.cancelRequest('rocCurve');
      apiService.cancelRequest('confusionMatrix');
      apiService.cancelRequest('thresholdSensitivity');
    };
  }, []);

  if (loading && !rocData) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-muted-foreground" />
          <p className="text-muted-foreground">Carregando métricas do modelo...</p>
        </div>
      </div>
    );
  }

  if (error && !rocData) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-destructive mb-4">{error}</p>
          <Button onClick={loadData}>Tentar Novamente</Button>
        </div>
      </div>
    );
  }

  // Preparar dados para o gráfico ROC
  const rocChartData = rocData ? rocData.fpr.map((fpr, index) => ({
    fpr: fpr,
    tpr: rocData.tpr[index],
    threshold: rocData.thresholds[index],
  })) : [];

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">Métricas do Modelo</h1>
          <p className="text-sm text-muted-foreground">
            Análise de performance e métricas de avaliação do modelo de ML
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm text-muted-foreground">Threshold:</label>
            <input
              type="range"
              min="0"
              max="100"
              value={threshold * 100}
              onChange={(e) => {
                const newThreshold = Number(e.target.value) / 100;
                setThreshold(newThreshold);
                localStorage.setItem('creditRiskThreshold', newThreshold.toString());
              }}
              className="w-32"
            />
            <span className="text-sm font-medium text-foreground w-12">{(threshold * 100).toFixed(0)}%</span>
          </div>
          <Button 
            onClick={loadData} 
            disabled={loading}
            variant="outline"
            size="sm"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
        </div>
      </div>

      {/* Métricas Principais */}
      {confusionMatrix && (
        <div className="grid grid-cols-4 gap-6">
          <Card className="p-6 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5">
            <p className="text-sm text-muted-foreground mb-2">Acurácia</p>
            <p className="text-3xl font-bold text-foreground">{confusionMatrix.accuracy.toFixed(2)}%</p>
          </Card>

          <Card className="p-6 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5">
            <p className="text-sm text-muted-foreground mb-2">Precisão</p>
            <p className="text-3xl font-bold text-chart-1">{confusionMatrix.precision.toFixed(2)}%</p>
          </Card>

          <Card className="p-6 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5">
            <p className="text-sm text-muted-foreground mb-2">Recall</p>
            <p className="text-3xl font-bold text-chart-2">{confusionMatrix.recall.toFixed(2)}%</p>
          </Card>

          <Card className="p-6 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5">
            <p className="text-sm text-muted-foreground mb-2">F1-Score</p>
            <p className="text-3xl font-bold text-chart-3">{confusionMatrix.f1_score.toFixed(2)}%</p>
          </Card>
        </div>
      )}

      {/* Curva ROC e AUC */}
      {rocData && (
        <Card className="p-6 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-bold text-foreground mb-1">Curva ROC</h3>
              <p className="text-sm text-muted-foreground">
                Receiver Operating Characteristic • AUC: {rocData.auc.toFixed(4)}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-muted-foreground">AUC Score</p>
              <p className="text-3xl font-bold text-chart-1">{rocData.auc.toFixed(4)}</p>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={rocChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis 
                dataKey="fpr" 
                stroke="rgba(255,255,255,0.3)"
                fontSize={12}
                tickLine={false}
                label={{ value: 'Taxa de Falsos Positivos (FPR)', position: 'insideBottom', offset: -5, fill: 'rgba(255,255,255,0.5)' }}
              />
              <YAxis 
                stroke="rgba(255,255,255,0.3)"
                fontSize={12}
                tickLine={false}
                label={{ value: 'Taxa de Verdadeiros Positivos (TPR)', angle: -90, position: 'insideLeft', fill: 'rgba(255,255,255,0.5)' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1A1D2E',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '12px'
                }}
                formatter={(value: number) => value.toFixed(4)}
              />
              <Legend />
              <ReferenceLine 
                segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} 
                stroke="rgba(255,255,255,0.2)" 
                strokeDasharray="5 5"
                label="Baseline"
              />
              <Line 
                type="monotone" 
                dataKey="tpr" 
                stroke="#7C3AED" 
                strokeWidth={3}
                dot={false}
                name="Curva ROC"
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      )}

      {/* Matriz de Confusão */}
      {confusionMatrix && (
        <Card className="p-6 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5">
          <h3 className="text-lg font-bold text-foreground mb-6">Matriz de Confusão</h3>
          
          <div className="grid grid-cols-2 gap-4 max-w-2xl mx-auto">
            {/* True Positives */}
            <div className="p-6 bg-chart-2/20 border-2 border-chart-2 rounded-lg">
              <p className="text-sm text-muted-foreground mb-2">Verdadeiros Positivos (TP)</p>
              <p className="text-4xl font-bold text-chart-2">{confusionMatrix.tp.toLocaleString('pt-BR')}</p>
              <p className="text-xs text-muted-foreground mt-2">Inadimplentes corretamente identificados</p>
            </div>

            {/* False Positives */}
            <div className="p-6 bg-destructive/20 border-2 border-destructive rounded-lg">
              <p className="text-sm text-muted-foreground mb-2">Falsos Positivos (FP)</p>
              <p className="text-4xl font-bold text-destructive">{confusionMatrix.fp.toLocaleString('pt-BR')}</p>
              <p className="text-xs text-muted-foreground mt-2">Adimplentes incorretamente rejeitados</p>
            </div>

            {/* False Negatives */}
            <div className="p-6 bg-destructive/20 border-2 border-destructive rounded-lg">
              <p className="text-sm text-muted-foreground mb-2">Falsos Negativos (FN)</p>
              <p className="text-4xl font-bold text-destructive">{confusionMatrix.fn.toLocaleString('pt-BR')}</p>
              <p className="text-xs text-muted-foreground mt-2">Inadimplentes incorretamente aprovados</p>
            </div>

            {/* True Negatives */}
            <div className="p-6 bg-chart-2/20 border-2 border-chart-2 rounded-lg">
              <p className="text-sm text-muted-foreground mb-2">Verdadeiros Negativos (TN)</p>
              <p className="text-4xl font-bold text-chart-2">{confusionMatrix.tn.toLocaleString('pt-BR')}</p>
              <p className="text-xs text-muted-foreground mt-2">Adimplentes corretamente aprovados</p>
            </div>
          </div>
        </Card>
      )}

      {/* Análise de Sensibilidade do Threshold */}
      {sensitivityData && (
        <Card className="p-6 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5">
          <div className="mb-6">
            <h3 className="text-lg font-bold text-foreground mb-1">Análise de Sensibilidade do Threshold</h3>
            <p className="text-sm text-muted-foreground">
              Impacto do threshold nas métricas de negócio
            </p>
          </div>

          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={sensitivityData.data}>
              <defs>
                <linearGradient id="approvalGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#7C3AED" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#7C3AED" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="defaultGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#EC4899" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#EC4899" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis 
                dataKey="threshold" 
                stroke="rgba(255,255,255,0.3)"
                fontSize={12}
                tickLine={false}
                label={{ value: 'Threshold', position: 'insideBottom', offset: -5, fill: 'rgba(255,255,255,0.5)' }}
              />
              <YAxis 
                stroke="rgba(255,255,255,0.3)"
                fontSize={12}
                tickLine={false}
                label={{ value: 'Taxa (%)', angle: -90, position: 'insideLeft', fill: 'rgba(255,255,255,0.5)' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1A1D2E',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '12px'
                }}
              />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="taxaAprovacao" 
                stroke="#7C3AED" 
                strokeWidth={2}
                fill="url(#approvalGradient)"
                name="Taxa de Aprovação (%)"
              />
              <Area 
                type="monotone" 
                dataKey="taxaInadimplencia" 
                stroke="#EC4899" 
                strokeWidth={2}
                fill="url(#defaultGradient)"
                name="Taxa de Inadimplência (%)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      )}

      {/* Saldo Líquido por Threshold */}
      {sensitivityData && (
        <Card className="p-6 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5">
          <div className="mb-6">
            <h3 className="text-lg font-bold text-foreground mb-1">Saldo Líquido por Threshold</h3>
            <p className="text-sm text-muted-foreground">
              Otimização do threshold para maximizar lucro
            </p>
          </div>

          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={sensitivityData.data}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis 
                dataKey="threshold" 
                stroke="rgba(255,255,255,0.3)"
                fontSize={12}
                tickLine={false}
                label={{ value: 'Threshold', position: 'insideBottom', offset: -5, fill: 'rgba(255,255,255,0.5)' }}
              />
              <YAxis 
                stroke="rgba(255,255,255,0.3)"
                fontSize={12}
                tickLine={false}
                tickFormatter={(value) => `R$ ${(value / 1000000).toFixed(1)}M`}
                label={{ value: 'Saldo Líquido (R$)', angle: -90, position: 'insideLeft', fill: 'rgba(255,255,255,0.5)' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1A1D2E',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '12px'
                }}
                formatter={(value: number) => new Intl.NumberFormat('pt-BR', {
                  style: 'currency',
                  currency: 'BRL',
                }).format(value)}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="saldoLiquido" 
                stroke="#06B6D4" 
                strokeWidth={3}
                dot={{ fill: '#06B6D4', r: 4 }}
                name="Saldo Líquido"
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      )}
    </div>
  );
}
