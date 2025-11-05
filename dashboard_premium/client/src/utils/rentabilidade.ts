/**
 * Utilitários para cálculo de rentabilidade bancária
 * Baseado em Resolução BACEN 2.682/99 e práticas do mercado
 */

export interface CalculoRentabilidade {
  receitaJuros: number;
  custoCaptacao: number;
  provisaoBACEN: number;
  custosOperacionais: number;
  lucroLiquido: number;
  roi: number;
  taxaMinimaRentavel: number;
  aprovavel: boolean;
}

/**
 * Calcula a taxa mínima de juros para garantir ROI positivo
 * 
 * @param valor - Valor do empréstimo
 * @param prazo - Prazo em meses
 * @param probabilidadeInadimplencia - Probabilidade de inadimplência (0-1)
 * @param taxaCDI - Taxa CDI anual (padrão: 13.31%)
 * @param margemMinima - Margem mínima de lucro desejada (padrão: 5%)
 * @returns Taxa mínima anual em percentual
 */
export function calcularTaxaMinimaRentavel(
  valor: number,
  prazo: number,
  probabilidadeInadimplencia: number,
  taxaCDI: number = 13.31,
  margemMinima: number = 5
): number {
  const prazoAnos = prazo / 12;
  
  // Custos que precisam ser cobertos
  const custoCaptacao = valor * (taxaCDI / 100) * prazoAnos;
  const provisaoBACEN = valor * probabilidadeInadimplencia * 1.5; // Provisão BACEN realista
  const custosOperacionais = valor * 0.0075; // 0.75% custos operacionais
  const margemDesejada = valor * (margemMinima / 100);
  
  const receitaNecessaria = custoCaptacao + provisaoBACEN + custosOperacionais + margemDesejada;
  
  // Taxa mínima = (Receita Necessária / Valor) / Prazo em Anos * 100
  const taxaMinima = (receitaNecessaria / valor / prazoAnos) * 100;
  
  return Math.ceil(taxaMinima * 10) / 10; // Arredondar para cima com 1 casa decimal
}

/**
 * Calcula a rentabilidade completa de uma operação de crédito
 * 
 * @param valor - Valor do empréstimo
 * @param prazo - Prazo em meses
 * @param taxa - Taxa de juros anual
 * @param probabilidadeInadimplencia - Probabilidade de inadimplência (0-1)
 * @param taxaCDI - Taxa CDI anual (padrão: 13.31%)
 * @returns Objeto com todos os cálculos de rentabilidade
 */
export function calcularRentabilidade(
  valor: number,
  prazo: number,
  taxa: number,
  probabilidadeInadimplencia: number,
  taxaCDI: number = 13.31
): CalculoRentabilidade {
  const prazoAnos = prazo / 12;
  
  // Receitas
  const receitaJuros = valor * (taxa / 100) * prazoAnos;
  
  // Custos
  const custoCaptacao = valor * (taxaCDI / 100) * prazoAnos;
  const provisaoBACEN = valor * probabilidadeInadimplencia * 1.5; // Provisão BACEN realista
  const custosOperacionais = valor * 0.0075; // 0.75% custos operacionais
  
  // Lucro
  const lucroLiquido = receitaJuros - custoCaptacao - provisaoBACEN - custosOperacionais;
  
  // ROI
  const roi = (lucroLiquido / valor) * 100;
  
  // Taxa mínima para ROI positivo
  const taxaMinimaRentavel = calcularTaxaMinimaRentavel(valor, prazo, probabilidadeInadimplencia, taxaCDI);
  
  // Aprovável se ROI > 0 e taxa >= taxa mínima
  const aprovavel = roi > 0 && taxa >= taxaMinimaRentavel;
  
  return {
    receitaJuros,
    custoCaptacao,
    provisaoBACEN,
    custosOperacionais,
    lucroLiquido,
    roi,
    taxaMinimaRentavel,
    aprovavel,
  };
}

/**
 * Formata valor em reais
 */
export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value);
}

/**
 * Classifica o risco BACEN baseado na probabilidade de inadimplência
 * Resolução BACEN 2.682/99
 */
export function classificarRiscoBACEN(probabilidade: number): {
  nivel: string;
  provisao: number;
  descricao: string;
} {
  if (probabilidade <= 0.01) {
    return { nivel: 'AA', provisao: 0, descricao: 'Risco mínimo' };
  } else if (probabilidade <= 0.03) {
    return { nivel: 'A', provisao: 0.5, descricao: 'Risco baixo' };
  } else if (probabilidade <= 0.10) {
    return { nivel: 'B', provisao: 1, descricao: 'Risco moderado baixo' };
  } else if (probabilidade <= 0.30) {
    return { nivel: 'C', provisao: 3, descricao: 'Risco moderado' };
  } else if (probabilidade <= 0.50) {
    return { nivel: 'D', provisao: 10, descricao: 'Risco moderado alto' };
  } else if (probabilidade <= 0.70) {
    return { nivel: 'E', provisao: 30, descricao: 'Risco alto' };
  } else if (probabilidade <= 0.90) {
    return { nivel: 'F', provisao: 50, descricao: 'Risco muito alto' };
  } else if (probabilidade <= 0.99) {
    return { nivel: 'G', provisao: 70, descricao: 'Risco crítico' };
  } else {
    return { nivel: 'H', provisao: 100, descricao: 'Perda total' };
  }
}
