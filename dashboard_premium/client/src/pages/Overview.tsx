import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { TrendingUp, TrendingDown, ChevronRight, MoreHorizontal, RefreshCw } from 'lucide-react';
import { useEffect, useState } from 'react';
import { apiService, MetricsResponse } from '@/services/api';
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';

export default function Overview() {
  // Carregar threshold do localStorage ou usar 0.5 como padrão
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [threshold, setThreshold] = useState(() => {
    const saved = localStorage.getItem('creditRiskThreshold');
    return saved ? parseFloat(saved) : 0.5;
  });
  const [tempThreshold, setTempThreshold] = useState(() => {
    const saved = localStorage.getItem('creditRiskThreshold');
    return saved ? parseFloat(saved) : 0.5;
  });
  const [error, setError] = useState<string | null>(null);

  const loadMetrics = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getMetrics(threshold);
      setMetrics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar métricas');
      console.error('Erro ao carregar métricas:', err);
    } finally {
      setLoading(false);
    }
  };

  // Debounce para threshold - só atualiza após 500ms sem mudanças
  useEffect(() => {
    const timer = setTimeout(() => {
      setThreshold(tempThreshold);
      // Salvar no localStorage
      localStorage.setItem('creditRiskThreshold', tempThreshold.toString());
    }, 500);

    return () => clearTimeout(timer);
  }, [tempThreshold]);

  useEffect(() => {
    loadMetrics();
  }, [threshold]);

  // Cancelar requisições ao sair da página
  useEffect(() => {
    return () => {
      console.log('🚫 Cancelando requisições ao sair da página Overview');
      apiService.cancelRequest('metrics');
    };
  }, []);

  if (loading && !metrics) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-muted-foreground" />
          <p className="text-muted-foreground">Carregando métricas...</p>
        </div>
      </div>
    );
  }

  if (error && !metrics) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-destructive mb-4">{error}</p>
          <Button onClick={loadMetrics}>Tentar Novamente</Button>
        </div>
      </div>
    );
  }

  if (!metrics) {
    return null;
  }

  const totalAnalyses = metrics.totalClientes;
  const approved = metrics.clientesAprovados;
  const denied = metrics.clientesRejeitados;
  const approvalRate = metrics.taxaAprovacao;
  const defaultRate = metrics.taxaInadimplencia;

  // Dados para o gráfico de distribuição de risco
  const riskDistribution = [
    { 
      name: 'Aprovados', 
      value: metrics.clientesAprovados, 
      color: '#06B6D4',
      percentage: ((metrics.clientesAprovados / metrics.totalClientes) * 100).toFixed(1)
    },
    { 
      name: 'Rejeitados', 
      value: metrics.clientesRejeitados, 
      color: '#EC4899',
      percentage: ((metrics.clientesRejeitados / metrics.totalClientes) * 100).toFixed(1)
    },
  ];

  // Metas de performance baseadas em dados reais
  const goals = [
    { 
      name: 'Taxa de Aprovação', 
      progress: Math.min(metrics.taxaAprovacao, 100), 
      saved: `${metrics.taxaAprovacao.toFixed(1)}%`, 
      goal: '75%', 
      color: '#7C3AED' 
    },
    { 
      name: 'Taxa de Inadimplência', 
      progress: Math.max(0, 100 - (metrics.taxaInadimplencia * 10)), 
      saved: `${metrics.taxaInadimplencia.toFixed(1)}%`, 
      goal: '< 3%', 
      color: '#06B6D4' 
    },
    { 
      name: 'Saldo Líquido', 
      progress: 85, 
      saved: formatCurrency(metrics.saldoLiquido), 
      goal: 'Máximo', 
      color: '#EC4899' 
    },
  ];

  function formatCurrency(value: number): string {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  }

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">Dashboard de Risco de Crédito</h1>
          <p className="text-sm text-muted-foreground">
            Monitore análises em tempo real e tendências de risco • Threshold: {(threshold * 100).toFixed(0)}%
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm text-muted-foreground">Threshold:</label>
            <input
              type="range"
              min="0"
              max="100"
              value={tempThreshold * 100}
              onChange={(e) => setTempThreshold(Number(e.target.value) / 100)}
              className="w-32"
            />
            <span className="text-sm font-medium text-foreground w-12">{(tempThreshold * 100).toFixed(0)}%</span>
          </div>
          <Button 
            onClick={loadMetrics} 
            disabled={loading}
            variant="outline"
            size="sm"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-4 gap-6">
        {/* Total Analyses */}
        <Card className="p-6 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-sm text-muted-foreground mb-2">Total de Clientes</p>
              <div className="flex items-baseline gap-2">
                <h2 className="text-3xl font-bold text-foreground">{totalAnalyses.toLocaleString('pt-BR')}</h2>
              </div>
            </div>
          </div>
          <p className="text-xs text-muted-foreground">Base completa analisada</p>
        </Card>

        {/* Approved */}
        <Card className="p-6 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-sm text-muted-foreground mb-2">Aprovados</p>
              <div className="flex items-baseline gap-2">
                <h2 className="text-3xl font-bold text-chart-2">{approved.toLocaleString('pt-BR')}</h2>
                <span className="flex items-center text-sm text-chart-2 font-medium px-2 py-0.5 rounded-full bg-chart-2/20">
                  {approvalRate.toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
          <p className="text-xs text-muted-foreground">Taxa de aprovação</p>
        </Card>

        {/* Denied */}
        <Card className="p-6 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-sm text-muted-foreground mb-2">Rejeitados</p>
              <div className="flex items-baseline gap-2">
                <h2 className="text-3xl font-bold text-destructive">{denied.toLocaleString('pt-BR')}</h2>
                <span className="flex items-center text-sm text-destructive font-medium px-2 py-0.5 rounded-full bg-destructive/20">
                  {(100 - approvalRate).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
          <p className="text-xs text-muted-foreground">Taxa de rejeição</p>
        </Card>

        {/* Default Rate */}
        <Card className="p-6 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-sm text-muted-foreground mb-2">Inadimplência</p>
              <div className="flex items-baseline gap-2">
                <h2 className="text-3xl font-bold text-foreground">{defaultRate.toFixed(1)}%</h2>
                <span className={`flex items-center text-sm font-medium px-2 py-0.5 rounded-full ${
                  defaultRate < 3 ? 'text-chart-2 bg-chart-2/20' : 'text-destructive bg-destructive/20'
                }`}>
                  {defaultRate < 3 ? <TrendingDown className="w-3 h-3 mr-1" /> : <TrendingUp className="w-3 h-3 mr-1" />}
                  {defaultRate < 3 ? 'Baixo' : 'Alto'}
                </span>
              </div>
            </div>
          </div>
          <p className="text-xs text-muted-foreground">Entre aprovados</p>
        </Card>
      </div>

      {/* Grid Layout */}
      <div className="grid grid-cols-12 gap-6">
        {/* Financial Overview */}
        <div className="col-span-8">
          <Card className="p-6 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5 h-full">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-bold text-foreground mb-1">Visão Financeira</h3>
                <p className="text-sm text-muted-foreground">Análise de receitas, perdas e oportunidades</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
              {/* Receita Total */}
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Receita Total (Aprovados)</p>
                <p className="text-2xl font-bold text-chart-2">{formatCurrency(metrics.receitaTotal)}</p>
              </div>

              {/* Perdas por Inadimplência */}
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Perdas por Inadimplência</p>
                <p className="text-2xl font-bold text-destructive">{formatCurrency(metrics.perdasInadimplencia)}</p>
              </div>

              {/* Saldo Líquido */}
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Saldo Líquido</p>
                <p className="text-2xl font-bold text-chart-1">{formatCurrency(metrics.saldoLiquido)}</p>
              </div>

              {/* Perdas Evitadas */}
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Perdas Evitadas (Rejeitados)</p>
                <p className="text-2xl font-bold text-chart-3">{formatCurrency(metrics.perdasEvitadas)}</p>
              </div>

              {/* Oportunidades Perdidas */}
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Oportunidades Perdidas</p>
                <p className="text-2xl font-bold text-muted-foreground">{formatCurrency(metrics.oportunidadesPerdidas)}</p>
              </div>

              {/* Valor Médio */}
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Valor Médio por Cliente</p>
                <p className="text-2xl font-bold text-foreground">{formatCurrency(metrics.valorMedio)}</p>
              </div>
            </div>
          </Card>
        </div>

        {/* Distribution Chart */}
        <div className="col-span-4">
          <Card className="p-6 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5 h-full">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold text-foreground">Distribuição</h3>
            </div>

            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={riskDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {riskDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{
                    backgroundColor: '#1A1D2E',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '12px'
                  }}
                  formatter={(value: number) => value.toLocaleString('pt-BR')}
                />
              </PieChart>
            </ResponsiveContainer>

            <div className="space-y-3 mt-4">
              {riskDistribution.map((item, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-sm text-muted-foreground">{item.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-foreground">{item.value.toLocaleString('pt-BR')}</span>
                    <span className="text-xs text-muted-foreground">({item.percentage}%)</span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* Performance Goals */}
      <Card className="p-6 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-bold text-foreground">Metas de Performance</h3>
        </div>

        <div className="grid grid-cols-3 gap-6">
          {goals.map((goal, index) => (
            <div key={index} className="flex items-center gap-4">
              {/* Progress Circle */}
              <div className="relative w-16 h-16 flex-shrink-0">
                <svg className="w-16 h-16 -rotate-90">
                  <circle
                    cx="32"
                    cy="32"
                    r="28"
                    stroke="rgba(255,255,255,0.05)"
                    strokeWidth="6"
                    fill="none"
                  />
                  <circle
                    cx="32"
                    cy="32"
                    r="28"
                    stroke={goal.color}
                    strokeWidth="6"
                    fill="none"
                    strokeDasharray={`${2 * Math.PI * 28}`}
                    strokeDashoffset={`${2 * Math.PI * 28 * (1 - goal.progress / 100)}`}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-xs font-bold text-foreground">{goal.progress.toFixed(0)}%</span>
                </div>
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground mb-1">{goal.name}</p>
                <p className="text-xs text-muted-foreground">Atual: {goal.saved}</p>
              </div>

              {/* Values */}
              <div className="text-right">
                <p className="text-xs text-muted-foreground">Meta</p>
                <p className="text-sm font-medium text-foreground">{goal.goal}</p>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
