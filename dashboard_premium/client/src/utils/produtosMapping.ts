/**
 * Mapeamento entre nomes de produtos exibidos e valores aceitos pelo modelo
 * 
 * O modelo foi treinado com valores SEM ACENTOS
 * Mas a API/interface usa valores COM ACENTOS
 * 
 * Este arquivo faz a conversão correta
 */

export const PRODUTOS_DISPLAY_TO_API: Record<string, string> = {
  'CDC': 'CDC',
  'Pessoal': 'Pessoal',
  'Imobiliário': 'Imobiliario', // Sem acento
  'Cartão': 'Cartao', // Sem til
};

export const PRODUTOS_API_TO_DISPLAY: Record<string, string> = {
  'CDC': 'CDC',
  'Pessoal': 'Pessoal',
  'Imobiliario': 'Imobiliário',
  'Cartao': 'Cartão',
};

/**
 * Converte nome de produto da interface para valor aceito pela API/modelo
 */
export function produtoParaAPI(produtoDisplay: string): string {
  return PRODUTOS_DISPLAY_TO_API[produtoDisplay] || produtoDisplay;
}

/**
 * Converte valor da API para nome de exibição
 */
export function produtoParaDisplay(produtoAPI: string): string {
  return PRODUTOS_API_TO_DISPLAY[produtoAPI] || produtoAPI;
}

/**
 * Lista de produtos disponíveis no modelo
 * (apenas os que realmente funcionam)
 */
export const PRODUTOS_DISPONIVEIS = [
  { display: 'CDC', api: 'CDC' },
  { display: 'Pessoal', api: 'Pessoal' },
  { display: 'Imobiliário', api: 'Imobiliario' },
  { display: 'Cartão', api: 'Cartao' },
];
