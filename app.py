"""
Sistema Inteligente de Gestão de Cobertura de Stock e Planeamento de Produção
Aplicação Streamlit multi-página.

PG em Tecnologias e IA Aplicadas aos Negócios | ISCTE Executive Education
Carlos Mota + Henrique Amaral Dias + Vítor Ribeiro

Execução:
    streamlit run app.py
"""
from pathlib import Path
import streamlit as st
import pandas as pd
from utils.data_loader import (
    load_dim_artigos, load_kpi_pa, load_kpi_comp, load_alertas,
    load_ecf, load_mrp_agg, load_ia_modelos, get_file_info
)
from utils.theme import CUSTOM_CSS, COLOR_PRIMARY, COLOR_DANGER, COLOR_WARNING, COLOR_SUCCESS
from utils.helpers import render_footer, header_with_refresh

ASSETS = Path(__file__).parent / 'assets'

# ============================================================
# Page config
# ============================================================
st.set_page_config(
    page_title='Gestão de Stock | Sistema IA',
    page_icon='🍇',
    layout='wide',
    initial_sidebar_state='expanded',
    menu_items={
        'About': 'Projeto Final PG IA ISCTE | Henrique Amaral Dias'
    }
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ============================================================
# Banner do cliente CARMIM
# ============================================================
logo_path = ASSETS / 'carmim_logo.png'
if logo_path.exists():
    bcol1, bcol2 = st.columns([1, 3])
    with bcol1:
        st.image(str(logo_path), use_container_width=True)
    with bcol2:
        st.markdown(
            '<div style="padding-top:1.2rem;">'
            '<div style="font-size:0.85rem; color:#6B7280; text-transform:uppercase; letter-spacing:1px;">Caso de estudo</div>'
            '<div style="font-size:1.4rem; font-weight:700; color:#722F37; margin-top:0.2rem;">'
            'CARMIM — Cooperativa Agrícola de Reguengos de Monsaraz, C.R.L.</div>'
            '<div style="font-size:0.95rem; color:#6B7280; margin-top:0.3rem;">'
            'Indústria vitivinícola | Alentejo, Portugal</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    st.markdown('---')

# ============================================================
# Header
# ============================================================
header_with_refresh(
    'Sistema Inteligente de Gestão de Cobertura de Stock',
    'Business Intelligence + Inteligência Artificial para antecipação de ruturas e otimização de compras',
    show_home=False,  # já estamos em casa
)

# ============================================================
# Carga de dados
# ============================================================
try:
    dim = load_dim_artigos()
    kpi_pa = load_kpi_pa()
    kpi_comp = load_kpi_comp()
    alertas = load_alertas()
    ecf = load_ecf()
    mrp = load_mrp_agg()
    ia_mdl = load_ia_modelos()
except Exception as e:
    st.error(f'Erro ao carregar dados: {e}')
    st.stop()

# ============================================================
# Resumo no topo: 4 grandes KPIs
# ============================================================
st.markdown('## Visão global')

c1, c2, c3, c4 = st.columns(4)

n_pa_critico = int((kpi_pa['Classe_Risco'].isin(['A_CRITICO', 'B_ALTO'])).sum())
n_comp_critico = int((kpi_comp['Classe_Risco'].isin(['A_CRITICO', 'B_ALTO'])).sum())
n_alertas = int(len(alertas))
n_ecf_atrasadas = int((ecf['Dias_Para_Entrega'] < 0).sum()) if 'Dias_Para_Entrega' in ecf.columns else 0

c1.metric('Total artigos geridos', f"{len(dim):,}")
c2.metric('PA em risco alto/crítico', f"{n_pa_critico}",
          delta=f"{n_pa_critico/max(len(kpi_pa),1)*100:.1f}% do universo PA",
          delta_color='inverse')
c3.metric('Componentes em risco alto/crítico', f"{n_comp_critico}",
          delta=f"{n_comp_critico/max(len(kpi_comp),1)*100:.1f}% do universo Comp",
          delta_color='inverse')
c4.metric('Alertas activos', f"{n_alertas}",
          delta=f"{n_ecf_atrasadas} ECFs com data passada",
          delta_color='inverse')

# ============================================================
# Navegação
# ============================================================
st.markdown('---')
st.markdown('## Navegação dos dashboards')

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown('### Dashboard Executivo')
    st.markdown(
        'KPIs globais, semáforo de risco, cobertura média, '
        'pipeline ECF, top alertas. Página de entrada para gestão.'
    )
    st.page_link('pages/1_Executivo.py', label='Abrir Executivo →', icon='📊')

with c2:
    st.markdown('### Produto Acabado')
    st.markdown(
        'Stock vs mínimo, saldo disponível, cobertura, dias até rutura, '
        'distribuição por subfamília, scatter risco × cobertura.'
    )
    st.page_link('pages/2_Produto_Acabado.py', label='Abrir PA →', icon='🍷')

with c3:
    st.markdown('### Produção')
    st.markdown(
        'Necessidades de fabrico (MRP), prioridades de produção, '
        'explosão BOM, disponibilidade de componentes por PA.'
    )
    st.page_link('pages/3_Produção.py', label='Abrir Produção →', icon='🏭')

c4, c5, _ = st.columns(3)

with c4:
    st.markdown('### Componentes')
    st.markdown(
        'Stock de componentes, centralidade BOM, lead times, '
        'pipeline de ordens de compra, criticidade ponderada.'
    )
    st.page_link('pages/4_Componentes.py', label='Abrir Componentes →', icon='📦')

with c5:
    st.markdown('### Inteligência Artificial')
    st.markdown(
        'Previsão de ruturas (Random Forest + XGBoost), recomendação ML '
        'de compras, deteção de anomalias (Isolation Forest), métricas dos modelos.'
    )
    st.page_link('pages/5_IA.py', label='Abrir IA →', icon='🤖')

c6, c7, _ = st.columns(3)

with c6:
    st.markdown('### Simulador What-If (extensão)')
    st.markdown(
        'Simulação interactiva de cenários: variação de parâmetros operacionais '
        '(cobertura, lead time, safety) e simulação por SKU.'
    )
    st.page_link('pages/6_Simulador.py', label='Abrir Simulador →', icon='🎛️')

with c7:
    st.markdown('### Alertas por Email (extensão)')
    st.markdown(
        'Geração de notificações executivas com top alertas críticos. '
        'Exporta `.eml` pronto a abrir em Outlook ou enviar por SMTP.'
    )
    st.page_link('pages/7_Alertas_Email.py', label='Abrir Alertas →', icon='📧')

# ============================================================
# Resumo dos modelos IA
# ============================================================
st.markdown('---')
st.markdown('## Performance dos modelos preditivos')

c1, c2 = st.columns([2, 1])
with c1:
    st.dataframe(
        ia_mdl.style.format({
            'Accuracy': '{:.3f}',
            'Precision': '{:.3f}',
            'Recall': '{:.3f}',
            'F1': '{:.3f}',
            'ROC_AUC': '{:.3f}',
            'Avg_Precision': '{:.3f}',
        }).background_gradient(subset=['F1', 'ROC_AUC'], cmap='Greens'),
        use_container_width=True,
        hide_index=True,
    )
with c2:
    melhor = ia_mdl.loc[ia_mdl['F1'].idxmax()]
    st.info(
        f'**Modelo vencedor:** {melhor["Modelo"]}\n\n'
        f'**F1:** {melhor["F1"]:.3f} | **ROC-AUC:** {melhor["ROC_AUC"]:.3f}\n\n'
        f'Precision: {melhor["Precision"]:.3f} | Recall: {melhor["Recall"]:.3f}'
    )

# ============================================================
# Metodologia (expansível)
# ============================================================
with st.expander('Metodologia e limitações'):
    st.markdown('''
**Estratégia A+B**

A camada de Business Intelligence (dashboards, alertas, MRP) opera sobre os snapshots reais
dos ficheiros ERP. A camada de Inteligência Artificial opera sobre série temporal sintética
derivada dos parâmetros de gestão observados (Stock Mínimo, Stock Reposição) e do lead time
real das ECF, com sazonalidade vitivinícola conhecida da literatura. A derivação está documentada
e é determinística.

**Fórmulas centrais**

Consumo diário implícito (Componentes): μ = (Stock_Reposição − Stock_Mínimo) / Lead_Time
(quando Reposição > Mínimo); senão Stock_Mín / Lead_Time

Consumo diário implícito (PA): μ = Stock_Mínimo / Cob_Obj_PA

Score de criticidade: 100 × (1 − Dias_Até_Rutura / Cob_Obj), com cap [0, 100]

Score ponderado de componente: Score × (1 + Centralidade_BOM / 20)

**Limitações documentadas**

1. Sem histórico de vendas real (snapshot pontual)
2. Sem carteira de encomendas de clientes
3. Lead time homogéneo de 14 dias para todos os componentes
4. BOM Standard como default; alternativos por cliente excluídos do MRP base
5. A performance ML é medida sobre série derivada; em produção espera-se ROC-AUC 0.80-0.92
    ''')

# ============================================================
# Metadados dos ficheiros
# ============================================================
info = get_file_info()
if info:
    with st.expander('Estado dos ficheiros de dados'):
        for nome, meta in info.items():
            st.text(f"{nome}: {meta['tamanho_kb']:.1f} KB | "
                    f"actualizado em {meta['modificado'].strftime('%Y-%m-%d %H:%M')}")

render_footer()
