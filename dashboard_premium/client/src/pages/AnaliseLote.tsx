import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Upload, Download, FileSpreadsheet, CheckCircle, XCircle, AlertCircle, Loader2, TrendingUp, DollarSign, AlertTriangle } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';
import axios from 'axios';
import Papa from 'papaparse';
import { produtoParaAPI } from '@/utils/produtosMapping';

// Mini trend data
const trendData = [
  { value: 65 },
  { value: 72 },
  { value: 68 },
  { value: 75 },
  { value: 82 },
  { value: 78 },
  { value: 85 },
];

interface AnalysisResult {
  cliente_id: string;
  nome?: string;
  valor: number;
  probabilidade_inadimplencia: number;
  score_credito: number;
  decisao: string;
  motivo_rejeicao?: string;
  perda_evitada?: number;
  risco_categoria: string;
}

export default function AnaliseLote() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<AnalysisResult[]>([]);
  const [error, setError] = useState<string>('');
  const [progress, setProgress] = useState({ current: 0, total: 0 });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError('');
      setResults([]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setError('');
    setResults([]);
    setProgress({ current: 0, total: 0 });

    try {
      // Parse CSV file
      Papa.parse(file, {
        header: true,
        skipEmptyLines: true,
        complete: async (parseResult) => {
          const data = parseResult.data;
          
          if (!data || data.length === 0) {
            setError('Arquivo vazio ou formato inválido');
            setLoading(false);
            return;
          }

          console.log(`Processando ${data.length} registros...`);
          setProgress({ current: 0, total: data.length });

          const allResults: AnalysisResult[] = [];
          const batchSize = 10; // Process 10 at a time to avoid overwhelming the API

          // Process in batches
          for (let i = 0; i < data.length; i += batchSize) {
            const batch = data.slice(i, Math.min(i + batchSize, data.length));
            
            const batchPromises = batch.map(async (row: any) => {
              // Helper functions to map CSV values to API enums
              const mapGenero = (g: string) => {
                const map: any = { 'M': 'Masculino', 'F': 'Feminino', 'Masculino': 'Masculino', 'Feminino': 'Feminino', 'Outro': 'Outro' };
                return map[g] || 'Masculino';
              };
              
              const mapTipoProduto = (tp: string) => {
                if (tp.includes('Pessoal') || tp.includes('pessoal')) return 'Pessoal';
                if (tp.includes('CDC') || tp.includes('cdc')) return 'CDC';
                if (tp.includes('Imobiliário') || tp.includes('Imobiliario') || tp.includes('imobili')) return 'Imobiliario';
                if (tp.includes('Cartão') || tp.includes('Cartao') || tp.includes('cart')) return 'Cartao';
                if (tp.includes('Veículo') || tp.includes('Veiculo') || tp.includes('Auto')) return 'CDC';
                return 'Pessoal';
              };
              
              const mapCanalAquisicao = (ca: string) => {
                if (ca.includes('App') || ca.includes('app') || ca.includes('Digital') || ca.includes('digital')) return 'App';
                if (ca.includes('Agência') || ca.includes('Agencia') || ca.includes('agencia')) return 'Agência';
                if (ca.includes('Parceiro') || ca.includes('parceiro')) return 'Parceiro';
                if (ca.includes('Internet') || ca.includes('Banking') || ca.includes('internet')) return 'Internet Banking';
                return 'App';
              };
              
              const mapEscolaridade = (esc: string) => {
                const escLower = esc.toLowerCase();
                if (escLower.includes('fundamental')) return 'Fundamental';
                if (escLower.includes('médio') || escLower.includes('medio')) return 'Médio';
                if (escLower.includes('superior') && !escLower.includes('pós') && !escLower.includes('pos')) return 'Superior';
                if (escLower.includes('pós') || escLower.includes('pos') || escLower.includes('gradua')) return 'Pós-Graduação';
                return 'Superior';
              };

              // Map CSV fields to API schema (with aliases and enums)
              const requestData = {
                  cliente_id: row.cliente_id || `CLI-${Math.floor(Math.random() * 100000)}`,
                  idade: parseInt(row.idade) || 30,
                  renda_mensal: parseFloat(row.renda_mensal) || 3000,  // API alias: renda
                  score_credito: parseInt(row.score_credito) || 650,    // API alias: score
                  valor: parseFloat(row.valor) || 10000,                // API alias: ticket
                  prazo: parseInt(row.prazo) || 12,                     // API alias: prazo_meses
                  taxa: parseFloat(row.taxa) || 2.5,                    // API alias: taxa_juros_aa
                  tempo_relacionamento: parseInt(row.tempo_relacionamento) || 12,  // API alias: tempo_cliente_meses
                  qtd_produtos_ativos: parseInt(row.qtd_produtos_ativos) || 1,    // API alias: qtd_produtos
                  qtd_atrasos_12m: parseInt(row.qtd_atrasos_12m) || 0,
                  genero: mapGenero(row.genero || 'M'),                // Enum: Masculino, Feminino, Outro
                  estado_civil: row.estado_civil || 'Solteiro',         // Enum: Solteiro, Casado, Divorciado, Viúvo
                  escolaridade: mapEscolaridade(row.escolaridade || 'Superior'),  // Enum: Fundamental, Médio, Superior, Pós-Graduação
                  regiao: row.regiao || 'Sudeste',                      // Enum: Sudeste, Sul, Nordeste, Centro-Oeste, Norte
                  uf: (row.uf || 'SP').toUpperCase(),                   // Must be 2-letter uppercase
                  porte_municipio: row.porte_municipio || 'Grande',     // Enum: Pequeno, Médio, Grande, Metrópole
                  tipo_produto: produtoParaAPI(mapTipoProduto(row.tipo_produto || 'Pessoal')),  // Converte para valor sem acentos
                  canal_aquisicao: mapCanalAquisicao(row.canal_aquisicao || 'App')  // Enum mapping
                };

              try {
                const response = await axios.post('http://localhost:8000/api/v1/predict', requestData, {
                  timeout: 10000 // 10 second timeout
                });

                const result = response.data;
                console.log('Resposta da API:', result);
                
                // Calculate risk category
                const risco = result.probability * 100;  // API usa 'probability', não 'probabilidade_inadimplencia'
                let risco_categoria = 'Baixo';
                if (risco > 60) risco_categoria = 'Alto';
                else if (risco > 30) risco_categoria = 'Médio';

                // Determine decision justification (for all decisions)
                let motivo_rejeicao = '';
                
                if (result.recommendation === 'Aprovar') {
                  // Justificativas para aprovação
                  if (requestData.score_credito >= 800) {
                    motivo_rejeicao = 'Score excelente e baixo risco de inadimplência';
                  } else if (requestData.score_credito >= 700) {
                    motivo_rejeicao = 'Bom score de crédito e perfil favorável';
                  } else if (result.probability < 0.15) {
                    motivo_rejeicao = 'Risco muito baixo de inadimplência';
                  } else if (requestData.qtd_atrasos_12m === 0 && requestData.tempo_relacionamento >= 24) {
                    motivo_rejeicao = 'Cliente fiel sem histórico de atrasos';
                  } else {
                    motivo_rejeicao = 'Perfil de crédito adequado para aprovação';
                  }
                } else if (result.recommendation === 'Revisar') {
                  // Motivos para revisão manual - priorizar por ordem de importância
                  if (requestData.qtd_atrasos_12m > 0 && requestData.qtd_atrasos_12m <= 2) {
                    motivo_rejeicao = 'Histórico de atrasos leves - verificar justificativas';
                  } else if (requestData.valor > requestData.renda_mensal * 3 && requestData.valor <= requestData.renda_mensal * 5) {
                    motivo_rejeicao = 'Comprometimento de renda elevado - validar capacidade';
                  } else if (requestData.tempo_relacionamento < 12) {
                    motivo_rejeicao = 'Relacionamento recente - avaliar histórico externo';
                  } else if (result.probability >= 0.4 && result.probability < 0.5) {
                    motivo_rejeicao = 'Risco médio-alto - análise criteriosa necessária';
                  } else if (result.probability >= 0.3 && result.probability < 0.4) {
                    motivo_rejeicao = 'Risco médio - validar garantias adicionais';
                  } else if (requestData.score_credito >= 600 && requestData.score_credito < 700) {
                    motivo_rejeicao = 'Score intermediário - avaliar outros fatores';
                  } else {
                    motivo_rejeicao = 'Perfil requer avaliação manual detalhada';
                  }
                } else if (result.recommendation === 'Negar') {
                  // Motivos para rejeição
                  if (requestData.score_credito < 600) {
                    motivo_rejeicao = 'Score de crédito abaixo do mínimo aceitável';
                  } else if (result.probability > 0.7) {
                    motivo_rejeicao = 'Alta probabilidade de inadimplência';
                  } else if (requestData.qtd_atrasos_12m > 3) {
                    motivo_rejeicao = 'Histórico crítico de atrasos recentes';
                  } else if (requestData.valor > requestData.renda_mensal * 5) {
                    motivo_rejeicao = 'Valor incompatível com capacidade de pagamento';
                  } else {
                    motivo_rejeicao = 'Análise de risco desfavorável';
                  }
                }

                // Calculate avoided loss (for rejected high-risk clients)
                let perda_evitada = 0;
                if (result.recommendation === 'Negar' && result.probability > 0.5) {
                  perda_evitada = requestData.valor * result.probability;
                }

                return {
                  cliente_id: row.cliente_id || `CLI-${Math.floor(Math.random() * 10000)}`,
                  nome: row.nome || `Cliente ${row.cliente_id || i}`,
                  valor: requestData.valor,
                  probabilidade_inadimplencia: result.probability,  // Mapear probability para probabilidade_inadimplencia
                  score_credito: requestData.score_credito,
                  decisao: result.recommendation,  // Mapear recommendation para decisao
                  motivo_rejeicao,
                  perda_evitada,
                  risco_categoria
                };
              } catch (err: any) {
                console.error('Erro ao processar registro:', err);
                console.error('Detalhes do erro:', err.response?.data);
                
                // Show detailed error in UI
                let errorMessage = err.response?.data?.detail || err.response?.data || 'Erro desconhecido';
                // Convert to string if it's an object
                if (typeof errorMessage === 'object') {
                  errorMessage = JSON.stringify(errorMessage);
                }
                
                // Return a default error result
                return {
                  cliente_id: row.cliente_id || `CLI-ERROR-${i}`,
                  nome: row.nome || 'Erro',
                  valor: parseFloat(row.valor) || 0,
                  probabilidade_inadimplencia: 0,
                  score_credito: parseInt(row.score_credito) || 0,
                  decisao: 'Erro',
                  motivo_rejeicao: String(errorMessage).substring(0, 150),  // Show first 150 chars of error
                  perda_evitada: 0,
                  risco_categoria: 'N/A'
                };
              }
            });

            const batchResults = await Promise.all(batchPromises);
            // Filter to ensure only desired fields are included
            const filteredResults = batchResults.map(r => ({
              cliente_id: r.cliente_id,
              nome: r.nome,
              valor: r.valor,
              probabilidade_inadimplencia: r.probabilidade_inadimplencia,
              score_credito: r.score_credito,
              decisao: r.decisao,
              motivo_rejeicao: r.motivo_rejeicao,
              perda_evitada: r.perda_evitada,
              risco_categoria: r.risco_categoria
            }));
            allResults.push(...filteredResults);
            
            // Update progress
            setProgress({ current: allResults.length, total: data.length });
            setResults([...allResults]); // Update UI progressively
          }

          setLoading(false);
          console.log(`Processamento concluído: ${allResults.length} registros`);
        },
        error: (error) => {
          setError(`Erro ao ler arquivo: ${error.message}`);
          setLoading(false);
        }
      });
    } catch (err: any) {
      setError(err.message || 'Erro ao processar arquivo');
      setLoading(false);
    }
  };

  const handleDownload = () => {
    const csv = [
      ['ID', 'Cliente', 'Valor', 'Risco (%)', 'Score', 'Decisão', 'Categoria', 'Motivo Rejeição', 'Perda Evitada'],
      ...results.map(r => [
        r.cliente_id,
        r.nome || '',
        r.valor.toFixed(2),
        (r.probabilidade_inadimplencia * 100).toFixed(1),
        r.score_credito,
        r.decisao,
        r.risco_categoria,
        r.motivo_rejeicao || '',
        r.perda_evitada ? r.perda_evitada.toFixed(2) : '0.00'
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analise_lote_completa_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const stats = results.length > 0 ? {
    total: results.length,
    aprovados: results.filter(r => r.decisao === 'Aprovar').length,
    negados: results.filter(r => r.decisao === 'Negar').length,
    riscoMedio: (results.reduce((acc, r) => acc + r.probabilidade_inadimplencia * 100, 0) / results.length).toFixed(1),
    perdaEvitadaTotal: results.reduce((acc, r) => acc + (r.perda_evitada || 0), 0)
  } : null;

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Análise em Lote</h1>
        <p className="text-sm text-muted-foreground">Processe múltiplas análises de crédito simultaneamente</p>
      </div>

      {/* Progress Bar */}
      {loading && progress.total > 0 && (
        <Card className="p-4 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-foreground font-medium">Processando...</span>
            <span className="text-sm text-muted-foreground">
              {progress.current} / {progress.total} ({Math.round((progress.current / progress.total) * 100)}%)
            </span>
          </div>
          <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
            <div 
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${(progress.current / progress.total) * 100}%` }}
            />
          </div>
        </Card>
      )}

      {/* Stats Row */}
      {stats && (
        <div className="grid grid-cols-5 gap-4">
          <Card className="p-6 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5">
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Total Processado</p>
                <h3 className="text-2xl font-bold text-foreground">{stats.total.toLocaleString('pt-BR')}</h3>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={40}>
              <LineChart data={trendData}>
                <Line type="monotone" dataKey="value" stroke="#7C3AED" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </Card>

          <Card className="p-6 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5">
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Aprovados</p>
                <h3 className="text-2xl font-bold text-green-500">{stats.aprovados.toLocaleString('pt-BR')}</h3>
                <p className="text-xs text-muted-foreground mt-1">{((stats.aprovados / stats.total) * 100).toFixed(1)}%</p>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={40}>
              <LineChart data={trendData}>
                <Line type="monotone" dataKey="value" stroke="#06B6D4" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </Card>

          <Card className="p-6 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5">
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Negados</p>
                <h3 className="text-2xl font-bold text-red-500">{stats.negados.toLocaleString('pt-BR')}</h3>
                <p className="text-xs text-muted-foreground mt-1">{((stats.negados / stats.total) * 100).toFixed(1)}%</p>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={40}>
              <LineChart data={trendData}>
                <Line type="monotone" dataKey="value" stroke="#EC4899" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </Card>

          <Card className="p-6 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5">
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Risco Médio</p>
                <h3 className="text-2xl font-bold text-foreground">{stats.riscoMedio}%</h3>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={40}>
              <LineChart data={trendData}>
                <Line type="monotone" dataKey="value" stroke="#8B5CF6" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </Card>

          <Card className="p-6 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5">
            <div className="mb-3">
              <p className="text-sm text-muted-foreground mb-1">Perda Evitada</p>
              <h3 className="text-2xl font-bold text-green-500">
                R$ {stats.perdaEvitadaTotal.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </h3>
            </div>
            <p className="text-xs text-muted-foreground">Economia com rejeições</p>
          </Card>
        </div>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-12 gap-6">
        {/* Upload Card */}
        <div className="col-span-4">
          <Card className="p-6 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5">
            <h2 className="text-xl font-bold text-foreground mb-6">Upload de Arquivo</h2>

            <div className="space-y-6">
              {/* Upload Area */}
              <div className="border-2 border-dashed border-white/10 rounded-xl p-8 text-center hover:border-primary/50 transition-all cursor-pointer">
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={handleFileChange}
                  className="hidden"
                  id="file-upload"
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                    <FileSpreadsheet className="w-8 h-8 text-primary" />
                  </div>
                  <p className="text-sm font-medium text-foreground mb-1">
                    {file ? file.name : 'Clique para selecionar'}
                  </p>
                  <p className="text-xs text-muted-foreground">CSV, XLSX ou XLS</p>

                </label>
              </div>

              {error && (
                <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-red-500">{error}</p>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="space-y-3">
                <Button
                  onClick={handleUpload}
                  disabled={!file || loading}
                  className="w-full bg-primary hover:bg-primary/90 text-primary-foreground h-12 text-base font-semibold"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                      Processando {progress.total > 0 ? `(${progress.current}/${progress.total})` : '...'}
                    </>
                  ) : (
                    <>
                      <Upload className="w-5 h-5 mr-2" />
                      Processar Arquivo
                    </>
                  )}
                </Button>

                {results.length > 0 && !loading && (
                  <Button
                    onClick={handleDownload}
                    variant="outline"
                    className="w-full bg-white/5 border-white/10 hover:bg-white/10 text-foreground h-12 text-base font-semibold"
                  >
                    <Download className="w-5 h-5 mr-2" />
                    Baixar Resultados Completos
                  </Button>
                )}
              </div>

              {/* Info */}
              <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                <h4 className="text-sm font-semibold text-foreground mb-2">Formato do Arquivo</h4>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  O arquivo deve conter as colunas: cliente_id, idade, renda_mensal, score_credito, valor, prazo, taxa, tempo_relacionamento, qtd_produtos_ativos, qtd_atrasos_12m, genero, estado_civil, escolaridade, regiao, uf, porte_municipio, tipo_produto, canal_aquisicao
                </p>
              </div>


            </div>
          </Card>
        </div>

        {/* Results Table */}
        <div className="col-span-8">
          <Card className="p-6 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-foreground">Resultados da Análise</h2>
              {results.length > 0 && (
                <span className="text-sm text-muted-foreground">
                  {results.length.toLocaleString('pt-BR')} registros processados
                </span>
              )}
            </div>

            {results.length > 0 ? (
              <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
                <table className="w-full">
                  <thead className="sticky top-0 bg-[#1A1D2E] z-10">
                    <tr className="border-b border-white/5">
                      <th className="text-left py-3 px-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">ID</th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Valor</th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Score</th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Risco</th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Decisão</th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Motivo/Perda</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.map((result, index) => (
                      <tr key={index} className="border-b border-white/5 hover:bg-white/5 transition-all">
                        <td className="py-4 px-4 text-sm font-mono text-muted-foreground">{result.cliente_id}</td>
                        <td className="py-4 px-4 text-sm text-foreground">
                          R$ {result.valor.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-4 px-4 text-sm font-bold text-foreground">{result.score_credito}</td>
                        <td className="py-4 px-4">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden max-w-[80px]">
                              <div
                                className="h-full rounded-full"
                                style={{
                                  width: `${result.probabilidade_inadimplencia * 100}%`,
                                  background: result.probabilidade_inadimplencia < 0.3 ? '#06B6D4' : result.probabilidade_inadimplencia < 0.6 ? '#F59E0B' : '#EC4899'
                                }}
                              />
                            </div>
                            <span className="text-xs font-medium text-foreground">
                              {(result.probabilidade_inadimplencia * 100).toFixed(1)}%
                            </span>
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex items-center gap-2">
                            {result.decisao === 'Aprovar' ? (
                              <>
                                <CheckCircle className="w-5 h-5 text-green-500" />
                                <span className="text-sm font-semibold text-green-500">Aprovado</span>
                              </>
                            ) : result.decisao === 'Negar' ? (
                              <>
                                <XCircle className="w-5 h-5 text-red-500" />
                                <span className="text-sm font-semibold text-red-500">Negado</span>
                              </>
                            ) : (
                              <>
                                <AlertCircle className="w-5 h-5 text-amber-500" />
                                <span className="text-sm font-semibold text-amber-500">{result.decisao}</span>
                              </>
                            )}
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          {result.motivo_rejeicao ? (
                            <div className="flex items-start gap-2">
                              {result.decisao === 'Aprovar' ? (
                                <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" style={{ zIndex: 10 }} />
                              ) : result.decisao === 'Negar' ? (
                                <XCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" style={{ zIndex: 10 }} />
                              ) : (
                                <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" style={{ zIndex: 10 }} />
                              )}
                              <div>
                                <p className={`text-xs font-medium mb-0 ${
                                  result.decisao === 'Aprovar' ? 'text-green-500' : 
                                  result.decisao === 'Negar' ? 'text-red-500' : 
                                  'text-amber-500'
                                }`}>
                                  {String(result.motivo_rejeicao)}
                                </p>
                                {(result.perda_evitada !== undefined && result.perda_evitada !== null && result.perda_evitada > 0) && (
                                  <p className="text-xs text-green-500 mt-1 mb-0">
                                    Perda evitada: {result.perda_evitada.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                                  </p>
                                )}
                              </div>
                            </div>
                          ) : (
                            <span className="text-xs text-muted-foreground">-</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-16">
                <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center mx-auto mb-4">
                  <FileSpreadsheet className="w-10 h-10 text-muted-foreground" />
                </div>
                <p className="text-sm text-muted-foreground mb-2">Nenhum arquivo processado ainda</p>
                <p className="text-xs text-muted-foreground">Faça upload de um arquivo CSV para começar</p>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
