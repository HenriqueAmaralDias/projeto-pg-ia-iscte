"""
Dashboard 1 — Executivo
KPIs globais, semáforo de risco, top alertas.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import (
    load_kpi_pa, load_kpi_comp, load_alertas, load_ecf, load_mrp_agg
)
from utils.theme import (
    CUSTOM_CSS, CLASS_RISCO_COLORS, PLOTLY_LAYOUT_DEFAULTS,
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_DANGER, COLOR_WARNING, COLOR_SUCCESS
)
from utils.helpers import render_footer, header_with_refresh, render_download

st.set_page_config(page_title='Executivo', page_icon='📊', layout='wide')
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

header_with_refresh('Dashboard Executivo',
                     'Visão consolidada para gestão | atualizado em tempo real')

# Carga
kpi_pa = load_kpi_pa()
kpi_comp = load_kpi_comp()
alertas = load_alertas()
ecf = load_ecf()
mrp = load_mrp_agg()

# ============================================================
# Linha 1 — KPIs principais (cartões)
# ============================================================
st.markdown('### Indicadores-chave')

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric('PA totais', f"{len(kpi_pa):,}")
c2.metric('Componentes totais', f"{len(kpi_comp):,}")

n_rupt_pa = int((kpi_pa['Dias_Ate_Rutura_Com_OC'] < 7).sum())
c3.metric('PA em rutura ≤7d', n_rupt_pa,
          delta=f"{(n_rupt_pa/len(kpi_pa)*100):.1f}%",
          delta_color='inverse')

n_rupt_comp = int((kpi_comp['Dias_Ate_Rutura_Com_OC'] < 14).sum())
c4.metric('Componentes em rutura ≤14d', n_rupt_comp,
          delta=f"{(n_rupt_comp/len(kpi_comp)*100):.1f}%",
          delta_color='inverse')

q_encomendar = int(len(mrp[mrp['Encomendar'] == 1])) if 'Encomendar' in mrp.columns else 0
c5.metric('Componentes a encomendar (MRP)', q_encomendar)

# ============================================================
# Linha 2 — Cobertura mediana e ECFs
# ============================================================
c1, c2, c3, c4 = st.columns(4)

cob_pa = kpi_pa.loc[kpi_pa['Dias_Ate_Rutura_Com_OC'] < 999, 'Dias_Ate_Rutura_Com_OC']
cob_comp = kpi_comp.loc[kpi_comp['Dias_Ate_Rutura_Com_OC'] < 999, 'Dias_Ate_Rutura_Com_OC']

c1.metric('Cobertura mediana PA',
          f"{cob_pa.median():.1f} dias" if len(cob_pa) else '—')
c2.metric('Cobertura mediana Comp',
          f"{cob_comp.median():.1f} dias" if len(cob_comp) else '—')
c3.metric('ECFs activas', len(ecf))

n_ecf_atrasadas = int((ecf['Dias_Para_Entrega'] < 0).sum()) if 'Dias_Para_Entrega' in ecf.columns else 0
c4.metric('ECFs com data passada', n_ecf_atrasadas,
          delta='Atenção' if n_ecf_atrasadas > 0 else 'OK',
          delta_color='inverse' if n_ecf_atrasadas > 0 else 'normal')

st.markdown('---')

# ============================================================
# Linha 3 — Semáforos de risco (donuts PA + Comp)
# ============================================================
st.markdown('### Distribuição de risco')

c1, c2 = st.columns(2)

with c1:
    dist_pa = kpi_pa['Classe_Risco'].value_counts().reset_index()
    dist_pa.columns = ['Classe', 'Quantidade']
    fig = px.pie(dist_pa, values='Quantidade', names='Classe',
                  title='Produto Acabado por classe de risco',
                  color='Classe',
                  color_discrete_map=CLASS_RISCO_COLORS,
                  hole=0.5)
    fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS, showlegend=True)
    fig.update_traces(textposition='inside', textinfo='value+percent')
    st.plotly_chart(fig, use_container_width=True)

with c2:
    dist_comp = kpi_comp['Classe_Risco'].value_counts().reset_index()
    dist_comp.columns = ['Classe', 'Quantidade']
    fig = px.pie(dist_comp, values='Quantidade', names='Classe',
                  title='Componentes por classe de risco',
                  color='Classe',
                  color_discrete_map=CLASS_RISCO_COLORS,
                  hole=0.5)
    fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS, showlegend=True)
    fig.update_traces(textposition='inside', textinfo='value+percent')
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# Linha 4 — Top alertas
# ============================================================
st.markdown('### Top 15 alertas operacionais (prioridade descendente)')

top_alertas = alertas.head(15)[
    ['Tipo', 'Cod_Artigo', 'Descricao', 'Subfamilia', 'Stock_Atual',
     'Stock_Minimo', 'Dias_Ate_Rutura_Com_OC', 'Score_Criticidade',
     'Classe_Risco', 'Recomendacao']
].copy()

st.dataframe(
    top_alertas.style.format({
        'Stock_Atual': '{:,.0f}',
        'Stock_Minimo': '{:,.0f}',
        'Dias_Ate_Rutura_Com_OC': '{:.1f}',
        'Score_Criticidade': '{:.1f}',
    }).background_gradient(subset=['Score_Criticidade'], cmap='Reds'),
    use_container_width=True,
    hide_index=True,
)

render_download(alertas, 'alertas_executivo.csv', 'Exportar todos os alertas')

# ============================================================
# Linha 5 — Pipeline ECF
# ============================================================
st.markdown('### Pipeline de Ordens de Compra (próximas entregas)')

ecf_futuro = ecf[ecf['Dias_Para_Entrega'] >= 0].copy() if 'Dias_Para_Entrega' in ecf.columns else ecf.copy()
if len(ecf_futuro) > 0 and 'Data_1a_Entrega' in ecf_futuro.columns:
    ecf_futuro = ecf_futuro.sort_values('Data_1a_Entrega').head(20)
    ecf_futuro['Data_1a_Entrega'] = pd.to_datetime(ecf_futuro['Data_1a_Entrega']).dt.strftime('%Y-%m-%d')
    cols_show = ['Cod_Artigo', 'Descricao', 'Data_1a_Entrega',
                 'Dias_Para_Entrega', 'Qtd_1a_ECF', 'Num_1a_ECF']
    cols_show = [c for c in cols_show if c in ecf_futuro.columns]
    st.dataframe(
        ecf_futuro[cols_show].style.format({
            'Qtd_1a_ECF': '{:,.0f}',
            'Dias_Para_Entrega': '{:.0f}',
        }),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info('Sem ordens de compra futuras a apresentar.')

render_footer()
