# Sistema Inteligente de Gestão de Cobertura de Stock e Planeamento de Produção

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://projeto-stock-iscte.streamlit.app/)

**Demo live:** https://projeto-stock-iscte.streamlit.app/

Aplicação Streamlit multi-página | Projeto Final | PG em IA | ISCTE
Autor: Henrique Amaral Dias

---

## Estrutura da aplicação

```
streamlit_app/
├── app.py                          # Home: visão global e navegação
├── pages/
│   ├── 1_Executivo.py              # Dashboard executivo
│   ├── 2_Produto_Acabado.py        # Dashboard PA
│   ├── 3_Producao.py               # Dashboard de produção (MRP)
│   ├── 4_Componentes.py            # Dashboard de componentes
│   └── 5_IA.py                     # Dashboard de IA preditiva
├── utils/
│   ├── data_loader.py              # Carga com cache
│   ├── helpers.py                  # Filtros e widgets partilhados
│   └── theme.py                    # Paleta de cores e estilos
├── data/
│   ├── Modelo_Dados_Consolidado_v1.xlsx
│   └── IA_Previsoes_v1.xlsx
├── requirements.txt
└── README.md
```

## Pré-requisitos

Python 3.10 ou superior.

## Instalação

```bash
cd streamlit_app
pip install -r requirements.txt
```

## Execução

```bash
streamlit run app.py
```

A aplicação abre automaticamente em `http://localhost:8501`.

## Dashboards disponíveis

| # | Dashboard | Funcionalidade |
|---|---|---|
| 1 | Executivo | KPIs globais, semáforo de risco, top alertas, pipeline ECF |
| 2 | Produto Acabado | Stock vs mínimo, cobertura, mapa de risco, drill-down BOM |
| 3 | Produção | Necessidades de fabrico, prioridades, explosão BOM, drill-down PA |
| 4 | Componentes | Stock, centralidade BOM, single points of failure, pipeline compras |
| 5 | Inteligência Artificial | Previsões de rutura, recomendação ML, deteção de anomalias |

## Estratégia metodológica A+B

A camada de BI (dashboards 1 a 4) opera sobre snapshots reais dos ficheiros ERP.
A camada de IA (dashboard 5) opera sobre série temporal sintética derivada dos parâmetros
de gestão observados (Stock Mínimo, Stock Reposição) e do lead time real das ECF, com
sazonalidade vitivinícola da literatura. A derivação é determinística, documentada e
está dentro do âmbito do caderno de encargos.

## Funcionalidades obrigatórias (caderno de encargos)

| Requisito | Cumprido em |
|---|---|
| Atualização automática de dados | Cache TTL 300s + botão "Actualizar dados" em todas as páginas |
| Visualização em tempo real | Streamlit re-render automático |
| Alertas de rutura | Dashboard Executivo e PA |
| Alertas de necessidade de compra | Dashboard Componentes e IA |
| Indicadores de prioridade | Score de Criticidade em todas as páginas |
| Simulação de cenários | Parâmetros editáveis em `01_Parametros` do modelo + filtros laterais |
| Drill-down até artigo e componente | Implementado em Produto Acabado e Produção |

## Atualização dos dados

O sistema lê dois ficheiros Excel da pasta `data/`:

1. `Modelo_Dados_Consolidado_v1.xlsx`: modelo de dados estrela com 13 sheets
2. `IA_Previsoes_v1.xlsx`: outputs dos modelos preditivos

Para atualizar os dados:
1. Substituir os ficheiros em `data/`
2. Clicar no botão "Actualizar dados" no canto superior direito de qualquer página

Em produção, estes ficheiros seriam substituídos por queries SQL directas ao ERP PHC
(arquitectura documentada no ficheiro TI-ARQ).

## Tecnologias

| Tecnologia | Função |
|---|---|
| Streamlit 1.x | Framework de UI |
| Pandas | Manipulação de dados |
| Plotly | Visualizações interactivas |
| Scikit-learn | Modelos ML (RF, LogReg, IsolationForest) |
| XGBoost | Modelo de classificação |
| openpyxl | Leitura/escrita Excel |

## Próximos passos (roadmap)

1. Substituir Excel por queries SQL directas ao PHC ERP
2. Retraining mensal dos modelos com histórico real
3. Adicionar carteira de encomendas de clientes (subtrair ao saldo disponível)
4. Modelos de séries temporais (Prophet, ARIMA) sobre histórico real
5. Alertas automáticos por email/Teams via webhooks Streamlit
6. Autenticação SSO corporativa
7. Deploy em servidor interno (Docker + nginx)
