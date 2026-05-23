"""
Dashboard 4 — Componentes
Stock de componentes, centralidade BOM, lead times, ordens de compra.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import load_kpi_comp, load_ecf, load_bom
from utils.theme import (
    CUSTOM_CSS, CLASS_RISCO_COLORS, PLOTLY_LAYOUT_DEFAULTS,
    COLOR_PRIMARY, COLOR_DANGER, COLOR_WARNING, COLOR_SUCCESS
)
from utils.helpers import (
    render_footer, header_with_refresh, sidebar_filters_comp, render_download
)

st.set_page_config(page_title='Componentes', page_icon='📦', layout='wide')
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

header_with_refresh('Dashboard de Componentes',
                     'Stock, centralidade BOM, pipeline de compras')

# Carga
kpi_comp = load_kpi_comp()
ecf = load_ecf()
bom = load_bom()

# Filtros
kpi_filt = sidebar_filters_comp(kpi_comp)

# ============================================================
# KPIs no topo
# ============================================================
c1, c2, c3, c4, c5 = st.columns(5)

c1.metric('Componentes filtrados', len(kpi_filt))
stock_total = kpi_filt['Stock_Atual'].sum()
c2.metric('Stock total (un)', f"{stock_total:,.0f}")
n_critico = int(kpi_filt['Classe_Risco'].isin(['A_CRITICO', 'B_ALTO']).sum())
c3.metric('Em risco alto/crítico', n_critico, delta_color='inverse')
n_encomendar = int(kpi_filt['Recomendacao'].str.contains('ENCOMENDAR', na=False).sum())
c4.metric('A encomendar', n_encomendar)
cen_max = int(kpi_filt['Centralidade_BOM'].max()) if len(kpi_filt) else 0
c5.metric('Centralidade BOM máx.', cen_max)

st.markdown('---')

# ============================================================
# Linha 2 — Scatter: centralidade × score (revela single points of failure)
# ============================================================
st.markdown('### Mapa de risco — Centralidade BOM vs Score Ponderado')

scatter_df = kpi_filt[kpi_filt['Centralidade_BOM'] > 0].copy()
scatter_df['Stock_Size'] = scatter_df['Stock_Atual'].clip(lower=0)
if len(scatter_df) > 0:
    fig = px.scatter(
        scatter_df,
        x='Centralidade_BOM',
        y='Score_Criticidade_Ponderado',
        size='Stock_Size',
        color='Classe_Risco',
        color_discrete_map=CLASS_RISCO_COLORS,
        hover_data=['Cod_Artigo', 'Descricao', 'Stock_Atual', 'Stock_Minimo'],
        title='Eixo X = nº de PAs que usam o componente; eixo Y = score ponderado',
    )
    fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS, height=450)
    fig.add_hline(y=75, line_dash='dash', line_color=COLOR_DANGER,
                  annotation_text='Limiar A_CRITICO', annotation_position='top right')
    fig.add_vline(x=20, line_dash='dot', line_color=COLOR_WARNING,
                  annotation_text='Single point of failure', annotation_position='top')
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        'Componentes no quadrante superior direito são "single points of failure": '
        'usados em muitos PAs **e** com risco elevado. Prioridade máxima de gestão.'
    )

# ============================================================
# Linha 3 — Top componentes mais críticos
# ============================================================
c1, c2 = st.columns(2)

with c1:
    st.markdown('### Top 15 — Mais centrais na BOM')
    top_central = kpi_filt.nlargest(15, 'Centralidade_BOM').copy()
    top_central['Label'] = top_central['Cod_Artigo'] + ' — ' + top_central['Descricao'].str[:35]
    if len(top_central) > 0:
        fig = px.bar(
            top_central.sort_values('Centralidade_BOM', ascending=True),
            x='Centralidade_BOM', y='Label', orientation='h',
            color='Classe_Risco', color_discrete_map=CLASS_RISCO_COLORS,
        )
        fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS, height=500,
                          yaxis_title='', xaxis_title='nº de PAs')
        st.plotly_chart(fig, use_container_width=True)

with c2:
    st.markdown('### Top 15 — Maior score de criticidade')
    top_score = kpi_filt.nlargest(15, 'Score_Criticidade_Ponderado').copy()
    top_score['Label'] = top_score['Cod_Artigo'] + ' — ' + top_score['Descricao'].str[:35]
    if len(top_score) > 0:
        fig = px.bar(
            top_score.sort_values('Score_Criticidade_Ponderado', ascending=True),
            x='Score_Criticidade_Ponderado', y='Label', orientation='h',
            color='Classe_Risco', color_discrete_map=CLASS_RISCO_COLORS,
        )
        fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS, height=500,
                          yaxis_title='', xaxis_title='Score (0-100)')
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# Linha 4 — Pipeline de compras (ECFs)
# ============================================================
st.markdown('### Pipeline de Ordens de Compra')

c1, c2, c3 = st.columns(3)
c1.metric('ECFs activas', len(ecf))
n_atras = int((ecf['Dias_Para_Entrega'] < 0).sum()) if 'Dias_Para_Entrega' in ecf.columns else 0
c2.metric('Com data passada', n_atras, delta_color='inverse')
qtd_total = ecf['Qtd_1a_ECF'].sum() if 'Qtd_1a_ECF' in ecf.columns else 0
c3.metric('Quantidade total pipeline', f"{qtd_total:,.0f}")

if len(ecf) > 0 and 'Data_1a_Entrega' in ecf.columns:
    ecf_view = ecf.copy()
    ecf_view['Data'] = pd.to_datetime(ecf_view['Data_1a_Entrega']).dt.normalize()
    daily = ecf_view.groupby('Data')['Qtd_1a_ECF'].sum().reset_index()
    fig = px.bar(
        daily, x='Data', y='Qtd_1a_ECF',
        title='Quantidade de entregas esperadas por dia',
        color_discrete_sequence=[COLOR_PRIMARY],
    )
    fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS, height=300)
    today_ts = pd.Timestamp.today().normalize()
    fig.add_shape(type='line', x0=today_ts, x1=today_ts, y0=0, y1=1,
                  yref='paper', line=dict(color=COLOR_DANGER, dash='dash', width=2))
    fig.add_annotation(x=today_ts, y=1.02, yref='paper', text='Hoje',
                       showarrow=False, font=dict(color=COLOR_DANGER))
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# Linha 5 — Tabela detalhada
# ============================================================
st.markdown('### Detalhe por componente')

cols = ['Cod_Artigo', 'Descricao', 'Tipo_Artigo', 'Subfamilia', 'Stock_Atual',
        'Stock_Minimo', 'Stock_Reposicao', 'Saldo_Disponivel',
        'Centralidade_BOM', 'Dias_Ate_Rutura_Com_OC',
        'Score_Criticidade_Ponderado', 'Classe_Risco', 'Recomendacao']
cols = [c for c in cols if c in kpi_filt.columns]

st.dataframe(
    kpi_filt[cols].sort_values('Score_Criticidade_Ponderado', ascending=False).style.format({
        'Stock_Atual': '{:,.0f}',
        'Stock_Minimo': '{:,.0f}',
        'Stock_Reposicao': '{:,.0f}',
        'Saldo_Disponivel': '{:,.0f}',
        'Dias_Ate_Rutura_Com_OC': '{:.1f}',
        'Score_Criticidade_Ponderado': '{:.1f}',
    }).background_gradient(subset=['Score_Criticidade_Ponderado'], cmap='Reds'),
    use_container_width=True,
    hide_index=True,
    height=400,
)

render_download(kpi_filt, 'componentes_filtrado.csv', 'Exportar componentes filtrados')

render_footer()
