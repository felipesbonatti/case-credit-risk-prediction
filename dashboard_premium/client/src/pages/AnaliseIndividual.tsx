import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { CheckCircle, CheckCircle2, XCircle, AlertCircle, Loader2, TrendingUp, TrendingDown } from 'lucide-react';
import { apiService, PredictRequest, PredictResponse } from '@/services/api';
import { calcularRentabilidade, calcularTaxaMinimaRentavel, formatCurrency as formatCurrencyUtil, classificarRiscoBACEN } from '@/utils/rentabilidade';
import { getTaxaMinimaProduto, getTaxaMediaProduto, getInfoProduto, validarTaxaProduto, ajustarTaxaMinima, TAXAS_POR_PRODUTO } from '@/utils/taxasProdutos';
import { produtoParaAPI } from '@/utils/produtosMapping';
import { calcularTaxaAutomatica, calcularRangeTaxas } from '@/utils/calculoTaxaAutomatica';

export default function AnaliseIndividual() {
  const [resultado, setResultado] = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [taxaWarning, setTaxaWarning] = useState<string | null>(null);
  const [taxaAutomatica, setTaxaAutomatica] = useState<{
    taxaSugerida: number;
    taxaMinima: number;
    taxaMaxima: number;
    justificativa: string;
    probabilidadeEstimada: number;
    taxaMinimaRentavel: number;
  } | null>(null);
  const [formData, setFormData] = useState<PredictRequest>({
    cliente_id: '',
    idade: 35,
    renda_mensal: 5000,
    score_credito: 650,
    valor: 15000,
    prazo: 24,
    taxa: getTaxaMediaProduto('CDC'), // Taxa média do produto CDC
    tempo_relacionamento: 24,
    qtd_produtos_ativos: 2,
    qtd_atrasos_12m: 0,
    genero: 'Masculino',
    estado_civil: 'Casado',
    escolaridade: 'Superior',
    regiao: 'Sudeste',
    uf: 'SP',
    porte_municipio: 'Metrópole',
    tipo_produto: 'CDC',
    canal_aquisicao: 'App',
  });

  // Recalcula taxa automaticamente quando mudam os parâmetros
  useEffect(() => {
    if (formData.tipo_produto && formData.valor > 0 && formData.score_credito > 0 && formData.prazo > 0 && formData.renda_mensal > 0) {
      const taxaCalc = calcularTaxaAutomatica({
        tipoProduto: formData.tipo_produto,
        valor: formData.valor,
        score: formData.score_credito,
        prazo: formData.prazo,
        renda: formData.renda_mensal,
        qtdAtrasos: formData.qtd_atrasos_12m
      });
      setTaxaAutomatica(taxaCalc);
      // SEMPRE atualiza a taxa do formulário com a sugerida quando o cálculo mudar
      setFormData(prev => ({ ...prev, taxa: taxaCalc.taxaSugerida }));
    }
  }, [formData.tipo_produto, formData.valor, formData.score_credito, formData.prazo, formData.renda_mensal, formData.qtd_atrasos_12m]);

  const handleInputChange = (field: keyof PredictRequest, value: any) => {
    setFormData({ ...formData, [field]: value });
  };

  const handleNumberInput = (field: keyof PredictRequest, value: string) => {
    // Remove zeros à esquerda e converte para número
    const numValue = value === '' ? 0 : Number(value.replace(/^0+/, '') || '0');
    setFormData({ ...formData, [field]: numValue });
  };

  // Handler para mudança de tipo de produto
  const handleProdutoChange = (tipoProduto: string) => {
    const taxaMedia = getTaxaMediaProduto(tipoProduto);
    setFormData({ 
      ...formData, 
      tipo_produto: tipoProduto,
      taxa: taxaMedia // Atualiza taxa para a média do novo produto
    });
    setTaxaWarning(null);
  };

  // Handler para mudança de taxa com validação
  const handleTaxaChange = (value: string) => {
    const taxa = value === '' ? 0 : Number(value.replace(/^0+/, '') || '0');
    const taxaMinima = getTaxaMinimaProduto(formData.tipo_produto);
    
    // Apenas avisa, mas não bloqueia
    if (taxa < taxaMinima && taxa > 0) {
      const infoProduto = getInfoProduto(formData.tipo_produto);
      setTaxaWarning(
        `Atenção: Taxa abaixo do mínimo recomendado de ${taxaMinima}% a.a. para ${infoProduto?.nome}. Isto pode não ser rentável para o banco.`
      );
    } else {
      setTaxaWarning(null);
    }
    setFormData({ ...formData, taxa });
  };

  // Handler para blur do campo de taxa (apenas validação visual)
  const handleTaxaBlur = () => {
    const taxaMinima = getTaxaMinimaProduto(formData.tipo_produto);
    if (formData.taxa < taxaMinima && formData.taxa > 0) {
      const infoProduto = getInfoProduto(formData.tipo_produto);
      setTaxaWarning(
        `Atenção: Taxa abaixo do mínimo recomendado de ${taxaMinima}% a.a. para ${infoProduto?.nome}.`
      );
    }
  };

  const handleAnalise = async () => {
    try {
      setLoading(true);
      setError(null);

      // Validação de idade mínima
      if (formData.idade < 18) {
        setError('Idade mínima para análise de crédito é 18 anos.');
        setLoading(false);
        return;
      }

      // Fazer a predição primeiro para obter a probabilidade
      // Converter produto para valor aceito pelo modelo (sem acentos)
      const formDataAPI = {
        ...formData,
        tipo_produto: produtoParaAPI(formData.tipo_produto)
      };
      const result = await apiService.predict(formDataAPI);

      // Calcular taxa mínima rentável baseada na probabilidade de inadimplência
      const taxaMinimaRentavel = calcularTaxaMinimaRentavel(
        formData.valor,
        formData.prazo,
        result.probability,
        13.31, // CDI atual
        5 // Margem mínima de 5%
      );

      // Calcular rentabilidade completa
      const rentabilidade = calcularRentabilidade(
        formData.valor,
        formData.prazo,
        formData.taxa,
        result.probability,
        13.31
      );

      // Se a taxa for insuficiente OU ROI negativo, ajustar recomendação
      // MAS respeitar a lógica do backend (não sobrescrever "Revisar")
      if (formData.taxa < taxaMinimaRentavel || rentabilidade.roi < 0) {
        // Apenas negar se já não for "Revisar"
        if (result.recommendation === 'Aprovar') {
          result.prediction = 1;
          result.recommendation = 'Revisar'; // Mudar de Aprovar para Revisar
        }
        // Se já é "Revisar" ou "Negar", manter
      }

      setResultado(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao fazer análise');
      console.error('Erro na análise:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (recommendation: string) => {
    if (recommendation === 'Aprovar') {
      return <CheckCircle2 className="w-16 h-16 text-chart-2" />;
    } else if (recommendation === 'Revisar') {
      return <AlertCircle className="w-16 h-16 text-yellow-500" />;
    } else {
      return <XCircle className="w-16 h-16 text-destructive" />;
    }
  };

  const getStatusColor = (recommendation: string) => {
    if (recommendation === 'Aprovar') return 'text-chart-2';
    if (recommendation === 'Revisar') return 'text-yellow-500';
    return 'text-destructive';
  };

  const getStatusBg = (recommendation: string) => {
    if (recommendation === 'Aprovar') return 'bg-chart-2/10';
    if (recommendation === 'Revisar') return 'bg-yellow-500/10';
    return 'bg-destructive/10';
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Análise Individual de Crédito</h1>
        <p className="text-sm text-muted-foreground">
          Preencha os dados do cliente para realizar a análise de risco de crédito
        </p>
      </div>

      {/* Formulário em Layout Horizontal */}
      <Card className="p-6 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5">
        <h3 className="text-lg font-bold text-foreground mb-6">Dados do Cliente</h3>
        
        <div className="space-y-6">
          {/* Linha 1: ID e Informações Básicas */}
          <div className="grid grid-cols-4 gap-4">
            <div>
              <Label htmlFor="cliente_id">ID do Cliente</Label>
              <Input
                id="cliente_id"
                value={formData.cliente_id}
                onChange={(e) => handleInputChange('cliente_id', e.target.value)}
                placeholder="Opcional"
                className="bg-white/5 border-white/10"
              />
            </div>

            <div>
              <Label htmlFor="idade">Idade</Label>
              <Input
                id="idade"
                type="number"
                value={formData.idade || ''}
                onChange={(e) => handleNumberInput('idade', e.target.value)}
                min="18"
                max="100"
                className="bg-white/5 border-white/10"
              />
            </div>

            <div>
              <Label htmlFor="renda_mensal">Renda Mensal (R$)</Label>
              <Input
                id="renda_mensal"
                type="number"
                value={formData.renda_mensal || ''}
                onChange={(e) => handleNumberInput('renda_mensal', e.target.value)}
                min="0"
                className="bg-white/5 border-white/10"
              />
            </div>

            <div>
              <Label htmlFor="score_credito">Score (300-950)</Label>
              <Input
                id="score_credito"
                type="number"
                value={formData.score_credito || ''}
                onChange={(e) => handleNumberInput('score_credito', e.target.value)}
                min="300"
                max="950"
                className="bg-white/5 border-white/10"
              />
            </div>
          </div>

          {/* Linha 2: Dados do Crédito */}
          <div className="grid grid-cols-4 gap-4">
            <div>
              <Label htmlFor="valor">Valor Solicitado (R$)</Label>
              <Input
                id="valor"
                type="number"
                value={formData.valor || ''}
                onChange={(e) => handleNumberInput('valor', e.target.value)}
                min="0"
                className="bg-white/5 border-white/10"
              />
            </div>

            <div>
              <Label htmlFor="prazo">Prazo (meses)</Label>
              <Input
                id="prazo"
                type="number"
                value={formData.prazo || ''}
                onChange={(e) => handleNumberInput('prazo', e.target.value)}
                min="1"
                max="360"
                className="bg-white/5 border-white/10"
              />
            </div>

            <div>
              <Label htmlFor="taxa">
                Taxa Anual (%)
              </Label>
              <div className="relative">
                <Input
                  id="taxa"
                  type="number"
                  value={formData.taxa || ''}
                  onChange={(e) => handleTaxaChange(e.target.value)}
                  onBlur={handleTaxaBlur}
                  step="0.1"
                  className={`bg-white/5 border-white/10 ${
                    taxaWarning ? 'border-red-500/70 bg-red-500/5 text-red-400' : ''
                  }`}
                />
              </div>
              {taxaWarning && (
                <div className="mt-2 p-2 rounded-md bg-red-500/10 border border-red-500/30">
                  <p className="text-xs text-red-400 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    {taxaWarning}
                  </p>
                </div>
              )}
            </div>

            <div>
              <Label htmlFor="tempo_relacionamento">Tempo Relac. (meses)</Label>
              <Input
                id="tempo_relacionamento"
                type="number"
                value={formData.tempo_relacionamento || ''}
                onChange={(e) => handleNumberInput('tempo_relacionamento', e.target.value)}
                min="0"
                className="bg-white/5 border-white/10"
              />
            </div>
          </div>

          {/* Linha 3: Histórico */}
          <div className="grid grid-cols-4 gap-4">
            <div>
              <Label htmlFor="qtd_produtos_ativos">Produtos Ativos</Label>
              <Input
                id="qtd_produtos_ativos"
                type="number"
                value={formData.qtd_produtos_ativos || ''}
                onChange={(e) => handleNumberInput('qtd_produtos_ativos', e.target.value)}
                min="0"
                max="10"
                className="bg-white/5 border-white/10"
              />
            </div>

            <div>
              <Label htmlFor="qtd_atrasos_12m">Atrasos (12 meses)</Label>
              <Input
                id="qtd_atrasos_12m"
                type="number"
                value={formData.qtd_atrasos_12m || ''}
                onChange={(e) => handleNumberInput('qtd_atrasos_12m', e.target.value)}
                min="0"
                className="bg-white/5 border-white/10"
              />
            </div>

            <div>
              <Label htmlFor="genero">Gênero</Label>
              <Select value={formData.genero} onValueChange={(value) => handleInputChange('genero', value)}>
                <SelectTrigger className="bg-white/5 border-white/10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Masculino">Masculino</SelectItem>
                  <SelectItem value="Feminino">Feminino</SelectItem>
                  <SelectItem value="Outro">Outro</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="estado_civil">Estado Civil</Label>
              <Select value={formData.estado_civil} onValueChange={(value) => handleInputChange('estado_civil', value)}>
                <SelectTrigger className="bg-white/5 border-white/10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Solteiro">Solteiro</SelectItem>
                  <SelectItem value="Casado">Casado</SelectItem>
                  <SelectItem value="Divorciado">Divorciado</SelectItem>
                  <SelectItem value="Viúvo">Viúvo</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Linha 4: Localização e Educação */}
          <div className="grid grid-cols-4 gap-4">
            <div>
              <Label htmlFor="escolaridade">Escolaridade</Label>
              <Select value={formData.escolaridade} onValueChange={(value) => handleInputChange('escolaridade', value)}>
                <SelectTrigger className="bg-white/5 border-white/10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Fundamental">Fundamental</SelectItem>
                  <SelectItem value="Médio">Médio</SelectItem>
                  <SelectItem value="Superior">Superior</SelectItem>
                  <SelectItem value="Pós-Graduação">Pós-Graduação</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="regiao">Região</Label>
              <Select value={formData.regiao} onValueChange={(value) => handleInputChange('regiao', value)}>
                <SelectTrigger className="bg-white/5 border-white/10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Sudeste">Sudeste</SelectItem>
                  <SelectItem value="Sul">Sul</SelectItem>
                  <SelectItem value="Nordeste">Nordeste</SelectItem>
                  <SelectItem value="Centro-Oeste">Centro-Oeste</SelectItem>
                  <SelectItem value="Norte">Norte</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="uf">UF</Label>
              <Select value={formData.uf} onValueChange={(value) => handleInputChange('uf', value)}>
                <SelectTrigger className="bg-white/5 border-white/10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="max-h-[300px]">
                  <SelectItem value="AC">AC</SelectItem>
                  <SelectItem value="AL">AL</SelectItem>
                  <SelectItem value="AP">AP</SelectItem>
                  <SelectItem value="AM">AM</SelectItem>
                  <SelectItem value="BA">BA</SelectItem>
                  <SelectItem value="CE">CE</SelectItem>
                  <SelectItem value="DF">DF</SelectItem>
                  <SelectItem value="ES">ES</SelectItem>
                  <SelectItem value="GO">GO</SelectItem>
                  <SelectItem value="MA">MA</SelectItem>
                  <SelectItem value="MT">MT</SelectItem>
                  <SelectItem value="MS">MS</SelectItem>
                  <SelectItem value="MG">MG</SelectItem>
                  <SelectItem value="PA">PA</SelectItem>
                  <SelectItem value="PB">PB</SelectItem>
                  <SelectItem value="PR">PR</SelectItem>
                  <SelectItem value="PE">PE</SelectItem>
                  <SelectItem value="PI">PI</SelectItem>
                  <SelectItem value="RJ">RJ</SelectItem>
                  <SelectItem value="RN">RN</SelectItem>
                  <SelectItem value="RS">RS</SelectItem>
                  <SelectItem value="RO">RO</SelectItem>
                  <SelectItem value="RR">RR</SelectItem>
                  <SelectItem value="SC">SC</SelectItem>
                  <SelectItem value="SP">SP</SelectItem>
                  <SelectItem value="SE">SE</SelectItem>
                  <SelectItem value="TO">TO</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="porte_municipio">Porte do Município</Label>
              <Select value={formData.porte_municipio} onValueChange={(value) => handleInputChange('porte_municipio', value)}>
                <SelectTrigger className="bg-white/5 border-white/10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Metrópole">Metrópole</SelectItem>
                  <SelectItem value="Grande">Grande</SelectItem>
                  <SelectItem value="Médio">Médio</SelectItem>
                  <SelectItem value="Pequeno">Pequeno</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Linha 5: Produto e Canal */}
          <div className="grid grid-cols-4 gap-4">
            <div>
              <Label htmlFor="tipo_produto">Tipo de Produto</Label>
              <Select value={formData.tipo_produto} onValueChange={handleProdutoChange}>
                <SelectTrigger className="bg-white/5 border-white/10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="CDC">CDC (28-120% a.a.)</SelectItem>
                  <SelectItem value="Imobiliário">Imobiliário (10-15% a.a.)</SelectItem>
                  <SelectItem value="Cartão">Cartão (180-450% a.a.)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="canal_aquisicao">Canal de Aquisição</Label>
              <Select value={formData.canal_aquisicao} onValueChange={(value) => handleInputChange('canal_aquisicao', value)}>
                <SelectTrigger className="bg-white/5 border-white/10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="App">App</SelectItem>
                  <SelectItem value="Site">Site</SelectItem>
                  <SelectItem value="Agência">Agência</SelectItem>
                  <SelectItem value="Telefone">Telefone</SelectItem>
                  <SelectItem value="Parceiro">Parceiro</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="col-span-2 flex items-end">
              <Button
                onClick={handleAnalise}
                disabled={loading}
                className="w-full bg-primary hover:bg-primary/90 text-primary-foreground h-10 text-base font-semibold"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Analisando...
                  </>
                ) : (
                  'Realizar Análise'
                )}
              </Button>
            </div>
          </div>
        </div>
      </Card>

      {/* Resultado */}
      {error && (
        <Card className="p-6 bg-destructive/10 border-destructive/20">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-6 h-6 text-destructive" />
            <div>
              <h3 className="font-semibold text-destructive">Erro na Análise</h3>
              <p className="text-sm text-destructive/80">{error}</p>
            </div>
          </div>
        </Card>
      )}

      {resultado && (
        <div className="grid grid-cols-12 gap-6">
          {/* Card de Resultado Principal */}
          <div className="col-span-12">
            <Card className={`p-8 ${
              resultado.recommendation === 'Aprovar' ? 'bg-green-500/10 border-green-500/30' : 
              resultado.recommendation === 'Revisar' ? 'bg-yellow-500/10 border-yellow-500/30' : 
              'bg-red-500/10 border-red-500/30'
            }`}>
              <div className="flex items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                  <div className="flex-shrink-0">
                    {resultado.recommendation === 'Aprovar' ? (
                      <div className="w-24 h-24 rounded-full bg-green-500 flex items-center justify-center">
                        <CheckCircle2 className="w-16 h-16 text-white" />
                      </div>
                    ) : resultado.recommendation === 'Revisar' ? (
                      <div className="w-24 h-24 rounded-full bg-yellow-500 flex items-center justify-center">
                        <AlertCircle className="w-16 h-16 text-white" />
                      </div>
                    ) : (
                      <div className="w-24 h-24 rounded-full bg-red-500 flex items-center justify-center">
                        <XCircle className="w-16 h-16 text-white" />
                      </div>
                    )}
                  </div>
                  <div className="text-center">
                    <h2 className={`text-3xl font-bold mb-2 ${
                      resultado.recommendation === 'Aprovar' ? 'text-green-500' : 
                      resultado.recommendation === 'Revisar' ? 'text-yellow-500' : 
                      'text-red-500'
                    }`}>
                      {resultado.recommendation === 'Aprovar' ? 'CRÉDITO APROVADO' : resultado.recommendation === 'Revisar' ? 'CRÉDITO EM ANÁLISE' : 'CRÉDITO NEGADO'}
                    </h2>
                  </div>
                </div>
              </div>
              <div className="flex justify-center gap-12 mt-6">
                <div className="text-center">
                  <p className="text-sm text-muted-foreground mb-1">Probabilidade de Inadimplência</p>
                  <p className="text-2xl font-bold text-foreground">
                    {(resultado.probability * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-muted-foreground mb-1">Score de Risco</p>
                  <p className="text-2xl font-bold text-foreground">
                    {resultado.risk_score.toFixed(0)}
                  </p>
                </div>
              </div>
            </Card>
          </div>

          {/* Detalhes Adicionais */}
          <div className="col-span-12">
            <Card className="p-6 bg-[#1A1D2E]/80 backdrop-blur-xl border-white/5">
              <h3 className="text-lg font-bold text-foreground mb-4">Detalhes da Análise</h3>
              <div className="grid grid-cols-4 gap-4">
                <div className="p-4 rounded-lg bg-white/5">
                  <p className="text-sm text-muted-foreground mb-1">Valor Solicitado</p>
                  <p className="text-xl font-bold text-foreground">{formatCurrency(formData.valor)}</p>
                </div>
                <div className="p-4 rounded-lg bg-white/5">
                  <p className="text-sm text-muted-foreground mb-1">Prazo</p>
                  <p className="text-xl font-bold text-foreground">{formData.prazo} meses</p>
                </div>
                <div className="p-4 rounded-lg bg-white/5">
                  <p className="text-sm text-muted-foreground mb-1">Taxa de Juros</p>
                  <p className="text-xl font-bold text-foreground">{formData.taxa}% a.a.</p>
                </div>
                <div className="p-4 rounded-lg bg-white/5">
                  <p className="text-sm text-muted-foreground mb-1">Score de Crédito</p>
                  <p className="text-xl font-bold text-foreground">{formData.score_credito}</p>
                </div>
              </div>

              {/* Análise de Rentabilidade - Apenas para créditos aprovados */}
              {resultado.prediction === 0 && (() => {
                const rentabilidade = calcularRentabilidade(
                  formData.valor,
                  formData.prazo,
                  formData.taxa,
                  resultado.probability,
                  13.31
                );
                const riscoBACEN = classificarRiscoBACEN(resultado.probability);
                
                return (
                  <div className="mt-6 p-4 rounded-lg bg-green-500/10 border border-green-500/20">
                    <h4 className="text-sm font-bold text-green-500 mb-3 flex items-center gap-2">
                      <CheckCircle className="w-4 h-4" />
                      Análise de Rentabilidade (BACEN/CMN)
                    </h4>
                    <div className="space-y-3 text-xs text-muted-foreground">
                      <div className="grid grid-cols-2 gap-3">
                        <div className="p-3 rounded bg-white/5">
                          <p className="text-green-400 font-semibold mb-1">Receita de Juros</p>
                          <p className="text-foreground font-bold text-lg">
                            {formatCurrencyUtil(rentabilidade.receitaJuros)}
                          </p>
                          <p className="text-xs mt-1">Juros totais no período</p>
                        </div>
                        <div className="p-3 rounded bg-white/5">
                          <p className="text-amber-500 font-semibold mb-1">Custo de Captação</p>
                          <p className="text-foreground font-bold text-lg">
                            {formatCurrencyUtil(rentabilidade.custoCaptacao)}
                          </p>
                          <p className="text-xs mt-1">Baseado em CDI 13,31% a.a.</p>
                        </div>
                      </div>

                      <div className="p-3 rounded bg-white/5 mt-3">
                        <p className="text-blue-400 font-semibold mb-2">Composição do Resultado</p>
                        <div className="space-y-1">
                          <div className="flex justify-between">
                            <span>Receita de juros:</span>
                            <strong className="text-green-400">
                              +{formatCurrencyUtil(rentabilidade.receitaJuros)}
                            </strong>
                          </div>
                          <div className="flex justify-between">
                            <span>Custo de captação (CDI 13,31%):</span>
                            <strong className="text-red-400">
                              -{formatCurrencyUtil(rentabilidade.custoCaptacao)}
                            </strong>
                          </div>
                          <div className="flex justify-between">
                            <span>Provisão BACEN 2.682/99 (Nível {riscoBACEN.nivel}):</span>
                            <strong className="text-red-400">
                              -{formatCurrencyUtil(rentabilidade.provisaoBACEN)}
                            </strong>
                          </div>
                          <div className="flex justify-between">
                            <span>Custos operacionais (0,75%):</span>
                            <strong className="text-red-400">
                              -{formatCurrencyUtil(rentabilidade.custosOperacionais)}
                            </strong>
                          </div>
                          <div className="border-t border-white/10 mt-2 pt-2"></div>
                          <div className="flex justify-between text-base">
                            <span className="font-bold">Lucro Líquido Estimado:</span>
                            <strong className={`text-lg ${rentabilidade.lucroLiquido > 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {formatCurrencyUtil(rentabilidade.lucroLiquido)}
                            </strong>
                          </div>
                          <div className="flex justify-between mt-1">
                            <span>ROI sobre valor emprestado:</span>
                            <strong className={rentabilidade.roi > 0 ? 'text-green-400' : 'text-red-400'}>
                              {rentabilidade.roi.toFixed(2)}%
                            </strong>
                          </div>
                          <div className="flex justify-between mt-1">
                            <span>Taxa mínima rentável:</span>
                            <strong className="text-blue-400">
                              {rentabilidade.taxaMinimaRentavel.toFixed(2)}% a.a.
                            </strong>
                          </div>
                        </div>
                      </div>

                    <div className="p-3 rounded bg-blue-500/10 border border-blue-500/20">
                      <p className="text-blue-400 font-semibold mb-1">Fundamentação Técnica</p>
                      <ul className="space-y-1 ml-4 list-disc text-xs">
                        <li>Custo de captação baseado em CDI (BACEN: 13,31% a.a. em nov/2025)</li>
                        <li>Provisão calculada conforme Resolução BACEN 2.682/99 - Nível {riscoBACEN.nivel}</li>
                        <li>Custos operacionais estimados em 0,75% (média mercado)</li>
                        <li>Spread bancário conforme dados do Departamento Econômico/BACEN</li>
                        <li>Taxa mínima calculada para garantir ROI positivo: {rentabilidade.taxaMinimaRentavel.toFixed(2)}% a.a.</li>
                      </ul>
                    </div>
                  </div>
                </div>
                );
              })()}

              {/* Análise Detalhada BACEN - Apenas para créditos negados */}
              {resultado.prediction === 1 && (
                <div className="mt-6 p-4 rounded-lg bg-red-500/10 border border-red-500/20">
                  <h4 className="text-sm font-bold text-red-500 mb-3 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4" />
                    Análise Detalhada de Risco (BACEN 2682)
                  </h4>
                  <div className="space-y-3 text-xs text-muted-foreground">
                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-3 rounded bg-white/5">
                        <p className="text-red-400 font-semibold mb-1">Score de Crédito</p>
                        <p className="text-foreground font-bold text-lg">{formData.score_credito}</p>
                        <p className="text-xs mt-1">
                          {formData.score_credito < 300 ? 'Crítico - Risco AA (>50%)' :
                           formData.score_credito < 500 ? 'Muito Alto - Risco A (30-50%)' :
                           formData.score_credito < 600 ? 'Alto - Risco B (10-30%)' : 'Médio'}
                        </p>
                      </div>
                      <div className="p-3 rounded bg-white/5">
                        <p className="text-red-400 font-semibold mb-1">Probabilidade de Inadimplência</p>
                        <p className="text-foreground font-bold text-lg">{(resultado.probability * 100).toFixed(1)}%</p>
                        <p className="text-xs mt-1">
                          {resultado.probability > 0.30 ? 'Acima do limite aceitável (30%)' : 
                           resultado.probability > 0.10 ? 'Dentro do limite de revisão (10-30%)' : 
                           'Dentro do limite aceitável (<10%)'}
                        </p>
                      </div>
                    </div>

                    <div className="p-3 rounded bg-white/5 mt-3">
                      <p className="text-red-400 font-semibold mb-2">Motivos da Rejeição</p>
                      <ul className="space-y-1 ml-4 list-disc">
                        {formData.score_credito < 600 && (
                          <li>Score de crédito <strong>{formData.score_credito}</strong> abaixo do mínimo regulatório (600 pontos)</li>
                        )}
                        {resultado.probability > 0.5 && (
                          <li>Probabilidade de inadimplência de <strong>{(resultado.probability * 100).toFixed(1)}%</strong> excede limite de <strong>30%</strong></li>
                        )}
                        {formData.qtd_atrasos_12m > 2 && (
                          <li>Histórico de <strong>{formData.qtd_atrasos_12m} atrasos</strong> nos últimos 12 meses</li>
                        )}
                        {formData.valor > formData.renda_mensal * 5 && (
                          <li>Comprometimento de renda: <strong>{((formData.valor / formData.prazo) / formData.renda_mensal * 100).toFixed(1)}%</strong> (limite: 30%)</li>
                        )}
                      </ul>
                    </div>

                    <div className="p-3 rounded bg-white/5">
                      <p className="text-amber-500 font-semibold mb-2">Simulação de Perda Esperada (BACEN)</p>
                      <div className="space-y-1">
                        <p>Valor solicitado: <strong className="text-foreground">{formatCurrency(formData.valor)}</strong></p>
                        <p>Perda esperada (PD x EAD): <strong className="text-red-400">{formatCurrency(formData.valor * resultado.probability)}</strong></p>
                        <p>Provisão necessária: <strong className="text-foreground">{formatCurrency(formData.valor * resultado.probability * 1.5)}</strong></p>
                        <p className="text-xs mt-2 text-muted-foreground">
                          * Cálculo baseado na Resolução BACEN 2.682/99 (Classificação de Risco)
                        </p>
                      </div>
                    </div>

                    <div className="p-3 rounded bg-green-500/10 border border-green-500/20">
                      <p className="text-green-500 font-semibold mb-1">Economia com Rejeição</p>
                      <p className="text-foreground text-lg font-bold">{formatCurrency(formData.valor * resultado.probability)}</p>
                      <p className="text-xs mt-1">Perda evitada ao negar crédito de alto risco</p>
                    </div>
                  </div>
                </div>
              )}
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
