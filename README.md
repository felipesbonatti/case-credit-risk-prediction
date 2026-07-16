<div align="center">

# 🏦 Credit Risk Platform

### Plataforma Enterprise de Machine Learning para Análise de Risco de Crédito

<br>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-5.0+-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-3.0+-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)

<br>

[![LightGBM](https://img.shields.io/badge/LightGBM-3.3.2-yellow?style=for-the-badge&logo=lightgbm&logoColor=black)](https://lightgbm.readthedocs.io/)
[![Scikit Learn](https://img.shields.io/badge/Scikit--Learn-1.3+-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0+-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![NumPy](https://img.shields.io/badge/NumPy-1.24+-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org/)



<br>

[![Tests](https://img.shields.io/badge/Tests-79_passing-success?style=for-the-badge&logo=pytest)](/api/tests)
[![BACEN](https://img.shields.io/badge/BACEN-Compliant-red?style=for-the-badge&logo=bank)](https://www.bcb.gov.br/)
[![Coverage](https://img.shields.io/badge/Coverage-92%25-brightgreen?style=for-the-badge&logo=codecov)](README.md)

</div>

@@ -33,372 +26,193 @@
## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Demonstração do Sistema](#-demonstração-do-sistema)
- [Objetivo do Case e Valor de Negócio](#-objetivo-do-case-e-valor-de-negócio)
- [Arquitetura de Solução](#️-arquitetura-de-solução)
- [Plano de Implementação](#️-plano-de-implementação)
- [Reprodutibilidade da Arquitetura](#️-reprodutibilidade-da-arquitetura)
- [Screenshots do Sistema](#-screenshots-do-sistema)
- [Melhorias e Roadmap](#-melhorias-e-roadmap)
- [Documentação Adicional](#-documentação-adicional)



---

## 🎯 Visão Geral

> **Plataforma de Machine Learning enterprise-grade para análise de risco de crédito, totalmente automatizada com um script de execução universal (`run_all.py`). A solução integra um modelo LightGBM de alta performance (AUC 0.79), uma API FastAPI robusta e um Dashboard Premium em React, demonstrando um ciclo de MLOps completo, desde a geração dos dados até a implantação e o teste, com foco em conformidade regulatória e rentabilidade do negócio.**

### Destaques do Projeto

<div align="center">

| **Automação** | **ML Model** | **API** | **Dashboard** | **Conformidade** |
|:---:|:---:|:---:|:---:|:---:|
| `run_all.py` | **LightGBM** | **FastAPI** | **React + TS** | **BACEN 2682/99** |
| Setup em 1 comando | AUC **0.79** | **79 testes** | Análise Individual | Taxa Mínima |
| Cross-platform | **21 features** | Swagger Docs | Análise em Lote | Provisão |

</div>

> [!IMPORTANT]
> Este projeto foi desenvolvido para a **Banca do Santander** e demonstra um ciclo completo de MLOps, desde a geração de dados até a implantação em produção.

---

## 📋 Demonstração do Sistema

### Análise Individual - Crédito Aprovado

<div align="center">

![Análise Individual - Aprovado](https://raw.githubusercontent.com/felipesbonatti/case-credit-risk-prediction/main/assets/analise-individual.gif)

**Análise individual com resultado de crédito aprovado**

</div>

### Análise Individual - Crédito Negado

<div align="center">

![Análise Individual - Negado](https://raw.githubusercontent.com/felipesbonatti/case-credit-risk-prediction/main/assets/analise_individual.gif)

**Análise individual com resultado de crédito negado**

</div>

### Análise em Lote

<div align="center">

![Análise em Lote](https://raw.githubusercontent.com/felipesbonatti/case-credit-risk-prediction/main/assets/demo.gif)

**Processamento em lote de múltiplas propostas com upload de arquivo CSV**

</div>

---

## 🎯 Objetivo do Case e Valor de Negócio

### Valor de Negócio Mensurável




<div align="center">

| Métrica | Valor Alcançado | Impacto no Negócio |
|:-----------|:-------------------|:----------------------|
| **Automação do Setup** | 100% com `run_all.py` | **Time-to-Market Reduzido**: Qualquer desenvolvedor pode ter o ambiente 100% funcional em minutos, não dias. |
| **Inteligência de Taxas** | Baseado em dados do BACEN | **Rentabilidade Otimizada**: A taxa mínima rentável, calculada com base no risco real e custos operacionais, evita prejuízos. |
| **Qualidade do Código** | 79 testes automatizados | **Redução de Riscos e Bugs**: Garante a estabilidade da API e a confiabilidade das predições. |
| **Performance do Modelo** | AUC-ROC > 0.79 | **Decisões Mais Precisas**: Aumenta a capacidade de identificar bons e maus pagadores, reduzindo a inadimplência. |
| **Conformidade** | Resolução CMN 2.682/99 | **Segurança Regulatória**: O cálculo de provisão e as taxas estão alinhados com as normas do BACEN. |

</div>

---

## 🏛️ Arquitetura de Solução

### Fluxo de Dados e Processamento

```mermaid
graph TB
    A[run_all.py] --> B[Geração de Dados<br/>1M registros]
    B --> C[Treinamento LightGBM<br/>AUC 0.79]
    C --> D[Artefatos PKL<br/>modelo + encoders]
    D --> E[API FastAPI<br/>79 testes]
    E --> F[Dashboard React<br/>Análise Individual]
    E --> G[Dashboard React<br/>Análise em Lote]
    F --> H[Usuário Final]
    G --> H
    
    style A fill:#4CAF50,stroke:#2E7D32,stroke-width:3px,color:#fff
    style B fill:#2196F3,stroke:#1565C0,stroke-width:2px,color:#fff
    style C fill:#FF9800,stroke:#E65100,stroke-width:2px,color:#fff
    style D fill:#9C27B0,stroke:#6A1B9A,stroke-width:2px,color:#fff
    style E fill:#F44336,stroke:#C62828,stroke-width:2px,color:#fff
    style F fill:#00BCD4,stroke:#00838F,stroke-width:2px,color:#fff
    style G fill:#00BCD4,stroke:#00838F,stroke-width:2px,color:#fff
    style H fill:#4CAF50,stroke:#2E7D32,stroke-width:3px,color:#fff
```

### Componentes Técnicos

<details open>
<summary><b>Clique para expandir/recolher a tabela de componentes</b></summary>




| Componente | Tecnologia | Responsabilidade | Justificativa da Escolha |
|:--------------|:--------------|:--------------------|:----------------------------|
| **API de Predição** | **FastAPI** | Orquestrar o fluxo de predição, aplicar regras de negócio, gerenciar segurança e servir o modelo de ML. | Altíssima performance (assíncrona), validação de dados nativa com Pydantic e geração automática de documentação interativa. |
| **Dashboard Premium** | **React (Vite) + TypeScript** | Fornecer uma interface rica, moderna e interativa para a análise de crédito, com componentes reutilizáveis e performance otimizada. | Ecossistema maduro, componentização, performance superior e flexibilidade para criar UIs complexas e profissionais. |
| **Modelo de Risco** | **LightGBM** | Realizar a classificação de risco de crédito com alta precisão e baixa latência. | Performance superior em dados tabulares, eficiência em memória e velocidade de treinamento, ideal para o cenário de crédito. |
| **Testes Automatizados** | **Pytest** | Garantir a qualidade, a estabilidade e a confiabilidade da API, com uma suíte de 79 testes cobrindo diversas camadas da aplicação. | Simplicidade, ecossistema rico em plugins e padrão de mercado para testes em Python, facilitando a manutenção e a evolução do código. |
| **Script de Automação** | **Python (Padrão)** | Orquestrar todo o ciclo de vida da aplicação: setup do ambiente, geração de dados, treinamento do modelo e inicialização dos serviços. | Linguagem universal e de fácil manutenção, permitindo a criação de um fluxo de trabalho complexo e à prova de falhas. |

</details>

---

## ⚙️ Plano de Implementação

### Automação Universal com `run_all.py`

> [!TIP]
> O principal diferencial do projeto é o script **`run_all.py`**, que automatiza **todo o ciclo de vida da aplicação** em um único comando, garantindo a **reprodutibilidade da arquitetura** em qualquer ambiente.

```mermaid
graph TD
    A[run_all.py] --> B[Verificação do Ambiente]
    B --> C[Criação dos .env]
    C --> D[Instalação de Dependências]
    D --> E[Geração de Dados 1M]
    E --> F[Treinamento LightGBM]
    F --> G[Build do Dashboard]
    G --> H[Execução de 79 Testes]
    H --> I[Inicialização dos Serviços]
    I --> J[Abre Navegador]
    
    style A fill:#4CAF50,stroke:#2E7D32,stroke-width:3px,color:#fff
    style B fill:#2196F3,stroke:#1565C0,stroke-width:2px,color:#fff
    style C fill:#2196F3,stroke:#1565C0,stroke-width:2px,color:#fff
    style D fill:#2196F3,stroke:#1565C0,stroke-width:2px,color:#fff
    style E fill:#FF9800,stroke:#E65100,stroke-width:2px,color:#fff
    style F fill:#FF9800,stroke:#E65100,stroke-width:2px,color:#fff
    style G fill:#9C27B0,stroke:#6A1B9A,stroke-width:2px,color:#fff
    style H fill:#00BCD4,stroke:#00838F,stroke-width:2px,color:#fff
    style I fill:#4CAF50,stroke:#2E7D32,stroke-width:2px,color:#fff
    style J fill:#4CAF50,stroke:#2E7D32,stroke-width:3px,color:#fff
```

<details open>
<summary><b>Clique para ver a tabela detalhada de passos</b></summary>

| Passo | Ação | Propósito |
|:--------:|:--------|:-------------|
| **1** | **Verificação do Ambiente** | Detecta Python, Node.js e gerenciadores de pacotes disponíveis no sistema. |
| **2** | **Criação dos Arquivos `.env`** | Gera arquivos de configuração com segredos e variáveis de ambiente necessárias. |
| **3** | **Instalação das Dependências** | Instala todos os pacotes necessários via `pip` e `pnpm`/`npm` automaticamente. |
| **4** | **Geração de Dados Sintéticos** | Executa `scripts/gerar_dados_REALISTICOS.py` para criar o dataset de treinamento realístico (1 milhão de registros). |
| **5** | **Treinamento do Modelo** | Executa `scripts/treinar_modelo_PREMIUM.py` para treinar o modelo LightGBM e salvar os artefatos (PKL). |
| **6** | **Build do Dashboard** | Compila a aplicação React (`dashboard_premium`) para produção com otimizações. |
| **7** | **Execução dos Testes** | Roda a suíte completa de 79 testes `pytest` para garantir a integridade da API. |
| **8** | **Inicialização dos Serviços** | Inicia a API FastAPI e serve o Dashboard Premium, abrindo ambos automaticamente no navegador. |

</details>





### Inteligência de Negócio e Conformidade Regulatória

#### Cálculo da Taxa Mínima Rentável

> [!NOTE]
> Para evitar operações que gerem prejuízo, o sistema calcula a **taxa mínima rentável** para cada proposta, baseada na Resolução 2.682/99 do CMN (Conselho Monetário Nacional).


**Fórmula:**

```math
Receita_{necessária} = CDI + Provisão_{BACEN} + Custos_{operacionais} + Margem_{mínima}
```

**Onde:**
- **CDI**: Taxa de captação do banco (custo de oportunidade)
- **Provisão BACEN**: Percentual de provisionamento obrigatório conforme nível de risco (Resolução 2.682/99)
- **Custos Operacionais**: Despesas administrativas, tecnologia, pessoal
- **Margem Mínima**: Retorno mínimo esperado pelos acionistas

#### Validação Flexível e Inteligente

```mermaid
stateDiagram-v2
    [*] --> Input: Usuário digita taxa
    Input --> Validacao1: Taxa < Recomendada BACEN?
    Validacao1 --> Aviso: Sim
    Validacao1 --> Validacao2: Não
    Aviso --> Validacao2: Usuário confirma e continua
    Validacao2 --> Bloqueio: Taxa < Mínima Rentável?
    Validacao2 --> Aprovado: Não
    Bloqueio --> [*]: Operação bloqueada
    Aprovado --> [*]: Análise prossegue
```
---

## 🛠️ Reprodutibilidade da Arquitetura

> [!IMPORTANT]
> A complexidade de configurar um ambiente de desenvolvimento de Machine Learning é um dos maiores gargalos em projetos de dados. Para resolver isso, o projeto inclui o `run_all.py`, um script de automação que encapsula **toda a complexidade do setup em um único comando**.

### Pré-requisitos

- **Python 3.11+**
- **Node.js 18+** (Necessário para o Dashboard Premium em React)

### Execução com um Único Comando

<table>
<tr>
<td width="50%">

#### Linux / macOS

```bash
python3 run_all.py
```

</td>
<td width="50%">

#### Windows

```powershell
python run_all.py
```

</td>
</tr>
</table>

> [!TIP]
> É só isso. O script cuidará de todo o resto, executando o pipeline completo de MLOps de forma sequencial.

### Verificação Final

Após a conclusão do script, os seguintes serviços estarão disponíveis:

<div align="center">

| Serviço | URL | Descrição |
|:-----------|:-------|:-------------|
| **API Docs (Swagger)** | [`http://localhost:8000/docs`](http://localhost:8000/docs) | Documentação interativa da API com interface Swagger UI |
| **Dashboard Premium** | [`http://localhost:3000`](http://localhost:3000) | Interface de análise de risco individual e em lote |
| **Health Check** | [`http://localhost:8000/health`](http://localhost:8000/health) | Endpoint de verificação de status da API |

</div>

---

## 📊 Screenshots do Sistema

### Análise em Lote - Interface Principal

<div align="center">

![Análise em Lote - Interface](https://raw.githubusercontent.com/felipesbonatti/case-credit-risk-prediction/main/assets/analise-lote.png)

**Interface de análise em lote com upload de arquivo CSV**

</div>

### Análise em Lote - Resultados

<div align="center">

![Análise em Lote - Resultados](https://raw.githubusercontent.com/felipesbonatti/case-credit-risk-prediction/main/assets/analise_lote.png)

**Visualização detalhada dos resultados do processamento em lote**

</div>

---

## 🧠 Melhorias e Roadmap

> [!NOTE]
> O projeto atual estabelece uma base sólida e `production-ready`. O próximo passo é evoluir para uma plataforma de MLOps totalmente automatizada e escalável em nuvem.

### Roadmap de Evolução

```mermaid
timeline
    title Roadmap de Evolução da Plataforma
    section Curto Prazo
        CI/CD : GitHub Actions
              : Testes automatizados
              : Deploy contínuo
        Orquestração : Apache Airflow
                     : Retreinamento periódico
                     : Monitoramento de jobs
    section Médio Prazo
        Cloud : AWS/Azure/GCP
              : Terraform (IaC)
              : Kubernetes (EKS/AKS/GKE)
        Escalabilidade : Auto-scaling
                       : Load balancing
                       : Alta disponibilidade
    section Longo Prazo
        MLOps Avançado : Data Drift detection
                       : Concept Drift monitoring
                       : A/B Testing
        Governança : Feature Store
                   : Model Registry
                   : Lineage tracking
```

<details open>
<summary><b>Clique para ver a tabela detalhada do roadmap</b></summary>

| Fase | Foco | Melhorias Propostas |
|:--------|:--------|:-----------------------|
| **Curto Prazo** | **CI/CD e Orquestração** | Implementação de **GitHub Actions** para CI/CD com testes automatizados a cada commit e deploy contínuo. Uso de **Apache Airflow** para orquestração do retreinamento periódico do modelo e monitoramento de jobs. |
| **Médio Prazo** | **Implantação em Nuvem** | Utilização de **Infraestrutura como Código (IaC)** com **Terraform** para provisionamento automatizado de recursos. Implantação em **Kubernetes (EKS/AKS/GKE)** para alta disponibilidade, escalabilidade automática e load balancing. |
| **Longo Prazo** | **Monitoramento e Governança** | Implementação de monitoramento avançado de **Data Drift** e **Concept Drift** para detectar degradação do modelo. Desenvolvimento de uma **Feature Store** centralizada para versionamento de variáveis e **Model Registry** para governança completa. |

</details>









---

## 📚 Documentação Adicional

### Arquivos de Documentação

<details open>
<summary><b>Clique para ver todos os arquivos de documentação</b></summary>

1. [`docs/BACEN_2682_Criterios_Risco.md`](https://github.com/felipesbonatti/case-credit-risk-prediction/blob/main/docs/BACEN_2682_Criterios_Risco.md) - Detalhamento técnico da aplicação da Resolução 2.682/99
2. [`docs/Santander_Criterios_Score.md`](https://github.com/felipesbonatti/case-credit-risk-prediction/blob/main/docs/Santander_Criterios_Score.md) - Critérios de score e taxas utilizadas pelo sistema
3. [`api/tests/`](https://github.com/felipesbonatti/case-credit-risk-prediction/tree/main/api/tests) - Suíte completa de 79 testes automatizados
4. [`api/app/services/model_service.py`](https://github.com/felipesbonatti/case-credit-risk-prediction/blob/main/api/app/services/model_service.py) - Implementação da lógica de risco e conformidade regulatória
5. [`scripts/`](https://github.com/felipesbonatti/case-credit-risk-prediction/tree/main/scripts) - Scripts de geração de dados sintéticos e treinamento do modelo

</details>






### URLs de Acesso

> [!TIP]
> Após a execução de `run_all.py`, os seguintes serviços estarão disponíveis:

<div align="center">

| Serviço | URL |
|:-----------|:-------|
| **API Docs (Swagger)** | `http://localhost:8000/docs` |
| **ReDoc** | `http://localhost:8000/redoc` |
| **Dashboard Premium** | `http://localhost:3000` |
| **Health Check** | `http://localhost:8000/health` |
| **Métricas** | `http://localhost:8000/api/v1/metrics` |

</div>





---

**Licença:** MIT License - consulte o arquivo [LICENSE](LICENSE) para mais detalhes.







</div>
