"""
Dashboard 2 — Produto Acabado
Stock vs mínimo, saldo, cobertura, dias até rutura, drill-down por artigo.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import load_kpi_pa, load_bom
from utils.theme import (
    CUSTOM_CSS, CLASS_RISCO_COLORS, PLOTLY_LAYOUT_DEFAULTS,
    COLOR_PRIMARY, COLOR_DANGER, COLOR_WARNING, COLOR_SUCCESS, COLOR_SECONDARY
)
from utils.helpers import (
    render_footer, header_with_refresh, sidebar_filters_pa, render_download
)

st.set_page_config(page_title='Produto Acabado', page_icon='🍷', layout='wide')
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

header_with_refresh('Dashboard de Produto Acabado',
                     'Stock, cobertura e prioridade de produção por SKU')

# Carga
kpi_pa = load_kpi_pa()
bom = load_bom()

# Aplicar filtros via sidebar
kpi_filt = sidebar_filters_pa(kpi_pa)

# ============================================================
# KPIs no topo (filtrados)
# ============================================================
c1, c2, c3, c4, c5 = st.columns(5)

c1.metric('PA filtrados', f"{len(kpi_filt):,}",
          delta=f"{len(kpi_filt)-len(kpi_pa)} vs total" if len(kpi_filt) != len(kpi_pa) else None,
          delta_color='off')

stock_total = kpi_filt['Stock_Atual'].sum()
c2.metric('Stock total (unidades)', f"{stock_total:,.0f}")

n_critico = int((kpi_filt['Classe_Risco'].isin(['A_CRITICO', 'B_ALTO'])).sum())
c3.metric('Em risco alto/crítico', n_critico, delta_color='inverse')

cob_med = kpi_filt.loc[kpi_filt['Dias_Ate_Rutura_Com_OC'] < 999, 'Dias_Ate_Rutura_Com_OC'].median()
c4.metric('Cobertura mediana', f"{cob_med:.1f} dias" if pd.notna(cob_med) else '—')

n_produzir = int(kpi_filt['Recomendacao'].str.contains('PRODUZIR', na=False).sum())
c5.metric('A produzir urgente', n_produzir, delta_color='inverse')

st.markdown('---')

# ============================================================
# Linha 2 — Scatter de risco × cobertura
# ============================================================
st.markdown('### Mapa de risco — Score de Criticidade vs Cobertura')

scatter_df = kpi_filt[kpi_filt['Dias_Ate_Rutura_Com_OC'] < 200].copy()
scatter_df['Stock_Size'] = scatter_df['Stock_Atual'].clip(lower=0)
if len(scatter_df) > 0:
    fig = px.scatter(
        scatter_df,
        x='Dias_Ate_Rutura_Com_OC',
        y='Score_Criticidade',
        size='Stock_Size',
        color='Classe_Risco',
        color_discrete_map=CLASS_RISCO_COLORS,
        hover_data=['Cod_Artigo', 'Descricao', 'Stock_Atual', 'Stock_Minimo'],
        title='Cada bolha = 1 PA; eixo X = dias até rutura; tamanho = stock atual',
    )
    fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS, height=450)
    fig.add_vline(x=7, line_dash='dash', line_color=COLOR_DANGER,
                  annotation_text='Rutura iminente (7d)', annotation_position='top')
    fig.add_vline(x=30, line_dash='dot', line_color=COLOR_WARNING,
                  annotation_text='Cob. objectivo (30d)', annotation_position='top')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info('Sem PA dentro do filtro para apresentar no mapa.')

# ============================================================
# Linha 3 — Distribuição por subfamília
# ============================================================
c1, c2 = st.columns(2)

with c1:
    st.markdown('### Stock total por subfamília')
    sf_agg = kpi_filt.groupby('Subfamilia').agg(
        Stock_Total=('Stock_Atual', 'sum'),
        N_Artigos=('Cod_Artigo', 'count'),
    ).reset_index().sort_values('Stock_Total', ascending=True)
    if len(sf_agg) > 0:
        fig = px.bar(sf_agg, x='Stock_Total', y='Subfamilia',
                      orientation='h', color='N_Artigos',
                      color_continuous_scale='Burg',
                      title='Volume e número de artigos por subfamília')
        fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS, height=400)
        st.plotly_chart(fig, use_container_width=True)

with c2:
    st.markdown('### Distribuição de classes de risco')
    cls_agg = kpi_filt.groupby(['Subfamilia', 'Classe_Risco']).size().reset_index(name='N')
    if len(cls_agg) > 0:
        fig = px.bar(cls_agg, x='Subfamilia', y='N', color='Classe_Risco',
                      color_discrete_map=CLASS_RISCO_COLORS,
                      title='Composição de risco por subfamília')
        fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS, height=400, barmode='stack',
                          xaxis={'categoryorder': 'total descending'})
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# Linha 4 — Tabela detalhada com drill-down
# ============================================================
st.markdown('### Detalhe por artigo (filtrável)')

cols_display = ['Cod_Artigo', 'Descricao', 'Subfamilia', 'Stock_Atual', 'Stock_Minimo',
                'Saldo_Disponivel', 'Consumo_Diario_Implic', 'Dias_Ate_Rutura_Com_OC',
                'Score_Criticidade', 'Classe_Risco', 'Recomendacao']
cols_display = [c for c in cols_display if c in kpi_filt.columns]

st.dataframe(
    kpi_filt[cols_display].sort_values('Score_Criticidade', ascending=False).style.format({
        'Stock_Atual': '{:,.0f}',
        'Stock_Minimo': '{:,.0f}',
        'Saldo_Disponivel': '{:,.0f}',
        'Consumo_Diario_Implic': '{:.2f}',
        'Dias_Ate_Rutura_Com_OC': '{:.1f}',
        'Score_Criticidade': '{:.1f}',
    }).background_gradient(subset=['Score_Criticidade'], cmap='Reds'),
    use_container_width=True,
    hide_index=True,
    height=400,
)

render_download(kpi_filt, 'kpi_pa_filtrado.csv', 'Exportar PA filtrados')

# ============================================================
# Linha 5 — Drill-down: BOM do PA seleccionado
# ============================================================
st.markdown('---')
st.markdown('### Drill-down BOM por PA')

pa_options = sorted(kpi_filt['Cod_Artigo'].unique().tolist())
if pa_options:
    sel_pa = st.selectbox('Seleccionar PA para ver a sua BOM:', pa_options)
    bom_pa = bom[bom['Cod_PA'] == sel_pa]
    if len(bom_pa) > 0:
        st.dataframe(
            bom_pa[['Cod_Comp', 'Desc_Comp', 'Familia_Comp', 'SubFamilia_Comp',
                    'Consumo_Unit', 'Stock_Comp_BOM']].style.format({
                'Consumo_Unit': '{:.2f}',
                'Stock_Comp_BOM': '{:,.0f}',
            }),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(f'Total de componentes para este PA: {len(bom_pa)}')
    else:
        st.info(f'PA {sel_pa} não tem BOM Standard registada.')

render_footer()
