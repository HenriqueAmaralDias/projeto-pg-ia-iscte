"""
Dashboard 3 — Produção
Necessidades de fabrico (MRP), prioridades, explosão BOM.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import (
    load_kpi_pa, load_mrp_net, load_mrp_agg, load_bom
)
from utils.theme import (
    CUSTOM_CSS, CLASS_RISCO_COLORS, PLOTLY_LAYOUT_DEFAULTS,
    COLOR_PRIMARY, COLOR_DANGER, COLOR_WARNING, COLOR_SUCCESS
)
from utils.helpers import render_footer, header_with_refresh, render_download

st.set_page_config(page_title='Produção', page_icon='🏭', layout='wide')
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

header_with_refresh('Dashboard de Produção',
                     'Necessidades de fabrico, prioridades, explosão BOM')

# Carga
kpi_pa = load_kpi_pa()
mrp_net = load_mrp_net()
mrp_agg = load_mrp_agg()
bom = load_bom()

# ============================================================
# KPIs no topo
# ============================================================
st.markdown('### Necessidades de Produção')

c1, c2, c3, c4 = st.columns(4)

pa_a_produzir = kpi_pa[
    kpi_pa['Recomendacao'].str.contains('PRODUZIR', na=False) |
    kpi_pa['Recomendacao'].str.contains('Planear', na=False)
]
c1.metric('PA a produzir', len(pa_a_produzir))

n_urgente = int(kpi_pa['Recomendacao'].str.contains('URGENTE', na=False).sum())
c2.metric('PA urgentes', n_urgente, delta_color='inverse')

n_planear = int(kpi_pa['Recomendacao'].str.contains('Planear', na=False).sum())
c3.metric('PA a planear', n_planear)

n_excesso = int(kpi_pa['Recomendacao'].str.contains('Excesso', na=False).sum())
c4.metric('PA com excesso de stock', n_excesso)

st.markdown('---')

# ============================================================
# Linha 2 — Prioridades de produção (top 20)
# ============================================================
st.markdown('### Top 20 prioridades de produção')

prio = pa_a_produzir.sort_values('Score_Criticidade', ascending=False).head(20).copy()

if len(prio) > 0:
    prio['Label'] = prio['Cod_Artigo'] + ' — ' + prio['Descricao'].str[:40]
    fig = px.bar(
        prio.sort_values('Score_Criticidade', ascending=True),
        x='Score_Criticidade',
        y='Label',
        orientation='h',
        color='Classe_Risco',
        color_discrete_map=CLASS_RISCO_COLORS,
        hover_data=['Stock_Atual', 'Stock_Minimo', 'Saldo_Disponivel',
                    'Dias_Ate_Rutura_Com_OC'],
        title='Score de criticidade dos PAs com necessidade de produção'
    )
    fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS, height=600,
                      yaxis_title='', xaxis_title='Score (0-100)')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info('Sem PAs a produzir no estado actual.')

# ============================================================
# Linha 3 — Tabela detalhada de produção
# ============================================================
st.markdown('### Plano de produção detalhado')

if len(pa_a_produzir) > 0:
    plan_cols = ['Cod_Artigo', 'Descricao', 'Subfamilia', 'Stock_Atual',
                 'Stock_Minimo', 'Saldo_Disponivel', 'Dias_Ate_Rutura_Com_OC',
                 'Score_Criticidade', 'Classe_Risco', 'Recomendacao']
    plan_cols = [c for c in plan_cols if c in pa_a_produzir.columns]
    plano = pa_a_produzir[plan_cols].sort_values('Score_Criticidade', ascending=False)

    st.dataframe(
        plano.style.format({
            'Stock_Atual': '{:,.0f}',
            'Stock_Minimo': '{:,.0f}',
            'Saldo_Disponivel': '{:,.0f}',
            'Dias_Ate_Rutura_Com_OC': '{:.1f}',
            'Score_Criticidade': '{:.1f}',
        }).background_gradient(subset=['Score_Criticidade'], cmap='Reds'),
        use_container_width=True,
        hide_index=True,
        height=350,
    )

    render_download(plano, 'plano_producao.csv', 'Exportar plano de produção')

# ============================================================
# Linha 4 — Explosão BOM agregada
# ============================================================
st.markdown('---')
st.markdown('### Explosão BOM — Componentes necessários para a produção planeada')

if len(mrp_agg) > 0:
    c1, c2, c3 = st.columns(3)
    c1.metric('Componentes únicos necessários', len(mrp_agg))
    c2.metric('Componentes a encomendar',
              int(mrp_agg['Encomendar'].sum()) if 'Encomendar' in mrp_agg.columns else 0)
    nec_total = mrp_agg['Nec_Liquida_Total'].sum() if 'Nec_Liquida_Total' in mrp_agg.columns else 0
    c3.metric('Necessidade líquida total (un)', f"{nec_total:,.0f}")

    # Top 15 com maior necessidade
    top_mrp = mrp_agg.sort_values('Nec_Liquida_Total', ascending=False).head(15)
    top_mrp_view = top_mrp.copy()
    top_mrp_view['Label'] = top_mrp_view['Cod_Comp'] + ' — ' + top_mrp_view['Desc_Comp'].str[:40]
    fig = px.bar(
        top_mrp_view.sort_values('Nec_Liquida_Total', ascending=True),
        x='Nec_Liquida_Total',
        y='Label',
        orientation='h',
        color='Num_PA_Afectados',
        color_continuous_scale='Burg',
        hover_data=['Stock_Actual', 'OC_Pendente', 'Nec_Bruta_Total'],
        title='Top 15 componentes a encomendar (cor = número de PAs afectados)'
    )
    fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS, height=550,
                      yaxis_title='', xaxis_title='Necessidade líquida (un)')
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        mrp_agg.style.format({
            'Nec_Bruta_Total': '{:,.0f}',
            'Nec_Liquida_Total': '{:,.0f}',
            'Stock_Actual': '{:,.0f}',
            'OC_Pendente': '{:,.0f}',
        }).background_gradient(subset=['Nec_Liquida_Total'], cmap='Reds'),
        use_container_width=True,
        hide_index=True,
        height=300,
    )

    render_download(mrp_agg, 'mrp_componentes.csv', 'Exportar MRP completo')
else:
    st.info('Sem necessidades MRP no estado actual.')

# ============================================================
# Linha 5 — Drill-down BOM por PA
# ============================================================
st.markdown('---')
st.markdown('### Drill-down: requisitos por PA seleccionado')

pa_options = sorted(pa_a_produzir['Cod_Artigo'].unique().tolist()) if len(pa_a_produzir) > 0 else []
if pa_options:
    sel_pa = st.selectbox('PA a explorar:', pa_options, key='prod_pa')
    detalhe = mrp_net[mrp_net['Cod_PA'] == sel_pa]
    if len(detalhe) > 0:
        st.dataframe(
            detalhe[['Cod_Comp', 'Desc_Comp', 'Familia_Comp', 'Consumo_Unit',
                     'Nec_Bruta', 'Stock_Comp_Actual', 'OC_Comp_Pendente',
                     'Nec_Liquida', 'Acao']].style.format({
                'Consumo_Unit': '{:.2f}',
                'Nec_Bruta': '{:,.0f}',
                'Stock_Comp_Actual': '{:,.0f}',
                'OC_Comp_Pendente': '{:,.0f}',
                'Nec_Liquida': '{:,.0f}',
            }),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(f'PA {sel_pa} sem necessidades líquidas calculadas.')

render_footer()
