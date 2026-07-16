<div align="center">

# 📊 A/B Test e Elasticidade Preço-Demanda

### Segmento: Consignado Privado

<br>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Jupyter](https://img.shields.io/badge/Jupyter-F37626?style=for-the-badge&logo=jupyter&logoColor=white)](https://jupyter.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0+-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![NumPy](https://img.shields.io/badge/NumPy-1.24+-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org/)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-3.7+-11557c?style=for-the-badge&logo=matplotlib&logoColor=white)](https://matplotlib.org/)
[![SciPy](https://img.shields.io/badge/SciPy-1.10+-8CAAE6?style=for-the-badge&logo=scipy&logoColor=white)](https://scipy.org/)

<br>

[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/felipesbonatti/pricing-ab-test-elasticity)
[![Repo Size](https://img.shields.io/github/repo-size/felipesbonatti/pricing-ab-test-elasticity?style=for-the-badge)](https://github.com/felipesbonatti/pricing-ab-test-elasticity)
[![Last Commit](https://img.shields.io/github/last-commit/felipesbonatti/pricing-ab-test-elasticity?style=for-the-badge)](https://github.com/felipesbonatti/pricing-ab-test-elasticity/commits/main)

</div>

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Demonstração dos Resultados](#-demonstração-dos-resultados)
- [Objetivo e Valor de Negócio](#-objetivo-e-valor-de-negócio)
- [Tarefa 1 — Teste A/B](#-tarefa-1--teste-ab)
- [Tarefa 2 — Elasticidade Preço-Demanda](#-tarefa-2--elasticidade-preço-demanda)
- [Limitações e Leitura Correta dos Resultados](#️-limitações-e-leitura-correta-dos-resultados)
- [Recomendações](#-recomendações)
- [Estrutura do Repositório](#-estrutura-do-repositório)
- [Como Reproduzir](#️-como-reproduzir)
- [Decisões Metodológicas](#-decisões-metodológicas)
- [Roadmap](#-roadmap)

---

## 🎯 Visão Geral

> **Análise quantitativa de pricing para o segmento de Consignado Privado, combinando um experimento A/B controlado (2.200 ofertas) com um modelo de elasticidade preço-demanda em painel observacional (105 semanas). A análise aplica erros-padrão cluster-robust, correção de Bonferroni e cálculo explícito de poder estatístico, entregando recomendações de negócio acompanhadas de suas devidas ressalvas metodológicas.**

### Destaques

<div align="center">

| **Experimento A/B** | **Elasticidade** | **Rigor Estatístico** | **Recomendação** |
|:---:|:---:|:---:|:---:|
| 2.200 ofertas | -1,03 | Cluster-robust | Não adotar o corte |
| Controle vs. tratamento | IC 95% [-1,18; -0,89] | Correção de Bonferroni | Nova taxa intermediária |
| Receita **-23,5%** (p=0,014) | Unitária, associacional | MDE explícito | Teste segmentado |

</div>

---

## 📋 Demonstração dos Resultados

### Teste A/B — Comparação de Taxas

<div align="center">

![Gráficos do Teste A/B](charts_ab.png)

**Comparação entre grupos controle (2,40% a.m.) e tratamento (2,20% a.m.)**

</div>

### Elasticidade Preço-Demanda

<div align="center">

![Gráficos de Elasticidade](charts_elasticidade.png)

**Modelo log-log com erro-padrão cluster-robust por semana**

</div>

---

## 🎯 Objetivo e Valor de Negócio

Duas perguntas de negócio sobre pricing no segmento de Consignado Privado:

1. **Um corte de taxa aumenta a conversão o suficiente para compensar a receita perdida por oferta?**
2. **Qual a sensibilidade da demanda a variações de taxa, e ela varia por canal ou UF?**

<div align="center">

| Métrica | Resultado | Impacto no Negócio |
|:---|:---|:---|
| **Decisão do A/B** | Tratamento reduziu receita em 23,5% | O corte de taxa não gera ganho de aceite suficiente para compensar a queda de receita por oferta. |
| **Elasticidade geral** | -1,03 (IC 95%: -1,18 a -0,89) | Demanda sensível a preço — mas leitura associacional, não causal (ver seção de limitações). |
| **Rigor estatístico** | Erro-padrão cluster-robust + Bonferroni | Evita falsos positivos e leituras de heterogeneidade que não se sustentam com o erro-padrão correto. |
| **Poder estatístico** | MDE inadimplência ≈ 3,6 p.p. | "Não significativo" é interpretado como "sem evidência suficiente", não como "equivalência". |
| **Recomendação final** | Manter taxa atual e testar 2,30% a.m. | Próximo experimento com taxa intermediária, segmentação por risco e amostra dimensionada. |

</div>

---

## 📊 Tarefa 1 — Teste A/B

Controle (A): taxa 2,40% a.m. · Tratamento (B): taxa 2,20% a.m. · n = 2.200 ofertas

| Métrica | A (controle) | B (tratamento) | Diferença | p-valor | Conclusão |
|:---|:---:|:---:|:---:|:---:|:---|
| Taxa de aceite | 19,74% | 19,08% | -0,67 p.p. | 0,693 | Não significativo |
| Receita média (90d) | R$ 111,44 | R$ 85,29 | -23,5% | 0,014 | **Significativo** |
| Inadimplência (90d) | 2,01% | 1,63% | -0,38 p.p. | 0,501 | Não confirmada |

> [!NOTE]
> O teste de inadimplência está subpotencializado — com ~215 aceitos por braço, a mínima diferença detectável (MDE) com 80% de poder é de ~3,6 p.p., bem acima da diferença observada. "Não significativo" aqui quer dizer *sem evidência suficiente*, não *equivalência entre os grupos*.

---

## 📈 Tarefa 2 — Elasticidade Preço-Demanda

Modelo log-log (`ln(propostas) ~ ln(taxa ofertada)`) estimado em três especificações:

| Modelo | Elasticidade | IC 95% | Erro-padrão |
|:---|:---:|:---:|:---|
| OLS simples | -1,018 | [-1,174; -0,861] | Homocedástico |
| FE canal + UF | **-1,033** | [-1,179; -0,888] | Cluster-robust (semana) |
| FE + tendência temporal | -1,036 | [-1,181; -0,891] | Cluster-robust (semana) |

**Elasticidade por canal e UF** (erro-padrão cluster-robust, correção de Bonferroni para 6 comparações):

| Canal | Elasticidade | | UF | Elasticidade |
|:---|:---:|---|:---|:---:|
| Agente | -1,18 | | RJ | -1,19 |
| Site | -1,05 | | SP | -1,03 |
| App | -0,89 | | MG | -0,88 |

Após a correção, **nenhuma diferença entre canais ou UFs é estatisticamente significativa** — os valores pontuais são hipóteses para um próximo teste segmentado, não uma base para pricing diferenciado imediato.

---

## ⚠️ Limitações e Leitura Correta dos Resultados

> [!IMPORTANT]
> **Endogeneidade:** o modelo de elasticidade é uma correlação entre taxa ofertada e volume de propostas em um painel **observacional**, não um experimento controlado como o da Tarefa 1. Se a taxa é ajustada em resposta à demanda (causalidade reversa), o coeficiente pode estar enviesado em qualquer direção. A elasticidade deve ser tratada como **leitura associacional/direcional**, não como estimativa causal pronta para alimentar uma curva de otimização de receita.

Outros pontos de atenção:

- A comparação entre subgrupos (canal/UF) usa amostras menores (~135 obs. por canal, ~315 por UF), resultando em intervalos de confiança mais largos — refletido nos gráficos.
- O teste de inadimplência da Tarefa 1 está subpotencializado; a ausência de significância não implica equivalência entre os grupos.

---

## ✅ Recomendações

1. **Não adotar**, no desenho atual, a taxa testada no tratamento B como padrão.
2. **Priorizar um novo teste** com taxa intermediária (ex.: 2,30% a.m.), com segmentação por perfil de risco e amostra dimensionada para o efeito mínimo relevante em inadimplência.
3. **Não segmentar pricing** por canal/UF com base apenas na elasticidade do painel atual — tratar como hipótese a testar.
4. **Complementar a decisão** com avaliação de receita líquida, custo de risco e LTV antes de cortes mais amplos de taxa, e desenhar o próximo experimento para permitir estimar elasticidade de preço causalmente (ex.: taxas aleatorizadas por célula).

---

## 📁 Estrutura do Repositório

| Arquivo | Descrição |
|:---|:---|
| [`pricing_notebook.ipynb`](pricing_notebook.ipynb) | Notebook executado com a análise completa (Tarefas 1 e 2), passo a passo. |
| [`pricing_analysis.py`](pricing_analysis.py) | Script que reproduz toda a análise e gera os dois gráficos consolidados. |
| [`ab_test_offers.csv`](ab_test_offers.csv) | Base do experimento A/B (2.200 ofertas). |
| [`demand_panel.csv`](demand_panel.csv) | Painel semanal para estimação de elasticidade (105 semanas × canal × UF). |
| [`charts_ab.png`](charts_ab.png) | Gráfico consolidado do teste A/B. |
| [`charts_elasticidade.png`](charts_elasticidade.png) | Gráfico consolidado da elasticidade preço-demanda. |
| [`requirements.txt`](requirements.txt) | Dependências Python com versões fixas. |

---

## ⚙️ Como Reproduzir

### Pré-requisitos

- Python 3.10+
- pip

### Instalação e execução

```bash
git clone https://github.com/felipesbonatti/pricing-ab-test-elasticity.git
cd pricing-ab-test-elasticity
pip install -r requirements.txt
python pricing_analysis.py
```

O script gera `charts_ab.png` e `charts_elasticidade.png` automaticamente e imprime todos os testes estatísticos no console.

> [!TIP]
> Para uma leitura sem rodar código, abra o notebook executado (`pricing_notebook.ipynb`), que já vem com todas as saídas, tabelas e gráficos gerados.

---

## 🔍 Decisões Metodológicas

- Intervalos de confiança usam o quantil exato da distribuição *t*, não um multiplicador fixo de 1,96.
- Erros-padrão cluster-robust por semana em todos os modelos de elasticidade (geral e por subgrupo), para não subestimar a incerteza em dados de painel.
- Correção de Bonferroni no teste conjunto de 6 subgrupos (canal × UF), para não confundir variação amostral com diferença real.
- Cálculo explícito de poder estatístico (MDE) para o teste de inadimplência.
- Caveat de endogeneidade explicitado em texto e nos gráficos.

---

## 🧭 Roadmap

| Prazo | Foco | Próximos passos |
|:---|:---|:---|
| **Curto prazo** | Novo experimento | Taxa intermediária (2,30% a.m.), amostra dimensionada para o MDE de inadimplência, segmentação por perfil de risco. |
| **Médio prazo** | Causalidade | Investigar endogeneidade da taxa ofertada; avaliar IV/2SLS para estimar elasticidade causal; testar interações canal × UF formalmente. |
| **Longo prazo** | Decisão de negócio | Modelar LTV em horizonte de 12–24 meses para suportar novas bandas de taxa antes de cortes mais amplos. |

</div>
