"""
Dashboard 5 — Inteligência Artificial
Previsões de rutura, recomendação ML de compras, anomalias.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import (
    load_ia_modelos, load_ia_rec_compras, load_ia_anomalias, load_prob_rutura
)
from utils.theme import (
    CUSTOM_CSS, PLOTLY_LAYOUT_DEFAULTS,
    COLOR_PRIMARY, COLOR_DANGER, COLOR_WARNING, COLOR_SUCCESS, COLOR_INFO
)
from utils.helpers import render_footer, header_with_refresh, render_download

st.set_page_config(page_title='Inteligência Artificial', page_icon='🤖', layout='wide')
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

header_with_refresh('Dashboard de Inteligência Artificial',
                     'Previsões de rutura, recomendação ML de compras, deteção de anomalias')

# Carga
ia_mdl = load_ia_modelos()
ia_rec = load_ia_rec_compras()
ia_anom = load_ia_anomalias()
ia_prob = load_prob_rutura()

# ============================================================
# Linha 1 — Performance dos modelos
# ============================================================
st.markdown('### Performance dos modelos preditivos')

c1, c2 = st.columns([2, 1])
with c1:
    st.dataframe(
        ia_mdl.style.format({
            'Accuracy': '{:.3f}', 'Precision': '{:.3f}', 'Recall': '{:.3f}',
            'F1': '{:.3f}', 'ROC_AUC': '{:.3f}', 'Avg_Precision': '{:.3f}',
        }).background_gradient(subset=['F1', 'ROC_AUC'], cmap='Greens'),
        use_container_width=True,
        hide_index=True,
    )

with c2:
    melhor = ia_mdl.loc[ia_mdl['F1'].idxmax()]
    st.success(
        f'**Modelo vencedor:** {melhor["Modelo"]}\n\n'
        f'F1 = {melhor["F1"]:.3f}, ROC-AUC = {melhor["ROC_AUC"]:.3f}'
    )

st.caption(
    'Métricas obtidas sobre a série temporal sintética (split temporal 80/20). '
    'Em produção sobre histórico real espera-se ROC-AUC entre 0.80 e 0.92, '
    'segundo benchmarks da literatura para problemas similares.'
)

st.markdown('---')

# ============================================================
# Linha 2 — Distribuição de probabilidade de rutura
# ============================================================
st.markdown('### Distribuição das probabilidades de rutura previstas')

c1, c2 = st.columns(2)

with c1:
    fig = px.histogram(
        ia_rec, x='Prob_Rutura_ML', nbins=30,
        color_discrete_sequence=[COLOR_PRIMARY],
        title='Histograma de probabilidades (modelo vencedor)',
    )
    fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS, height=380, bargap=0.05)
    fig.add_vline(x=0.5, line_dash='dash', line_color=COLOR_DANGER,
                  annotation_text='Limiar 0.5')
    st.plotly_chart(fig, use_container_width=True)

with c2:
    accao_counts = ia_rec['Accao'].value_counts().reset_index()
    accao_counts.columns = ['Acao', 'N']
    color_map = {
        'ENCOMENDAR': COLOR_DANGER,
        'PLANEAR ENCOMENDA': COLOR_WARNING,
        'OK': COLOR_SUCCESS,
    }
    fig = px.pie(
        accao_counts, values='N', names='Acao',
        title='Distribuição de ações recomendadas',
        color='Acao', color_discrete_map=color_map, hole=0.4,
    )
    fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS, height=380)
    fig.update_traces(textposition='inside', textinfo='value+percent')
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# Linha 3 — Top recomendações de compra
# ============================================================
st.markdown('### Top 20 recomendações de compra (Score de Prioridade ML)')

top20 = ia_rec.head(20).copy()
top20['Label'] = top20['Cod_Artigo'] + ' — ' + top20['Descricao'].str[:40]

color_map = {'ENCOMENDAR': COLOR_DANGER, 'PLANEAR ENCOMENDA': COLOR_WARNING, 'OK': COLOR_SUCCESS}
fig = px.bar(
    top20.sort_values('Score_Prioridade', ascending=True),
    x='Score_Prioridade', y='Label', orientation='h',
    color='Accao', color_discrete_map=color_map,
    hover_data=['Stock_Atual', 'Stock_Minimo', 'Prob_Rutura_ML',
                'Dias_ate_Rutura', 'Quantidade_a_Encomendar'],
)
fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS, height=600,
                  yaxis_title='', xaxis_title='Score de Prioridade (0-1)')
st.plotly_chart(fig, use_container_width=True)

st.markdown('### Tabela completa de recomendações ML')

# Filtros locais
c1, c2, c3 = st.columns(3)
with c1:
    accoes = ['(Todas)'] + sorted(ia_rec['Accao'].unique().tolist())
    sel_accao = st.selectbox('Ação', accoes, index=0)
with c2:
    prob_min = st.slider('Prob. mínima de rutura', 0.0, 1.0, 0.0, 0.05)
with c3:
    score_min = st.slider('Score de prioridade mínimo', 0.0, 1.0, 0.0, 0.05)

ia_rec_filt = ia_rec.copy()
if sel_accao != '(Todas)':
    ia_rec_filt = ia_rec_filt[ia_rec_filt['Accao'] == sel_accao]
ia_rec_filt = ia_rec_filt[
    (ia_rec_filt['Prob_Rutura_ML'] >= prob_min) &
    (ia_rec_filt['Score_Prioridade'] >= score_min)
]

cols_show = ['Cod_Artigo', 'Descricao', 'Stock_Atual', 'Stock_Minimo',
             'Consumo_30d', 'Centralidade_BOM', 'Prob_Rutura_ML',
             'Dias_ate_Rutura', 'Quantidade_a_Encomendar',
             'Data_Pedido_Optima', 'Score_Prioridade', 'Accao']
cols_show = [c for c in cols_show if c in ia_rec_filt.columns]

st.dataframe(
    ia_rec_filt[cols_show].style.format({
        'Stock_Atual': '{:,.0f}', 'Stock_Minimo': '{:,.0f}',
        'Consumo_30d': '{:,.1f}', 'Prob_Rutura_ML': '{:.1%}',
        'Dias_ate_Rutura': '{:.1f}', 'Quantidade_a_Encomendar': '{:,.0f}',
        'Score_Prioridade': '{:.3f}',
    }).background_gradient(subset=['Prob_Rutura_ML', 'Score_Prioridade'], cmap='Reds'),
    use_container_width=True,
    hide_index=True,
    height=400,
)

render_download(ia_rec_filt, 'ia_recomendacoes_filtrado.csv', 'Exportar recomendações')

# ============================================================
# Linha 4 — Anomalias
# ============================================================
st.markdown('---')
st.markdown('### Deteção de Anomalias (Isolation Forest)')

n_anom = int(ia_anom['E_Anomalia'].sum())
c1, c2, c3 = st.columns(3)
c1.metric('Anomalias detectadas', n_anom)
c2.metric('Total analisado', len(ia_anom))
c3.metric('Taxa', f"{n_anom/len(ia_anom)*100:.1f}%" if len(ia_anom) else '—')

# Scatter
fig = px.scatter(
    ia_anom,
    x='Ratio_Mean_30v60',
    y='Max_30_vs_Med',
    color='E_Anomalia',
    color_continuous_scale=[[0, COLOR_INFO], [1, COLOR_DANGER]],
    size='Score_Anomalia',
    hover_data=['Cod_Artigo', 'Descricao', 'Consumo_Med_30d',
                'Stock_vs_Consumo_Esperado'],
    title='Mapa de anomalias — outliers em vermelho',
)
fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS, height=450,
                  coloraxis_colorbar=dict(title='Anomalia'))
st.plotly_chart(fig, use_container_width=True)

# Tabela top anomalias
st.markdown('#### Top 15 anomalias (maior score)')
anom_top = ia_anom.nlargest(15, 'Score_Anomalia')
cols_anom = ['Cod_Artigo', 'Descricao', 'Ratio_Mean_30v60', 'Max_30_vs_Med',
             'Stock_vs_Consumo_Esperado', 'Score_Anomalia', 'E_Anomalia']
cols_anom = [c for c in cols_anom if c in anom_top.columns]

st.dataframe(
    anom_top[cols_anom].style.format({
        'Ratio_Mean_30v60': '{:.3f}',
        'Max_30_vs_Med': '{:.2f}',
        'Stock_vs_Consumo_Esperado': '{:.1f}',
        'Score_Anomalia': '{:.3f}',
    }).background_gradient(subset=['Score_Anomalia'], cmap='Reds'),
    use_container_width=True,
    hide_index=True,
)

render_download(ia_anom, 'anomalias.csv', 'Exportar todas as anomalias')

# ============================================================
# Disclaimer metodológico
# ============================================================
with st.expander('Notas metodológicas dos modelos'):
    st.markdown('''
**Modelo 1 — Previsão de Ruturas**

Classificação binária supervisionada. Target = rutura nos próximos 14 dias.
Features: cobertura implícita, ratio stock/mínimo, consumos médios em janelas 7/30/90 dias,
desvio-padrão a 30d, tendência 7v30, índice sazonal, ordens de compra pendentes,
centralidade na BOM, tipo de artigo (PA vs comp).

Três modelos comparados: Logistic Regression (baseline), Random Forest, XGBoost.
Split temporal 80/20 para evitar data leakage.

**Modelo 2 — Recomendação de Compras**

Pipeline em duas etapas: (1) modelo ML estima probabilidade de rutura; (2) regras de negócio
calculam quantidade óptima Q* = max(0, (Cob_Obj + Lead_Time) × μ × Safety_Factor − Stock − OC).

Score de prioridade = 0.40 × P(rutura) + 0.25 × urgência temporal + 0.20 × centralidade BOM
normalizada + 0.15 × violação de stock mínimo.

**Modelo 3 — Deteção de Anomalias**

Isolation Forest sobre features de comportamento de consumo:
razão consumo médio últimos 30d vs janela anterior, razão desvio-padrão,
pico máximo vs média, razão stock atual vs consumo esperado.

Contamination = 0.05 (assume 5% de anomalias esperadas; alinhado com benchmarks típicos).
    ''')

render_footer()
