/**
 * Taxas Mínimas por Tipo de Produto
 * Baseado em dados de mercado e práticas do setor financeiro
 * 
 * Fontes:
 * - Fonte 1: Relatório de Taxas de Juros (out/2025)
 * - Fonte 2: Dados oficiais do setor (out/2025)
 * - CMN: Resolução 2.682/99
 * 
 * ATUALIZAÇÃO: Novembro 2025 - Dados coletados diretamente do site do BACEN
 */

export interface TaxaProduto {
  codigo: string;
  nome: string;
  taxaMinima: number;
  taxaMedia: number;
  taxaMaxima: number;
  taxaSantander: number; // Taxa praticada pelo Santander
  descricao: string;
  observacoes: string;
  fonteBACEN: string;
}

/**
 * Taxas por tipo de produto - DADOS DE MERCADO
 * Valores em % ao ano
 * 
 * Período de referência: 14/10/2025 a 20/10/2025
 * Fonte: Dados de mercado e relatórios setoriais
 */
export const TAXAS_POR_PRODUTO: Record<string, TaxaProduto> = {
  'CDC': {
    codigo: 'CDC',
    nome: 'Crédito Direto ao Consumidor (CDC)',
    taxaMinima: 25.0,  // Ajustado para refletir realidade do mercado
    taxaMedia: 35.0,   // Média ponderada do mercado
    taxaMaxima: 75.0,  // Limite superior observado
    taxaSantander: 29.03, // Taxa oficial do banco (out/2025)
    descricao: 'Financiamento de bens duráveis (eletrodomésticos, eletrônicos, móveis)',
    observacoes: 'Taxa praticada: 29,03% a.a. (2,15% a.m.). Faixa de mercado: 2,48% a 75% a.a.',
    fonteBACEN: 'Modalidade: Aquisição de outros bens - Pré-fixado (out/2025) - Fonte: Setor Financeiro'
  },

  'Pessoal': {
    codigo: 'Pessoal',
    nome: 'Crédito Pessoal Não Consignado',
    taxaMinima: 28.0,  // Baseado na faixa competitiva do mercado
    taxaMedia: 35.0,   // Média do mercado
    taxaMaxima: 60.0,  // Limite superior razoável
    taxaSantander: 31.56, // Taxa oficial do banco (out/2025)
    descricao: 'Empréstimo pessoal sem garantia ou desconto em folha',
    observacoes: 'Taxa praticada: 31,56% a.a. (2,31% a.m.). Faixa de mercado: 1,07% a 50%+ a.a.',
    fonteBACEN: 'Modalidade: Crédito pessoal não consignado - Pré-fixado (out/2025) - Fonte: Setor Financeiro'
  },

  'Imobiliário': {
    codigo: 'Imobiliário',
    nome: 'Crédito Imobiliário',
    taxaMinima: 8.0,   // Mínimo do mercado
    taxaMedia: 10.0,   // Média do mercado
    taxaMaxima: 16.0,  // Limite superior
    taxaSantander: 10.0, // Estimativa baseada na média do mercado
    descricao: 'Financiamento de imóveis com garantia hipotecária',
    observacoes: 'Taxa mais baixa devido à garantia real (imóvel). Faixa de mercado: 7,90% a 16% a.a. (IPCA + taxa fixa).',
    fonteBACEN: 'Modalidade: Financiamento imobiliário com taxas de mercado - IPCA (set/2025)'
  },

  'Cartao': {
    codigo: 'Cartão',
    nome: 'Cartão de Crédito Rotativo',
    taxaMinima: 250.0, // Mínimo realista do mercado
    taxaMedia: 350.0,  // Média do mercado
    taxaMaxima: 500.0, // Limite superior
    taxaSantander: 434.75, // Taxa oficial do banco (BACEN out/2025)
    descricao: 'Crédito rotativo do cartão de crédito',
    observacoes: 'Taxa praticada: 434,75% a.a. (15% a.m.). Taxa mais alta do mercado. Uso emergencial apenas.',
    fonteBACEN: 'Modalidade: Cartão de crédito - rotativo total - Pré-fixado (out/2025) - Fonte: Setor Financeiro'
  }
};

/**
 * Obtém a taxa mínima para um tipo de produto
 */
export function getTaxaMinimaProduto(tipoProduto: string): number {
  const produto = TAXAS_POR_PRODUTO[tipoProduto];
  if (!produto) {
    console.warn(`Produto não encontrado: ${tipoProduto}. Usando taxa mínima padrão de 28%.`);
    return 28.0; // Taxa mínima padrão (CDC)
  }
  return produto.taxaMinima;
}

/**
 * Obtém a taxa média para um tipo de produto
 */
export function getTaxaMediaProduto(tipoProduto: string): number {
  const produto = TAXAS_POR_PRODUTO[tipoProduto];
  if (!produto) {
    return 24.0; // Taxa média padrão
  }
  return produto.taxaMedia;
}

/**
 * Obtém a taxa praticada pelo Santander para um tipo de produto
 */
export function getTaxaSantander(tipoProduto: string): number {
  const produto = TAXAS_POR_PRODUTO[tipoProduto];
  if (!produto) {
    return getTaxaMediaProduto(tipoProduto);
  }
  return produto.taxaSantander;
}

/**
 * Obtém informações completas do produto
 */
export function getInfoProduto(tipoProduto: string): TaxaProduto | null {
  return TAXAS_POR_PRODUTO[tipoProduto] || null;
}

/**
 * Valida se a taxa está dentro do range permitido para o produto
 * IMPORTANTE: Agora permite qualquer taxa, mas avisa se está fora do recomendado
 */
export function validarTaxaProduto(tipoProduto: string, taxa: number): {
  valida: boolean;
  mensagem: string;
  taxaCorrigida?: number;
  nivel: 'ok' | 'aviso' | 'erro';
} {
  const produto = TAXAS_POR_PRODUTO[tipoProduto];
  
  if (!produto) {
    return {
      valida: false,
      mensagem: `Tipo de produto inválido: ${tipoProduto}`,
      nivel: 'erro'
    };
  }

  // Permite qualquer taxa, mas avisa se está abaixo da mínima recomendada
  if (taxa < produto.taxaMinima) {
    return {
      valida: true, // Permite, mas avisa
      mensagem: `Taxa abaixo da mínima recomendada para ${produto.nome}. Recomendado: ${produto.taxaMinima}% a.a. (Taxa praticada: ${produto.taxaSantander}% a.a.)`,
      taxaCorrigida: produto.taxaSantander, // Sugere a taxa praticada pelo banco
      nivel: 'aviso'
    };
  }

  if (taxa > produto.taxaMaxima) {
    return {
      valida: true,
      mensagem: `Taxa acima do usual para ${produto.nome}. Máximo típico: ${produto.taxaMaxima}% a.a.`,
      nivel: 'aviso'
    };
  }

  return {
    valida: true,
    mensagem: 'Taxa dentro da faixa recomendada',
    nivel: 'ok'
  };
}

/**
 * Lista todos os produtos disponíveis
 */
export function listarProdutos(): TaxaProduto[] {
  return Object.values(TAXAS_POR_PRODUTO);
}

/**
 * Sugere a melhor taxa para o produto (taxa praticada pelo banco)
 */
export function sugerirTaxa(tipoProduto: string): number {
  return getTaxaSantander(tipoProduto);
}
