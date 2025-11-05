/**
 * Cálculo Automático de Taxa de Juros
 * Baseado em BACEN, Santander e análise de risco
 * 
 * ATUALIZAÇÃO: Novembro 2025
 * - Dados oficiais do BACEN (out/2025)
 * - Taxas reais praticadas pelo Santander
 * - Cálculo de taxa mínima rentável integrado
 */

import { getTaxaMinimaProduto, getTaxaMediaProduto, getTaxaSantander } from './taxasProdutos';

/**
 * Calcula taxa de juros automaticamente baseada em múltiplos fatores
 * Retorna taxa sugerida + taxa mínima rentável
 */
export function calcularTaxaAutomatica(params: {
  tipoProduto: string;
  valor: number;
  score: number;
  prazo: number;
  renda: number;
  probabilidadeInadimplencia?: number; // Opcional: se vier do modelo ML
}): {
  taxaSugerida: number;
  taxaMinima: number;
  taxaMaxima: number;
  taxaMinimaRentavel: number;
  justificativa: string;
} {
  const { tipoProduto, valor, score, prazo, renda, probabilidadeInadimplencia } = params;

  // 1. Taxa base do Santander (referência oficial)
  const taxaSantander = getTaxaSantander(tipoProduto);
  const taxaMinimaProduto = getTaxaMinimaProduto(tipoProduto);
  const taxaMediaProduto = getTaxaMediaProduto(tipoProduto);

  // 2. Fator de risco baseado no score (0.7 a 1.5)
  const fatorRiscoScore = calcularFatorRiscoScore(score);

  // 3. Fator de valor (valores maiores = taxas menores)
  const fatorValor = calcularFatorValor(valor, tipoProduto);

  // 4. Fator de prazo (prazos maiores = taxas maiores)
  const fatorPrazo = calcularFatorPrazo(prazo, tipoProduto);

  // 5. Fator de comprometimento de renda
  const parcelaMensal = calcularParcelaMensal(valor, taxaSantander, prazo);
  const fatorComprometimento = calcularFatorComprometimento(parcelaMensal, renda);

  // 6. Calcular taxa mínima rentável PRIMEIRO (considerando risco)
  const probInad = probabilidadeInadimplencia || estimarProbabilidadeInadimplencia(score);
  const taxaMinimaRentavel = calcularTaxaMinimaRentavel(valor, prazo, probInad);

  // Cálculo da taxa sugerida baseada na taxa do Santander
  // REALISTA: Fatores refletem risco real
  let taxaSugerida = taxaSantander * fatorRiscoScore * fatorValor * fatorPrazo * fatorComprometimento;

  // Garantir que a taxa sugerida seja no mínimo a taxa mínima rentável
  taxaSugerida = Math.max(taxaSugerida, taxaMinimaRentavel);

  // Garantir que está dentro dos limites do produto
  const taxaMaximaProduto = taxaMediaProduto * 2.0;
  taxaSugerida = Math.max(taxaMinimaProduto, Math.min(taxaSugerida, taxaMaximaProduto));

  // Arredondar para 0.5%
  taxaSugerida = Math.round(taxaSugerida * 2) / 2;

  // VALIDAÇÃO FINAL: SEMPRE garantir que taxa >= taxa mínima rentável
  // Isso é CRÍTICO para evitar operações com prejuízo
  taxaSugerida = Math.max(taxaSugerida, Math.ceil(taxaMinimaRentavel * 2) / 2);

  // Justificativa detalhada
  const justificativa = gerarJustificativa({
    tipoProduto,
    score,
    valor,
    prazo,
    fatorRiscoScore,
    fatorValor,
    fatorPrazo,
    fatorComprometimento,
    taxaSugerida,
    taxaMinimaProduto,
    taxaSantander,
    taxaMinimaRentavel,
    probabilidadeInadimplencia: probInad
  });

  return {
    taxaSugerida,
    taxaMinima: taxaMinimaProduto,
    taxaMaxima: taxaMaximaProduto,
    taxaMinimaRentavel,
    justificativa
  };
}

/**
 * Calcula fator de risco baseado no score de crédito
 * Score alto = fator baixo (taxa menor)
 * Score baixo = fator alto (taxa maior)
 * REALISTA: Baseado em práticas bancárias
 */
function calcularFatorRiscoScore(score: number): number {
  if (score >= 800) return 0.65; // Excelente: -35% da taxa
  if (score >= 700) return 0.80; // Bom: -20% da taxa
  if (score >= 600) return 1.00; // Regular: taxa padrão
  if (score >= 500) return 1.35; // Ruim: +35% da taxa
  if (score >= 400) return 1.70; // Muito ruim: +70% da taxa (inviável)
  return 2.00; // Péssimo: +100% da taxa (inviável)
}

/**
 * Calcula fator baseado no valor solicitado
 * Valores maiores geralmente têm taxas menores (economia de escala)
 */
function calcularFatorValor(valor: number, tipoProduto: string): number {
  // Imobiliário: valores muito altos, fator menor
  if (tipoProduto === 'Imobiliário') {
    if (valor >= 500000) return 0.85;
    if (valor >= 300000) return 0.90;
    if (valor >= 150000) return 0.95;
    return 1.00;
  }

  // CDC e Pessoal: valores médios
  if (tipoProduto === 'CDC' || tipoProduto === 'Pessoal') {
    if (valor >= 50000) return 0.90;
    if (valor >= 30000) return 0.95;
    if (valor >= 15000) return 1.00;
    if (valor >= 5000) return 1.05;
    return 1.10; // Valores muito baixos: taxa maior
  }

  // Cartão: valor não afeta muito
  if (tipoProduto === 'Cartao') {
    return 1.00;
  }

  return 1.00;
}

/**
 * Calcula fator baseado no prazo
 * Prazos maiores = risco maior = taxa maior
 */
function calcularFatorPrazo(prazo: number, tipoProduto: string): number {
  // Imobiliário: prazos longos são normais
  if (tipoProduto === 'Imobiliário') {
    if (prazo >= 360) return 1.00;
    if (prazo >= 240) return 0.95;
    if (prazo >= 180) return 0.90;
    return 0.85; // Prazos curtos: taxa menor
  }

  // CDC: prazo padrão 12-36 meses
  if (tipoProduto === 'CDC' || tipoProduto === 'Pessoal') {
    if (prazo >= 48) return 1.15;
    if (prazo >= 36) return 1.10;
    if (prazo >= 24) return 1.05;
    if (prazo >= 12) return 1.00;
    return 0.95;
  }

  // Cartão: rotativo, prazo curto
  if (tipoProduto === 'Cartao') {
    if (prazo >= 24) return 1.10;
    if (prazo >= 12) return 1.00;
    return 0.95;
  }

  return 1.00;
}

/**
 * Calcula fator baseado no comprometimento de renda
 */
function calcularFatorComprometimento(parcela: number, renda: number): number {
  const comprometimento = (parcela / renda) * 100;

  if (comprometimento >= 50) return 1.30; // Alto risco
  if (comprometimento >= 40) return 1.20;
  if (comprometimento >= 30) return 1.10;
  if (comprometimento >= 20) return 1.00;
  return 0.95; // Baixo comprometimento: pode dar desconto
}

/**
 * Calcula parcela mensal aproximada
 */
function calcularParcelaMensal(valor: number, taxaAnual: number, prazo: number): number {
  const taxaMensal = taxaAnual / 100 / 12;
  if (taxaMensal === 0) return valor / prazo;
  
  const parcela = valor * (taxaMensal * Math.pow(1 + taxaMensal, prazo)) / 
                  (Math.pow(1 + taxaMensal, prazo) - 1);
  
  return parcela;
}

/**
 * Estima probabilidade de inadimplência baseada no score
 * REALISTA: Baseado em práticas bancárias reais
 * Threshold de aprovação: 30% (BACEN)
 */
function estimarProbabilidadeInadimplencia(score: number): number {
  // Estimativas realistas baseadas em dados bancários
  if (score >= 800) return 0.02; // 2% - Excelente
  if (score >= 700) return 0.05; // 5% - Bom
  if (score >= 600) return 0.12; // 12% - Regular
  if (score >= 500) return 0.28; // 28% - Ruim (limite de aprovação)
  if (score >= 400) return 0.50; // 50% - Muito Ruim (NEGAR)
  return 0.70; // 70% - Péssimo (NEGAR)
}

/**
 * Calcula taxa mínima rentável para o banco
 * Baseado em: custo de captação (CDI), provisão BACEN, custos operacionais
 */
function calcularTaxaMinimaRentavel(
  valor: number,
  prazo: number,
  probabilidadeInadimplencia: number
): number {
  const prazoAnos = prazo / 12;
  const taxaCDI = 13.31; // CDI atual (out/2025)
  
  // Custos que precisam ser cobertos
  const custoCaptacao = valor * (taxaCDI / 100) * prazoAnos;
  const provisaoBACEN = valor * probabilidadeInadimplencia * 1.5; // Provisão BACEN realista
  const custosOperacionais = valor * 0.0075; // 0.75% custos operacionais
  const margemMinima = 5; // 5% de margem mínima desejada
  const margemDesejada = valor * (margemMinima / 100);
  
  const receitaNecessaria = custoCaptacao + provisaoBACEN + custosOperacionais + margemDesejada;
  
  // Taxa mínima = (Receita Necessária / Valor) / Prazo em Anos * 100
  const taxaMinima = (receitaNecessaria / valor / prazoAnos) * 100;
  
  return Math.ceil(taxaMinima * 10) / 10; // Arredondar para cima com 1 casa decimal
}

/**
 * Gera justificativa detalhada da taxa sugerida
 */
function gerarJustificativa(params: {
  tipoProduto: string;
  score: number;
  valor: number;
  prazo: number;
  fatorRiscoScore: number;
  fatorValor: number;
  fatorPrazo: number;
  fatorComprometimento: number;
  taxaSugerida: number;
  taxaMinimaProduto: number;
  taxaSantander: number;
  taxaMinimaRentavel: number;
  probabilidadeInadimplencia: number;
}): string {
  const {
    tipoProduto,
    score,
    valor,
    prazo,
    fatorRiscoScore,
    fatorValor,
    fatorPrazo,
    fatorComprometimento,
    taxaSugerida,
    taxaMinimaProduto,
    taxaSantander,
    taxaMinimaRentavel,
    probabilidadeInadimplencia
  } = params;

  let justificativa = `Taxa calculada automaticamente:\n\n`;

  // Risco estimado
  justificativa += `• Risco estimado: ${(probabilidadeInadimplencia * 100).toFixed(1)}% de inadimplência\n`;
  justificativa += `• Taxa mínima rentável: ${taxaMinimaRentavel.toFixed(1)}% a.a.\n\n`;

  // Taxa base
  justificativa += `• Taxa média ${tipoProduto}: ${taxaSantander.toFixed(1)}% a.a. (BACEN/Santander)\n`;

  // Score
  if (fatorRiscoScore < 1.0) {
    justificativa += `• Score ${score}: Excelente (-${((1 - fatorRiscoScore) * 100).toFixed(0)}%)\n`;
  } else if (fatorRiscoScore > 1.0) {
    justificativa += `• Score ${score}: Risco padrão\n`;
  } else {
    justificativa += `• Score ${score}: Risco padrão\n`;
  }

  // Valor
  if (fatorValor < 1.0) {
    justificativa += `• Valor R$ ${valor.toLocaleString('pt-BR')}: Alto valor (-${((1 - fatorValor) * 100).toFixed(0)}%)\n`;
  } else if (fatorValor > 1.0) {
    justificativa += `• Valor R$ ${valor.toLocaleString('pt-BR')}: Baixo valor (+${((fatorValor - 1) * 100).toFixed(0)}%)\n`;
  }

  // Prazo
  if (fatorPrazo < 1.0) {
    justificativa += `• Prazo ${prazo} meses: Curto prazo (-${((1 - fatorPrazo) * 100).toFixed(0)}%)\n`;
  } else if (fatorPrazo > 1.0) {
    justificativa += `• Prazo ${prazo} meses: Longo prazo (+${((fatorPrazo - 1) * 100).toFixed(0)}%)\n`;
  }

  // Comprometimento
  if (fatorComprometimento > 1.0) {
    justificativa += `• Comprometimento de renda elevado (+${((fatorComprometimento - 1) * 100).toFixed(0)}%)\n`;
  }

  justificativa += `\n**Taxa sugerida: ${taxaSugerida.toFixed(1)}% a.a.**\n`;
  justificativa += `(Mínima produto: ${taxaMinimaProduto.toFixed(1)}% | Mínima rentável: ${taxaMinimaRentavel.toFixed(1)}%)`;

  return justificativa;
}

/**
 * Calcula range de taxas aceitáveis
 */
export function calcularRangeTaxas(tipoProduto: string, score: number): {
  minima: number;
  recomendada: number;
  maxima: number;
} {
  const taxaMinima = getTaxaMinimaProduto(tipoProduto);
  const taxaSantander = getTaxaSantander(tipoProduto);
  const fatorRisco = calcularFatorRiscoScore(score);

  return {
    minima: taxaMinima,
    recomendada: Math.round(taxaSantander * fatorRisco * 2) / 2,
    maxima: taxaSantander * 2.0
  };
}
