"""
Dashboard 6 — Simulador What-If (Extensão 3 do projeto)
Permite simulação interactiva de cenários:
1. Variação dos parâmetros globais (cobertura objectivo, lead time, safety)
2. Simulação por SKU específico (e se stock subir X%? e se consumo cair Y%?)
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import load_kpi_pa, load_kpi_comp
from utils.theme import (
    CUSTOM_CSS, CLASS_RISCO_COLORS, PLOTLY_LAYOUT_DEFAULTS,
    COLOR_PRIMARY, COLOR_DANGER, COLOR_WARNING, COLOR_SUCCESS, COLOR_SECONDARY
)
from utils.helpers import render_footer, header_with_refresh

st.set_page_config(page_title='Simulador', page_icon='🎛️', layout='wide')
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

header_with_refresh('Simulador de Cenários (What-If)',
                     'Simulação interactiva: parâmetros globais e variações por SKU')

# Carga
kpi_pa = load_kpi_pa()
kpi_comp = load_kpi_comp()

st.markdown('''
Este simulador permite testar duas dimensões de cenários:

1. **Cenário global**: alterar parâmetros operacionais (cobertura objectivo, lead time, safety factor)
   e ver o impacto agregado em número de PAs e componentes em risco
2. **Cenário por SKU**: simular variações pontuais (stock, consumo, ordens de compra) num artigo
   específico e ver como a sua classificação muda
''')

st.markdown('---')

# ============================================================
# Parte 1: Cenário Global
# ============================================================
st.markdown('## 1. Cenário global — variação de parâmetros operacionais')

c1, c2 = st.columns([1, 2])

with c1:
    st.markdown('### Parâmetros')
    cob_obj_pa = st.slider('Cobertura objectivo PA (dias)', 7, 90, 30, 1,
                            help='Stock objectivo expresso em dias de cobertura')
    cob_obj_comp = st.slider('Cobertura objectivo Comp (dias)', 7, 60, 21, 1)
    lead_time = st.slider('Lead time componentes (dias)', 7, 30, 14, 1,
                           help='Tempo médio entre encomenda e recepção')
    safety = st.slider('Safety factor', 1.0, 2.0, 1.2, 0.05,
                        help='Multiplicador de segurança sobre consumo médio')

    # Limiares de criticidade configuráveis
    st.markdown('#### Limiares de classe de risco')
    lim_critico = st.slider('Limiar A_CRITICO', 50, 95, 75)
    lim_alto = st.slider('Limiar B_ALTO', 25, lim_critico-1, min(50, lim_critico-1))
    lim_medio = st.slider('Limiar C_MEDIO', 5, lim_alto-1, min(25, lim_alto-1))

with c2:
    # Recalcular KPIs com novos parâmetros
    def reclassify(score, l_crit, l_alto, l_medio):
        if pd.isna(score) or score <= 0:
            return 'E_SEM_RISCO'
        if score >= l_crit:
            return 'A_CRITICO'
        if score >= l_alto:
            return 'B_ALTO'
        if score >= l_medio:
            return 'C_MEDIO'
        return 'D_BAIXO'

    # PA: recalcular consumo, dias_rutura, score
    pa_sim = kpi_pa.copy()
    pa_sim['Consumo_Sim'] = np.where(
        pa_sim['Stock_Minimo'] > 0,
        pa_sim['Stock_Minimo'] / cob_obj_pa,
        np.nan
    )
    pa_sim['Saldo'] = pa_sim['Stock_Atual'] + pa_sim['OC_Qtd_Total']
    pa_sim['Dias_Rutura_Sim'] = np.where(
        pa_sim['Consumo_Sim'] > 0,
        pa_sim['Saldo'] / pa_sim['Consumo_Sim'],
        999
    )
    pa_sim['Score_Sim'] = np.where(
        pa_sim['Dias_Rutura_Sim'] >= 999, 0,
        np.clip(100 * (1 - pa_sim['Dias_Rutura_Sim'] / cob_obj_pa), 0, 100)
    )
    pa_sim['Classe_Sim'] = pa_sim['Score_Sim'].apply(
        lambda s: reclassify(s, lim_critico, lim_alto, lim_medio)
    )

    # Componentes
    comp_sim = kpi_comp.copy()
    comp_sim['Consumo_Sim'] = np.where(
        (comp_sim['Stock_Reposicao'] > comp_sim['Stock_Minimo']) & (comp_sim['Stock_Reposicao'] > 0),
        (comp_sim['Stock_Reposicao'] - comp_sim['Stock_Minimo']) / lead_time,
        np.where(comp_sim['Stock_Minimo'] > 0,
                 comp_sim['Stock_Minimo'] / lead_time,
                 np.nan)
    )
    comp_sim['Saldo'] = comp_sim['Stock_Atual'] + comp_sim['OC_Qtd_Total']
    comp_sim['Dias_Rutura_Sim'] = np.where(
        comp_sim['Consumo_Sim'] > 0,
        comp_sim['Saldo'] / comp_sim['Consumo_Sim'],
        999
    )
    comp_sim['Score_Sim'] = np.where(
        comp_sim['Dias_Rutura_Sim'] >= 999, 0,
        np.clip(100 * (1 - comp_sim['Dias_Rutura_Sim'] / cob_obj_comp), 0, 100)
    )
    comp_sim['Score_Pond_Sim'] = np.clip(
        comp_sim['Score_Sim'] * (1 + comp_sim['Centralidade_BOM']/20), 0, 100
    )
    comp_sim['Classe_Sim'] = comp_sim['Score_Pond_Sim'].apply(
        lambda s: reclassify(s, lim_critico, lim_alto, lim_medio)
    )

    # Painel comparativo: actual vs simulado
    st.markdown('### Impacto do cenário simulado')

    # Distribuição PA
    pa_orig = kpi_pa['Classe_Risco'].value_counts()
    pa_new = pa_sim['Classe_Sim'].value_counts()
    classes_ordem = ['A_CRITICO', 'B_ALTO', 'C_MEDIO', 'D_BAIXO', 'E_SEM_RISCO']

    comp_df = pd.DataFrame({
        'Classe': classes_ordem,
        'Actual': [int(pa_orig.get(c, 0)) for c in classes_ordem],
        'Simulado': [int(pa_new.get(c, 0)) for c in classes_ordem],
    })
    comp_df['Δ'] = comp_df['Simulado'] - comp_df['Actual']

    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown('#### Produto Acabado')
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Actual', x=comp_df['Classe'], y=comp_df['Actual'],
                              marker_color=COLOR_NEUTRAL if (COLOR_NEUTRAL := '#6B7280') else '#6B7280'))
        fig.add_trace(go.Bar(name='Simulado', x=comp_df['Classe'], y=comp_df['Simulado'],
                              marker_color=COLOR_PRIMARY))
        fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS, barmode='group', height=300,
                          title='Distribuição de classes (PA)')
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(comp_df, use_container_width=True, hide_index=True)

    with cc2:
        st.markdown('#### Componentes')
        comp_orig = kpi_comp['Classe_Risco'].value_counts()
        comp_new = comp_sim['Classe_Sim'].value_counts()
        comp_df2 = pd.DataFrame({
            'Classe': classes_ordem,
            'Actual': [int(comp_orig.get(c, 0)) for c in classes_ordem],
            'Simulado': [int(comp_new.get(c, 0)) for c in classes_ordem],
        })
        comp_df2['Δ'] = comp_df2['Simulado'] - comp_df2['Actual']

        fig = go.Figure()
        fig.add_trace(go.Bar(name='Actual', x=comp_df2['Classe'], y=comp_df2['Actual'],
                              marker_color='#6B7280'))
        fig.add_trace(go.Bar(name='Simulado', x=comp_df2['Classe'], y=comp_df2['Simulado'],
                              marker_color=COLOR_SECONDARY))
        fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS, barmode='group', height=300,
                          title='Distribuição de classes (Componentes)')
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(comp_df2, use_container_width=True, hide_index=True)

# Métricas-resumo do cenário
st.markdown('### Síntese do cenário')
m1, m2, m3, m4 = st.columns(4)

n_pa_critico_orig = int((kpi_pa['Classe_Risco'].isin(['A_CRITICO', 'B_ALTO'])).sum())
n_pa_critico_sim = int((pa_sim['Classe_Sim'].isin(['A_CRITICO', 'B_ALTO'])).sum())
delta_pa = n_pa_critico_sim - n_pa_critico_orig

n_comp_critico_orig = int((kpi_comp['Classe_Risco'].isin(['A_CRITICO', 'B_ALTO'])).sum())
n_comp_critico_sim = int((comp_sim['Classe_Sim'].isin(['A_CRITICO', 'B_ALTO'])).sum())
delta_comp = n_comp_critico_sim - n_comp_critico_orig

m1.metric('PA em risco alto/crítico (actual)', n_pa_critico_orig)
m2.metric('PA em risco alto/crítico (simulado)', n_pa_critico_sim,
          delta=f"{delta_pa:+d}", delta_color='inverse')
m3.metric('Componentes em risco (actual)', n_comp_critico_orig)
m4.metric('Componentes em risco (simulado)', n_comp_critico_sim,
          delta=f"{delta_comp:+d}", delta_color='inverse')

# ============================================================
# Parte 2: Cenário por SKU
# ============================================================
st.markdown('---')
st.markdown('## 2. Cenário por SKU — variações pontuais')

st.caption(
    'Selecciona um SKU e simula variações de stock, consumo médio e ordens de compra '
    'para ver como muda a sua classificação.'
)

c1, c2 = st.columns([1, 2])

with c1:
    tipo_sku = st.radio('Tipo de SKU', ['Produto Acabado', 'Componente'], horizontal=True)
    if tipo_sku == 'Produto Acabado':
        df_pick = kpi_pa
    else:
        df_pick = kpi_comp
    df_pick = df_pick.sort_values('Score_Criticidade' if 'Score_Criticidade' in df_pick.columns
                                    else 'Score_Criticidade_Ponderado', ascending=False)
    options = (df_pick['Cod_Artigo'] + ' — ' + df_pick['Descricao'].str[:50]).tolist()
    sel = st.selectbox('SKU a simular:', options, index=0)
    cod_sel = sel.split(' — ')[0]

    art = df_pick[df_pick['Cod_Artigo'] == cod_sel].iloc[0]

    st.markdown('### Variações what-if')
    delta_stock = st.slider('Δ Stock atual (%)', -50, 200, 0, 5,
                             help='+20% simula entrada de mercadoria; -30% simula consumo extra')
    delta_consumo = st.slider('Δ Consumo médio (%)', -50, 100, 0, 5,
                                help='+50% simula campanha promocional')
    delta_oc = st.slider('Δ Ordens de compra (%)', -100, 300, 0, 10,
                          help='+100% simula encomenda urgente extra')

with c2:
    # Cenário base e simulado
    stock_base = float(art['Stock_Atual'])
    stock_min = float(art['Stock_Minimo'])
    oc_base = float(art.get('OC_Qtd_Total', 0))
    consumo_base = float(art.get('Consumo_Diario_Implic', 0)) if pd.notna(art.get('Consumo_Diario_Implic', 0)) else 0

    stock_sim = stock_base * (1 + delta_stock/100)
    consumo_sim = consumo_base * (1 + delta_consumo/100)
    oc_sim = oc_base * (1 + delta_oc/100)

    saldo_base = stock_base + oc_base
    saldo_sim = stock_sim + oc_sim

    dias_base = saldo_base / consumo_base if consumo_base > 0 else 999
    dias_sim = saldo_sim / consumo_sim if consumo_sim > 0 else 999

    cob_obj_use = cob_obj_pa if tipo_sku == 'Produto Acabado' else cob_obj_comp
    score_base = max(0, min(100, 100 * (1 - dias_base / cob_obj_use))) if dias_base < 999 else 0
    score_sim = max(0, min(100, 100 * (1 - dias_sim / cob_obj_use))) if dias_sim < 999 else 0

    classe_base = reclassify(score_base, lim_critico, lim_alto, lim_medio)
    classe_sim = reclassify(score_sim, lim_critico, lim_alto, lim_medio)

    # Painel comparativo
    st.markdown(f'### {cod_sel}')
    st.caption(art['Descricao'])

    cc1, cc2 = st.columns(2)

    with cc1:
        st.markdown('#### Estado actual')
        st.metric('Stock', f"{stock_base:,.0f}")
        st.metric('Consumo médio diário', f"{consumo_base:,.2f}")
        st.metric('Ordens de compra', f"{oc_base:,.0f}")
        st.metric('Dias até rutura', f"{dias_base:.1f}" if dias_base < 999 else 'N/D')
        st.metric('Score', f"{score_base:.1f}")
        st.markdown(f'**Classe:** :red[{classe_base}]' if classe_base in ('A_CRITICO','B_ALTO')
                    else f'**Classe:** {classe_base}')

    with cc2:
        st.markdown('#### Estado simulado')
        st.metric('Stock', f"{stock_sim:,.0f}",
                  delta=f"{stock_sim-stock_base:+,.0f}")
        st.metric('Consumo médio diário', f"{consumo_sim:,.2f}",
                  delta=f"{consumo_sim-consumo_base:+,.2f}", delta_color='inverse')
        st.metric('Ordens de compra', f"{oc_sim:,.0f}",
                  delta=f"{oc_sim-oc_base:+,.0f}")
        st.metric('Dias até rutura',
                  f"{dias_sim:.1f}" if dias_sim < 999 else 'N/D',
                  delta=f"{(dias_sim-dias_base):+.1f}" if dias_sim < 999 and dias_base < 999 else None)
        st.metric('Score', f"{score_sim:.1f}",
                  delta=f"{score_sim-score_base:+.1f}", delta_color='inverse')
        st.markdown(f'**Classe:** :red[{classe_sim}]' if classe_sim in ('A_CRITICO','B_ALTO')
                    else f'**Classe:** {classe_sim}')

    # Gauge visual do score
    fig = go.Figure(go.Indicator(
        mode='gauge+number+delta',
        value=score_sim,
        delta={'reference': score_base, 'increasing': {'color': COLOR_DANGER},
               'decreasing': {'color': COLOR_SUCCESS}},
        title={'text': 'Score de Criticidade (simulado)'},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': COLOR_PRIMARY},
            'steps': [
                {'range': [0, lim_medio], 'color': '#86EFAC'},
                {'range': [lim_medio, lim_alto], 'color': '#FFE699'},
                {'range': [lim_alto, lim_critico], 'color': COLOR_WARNING},
                {'range': [lim_critico, 100], 'color': COLOR_DANGER},
            ],
        }
    ))
    fig.update_layout(height=300, margin={'l': 20, 'r': 20, 't': 50, 'b': 20})
    st.plotly_chart(fig, use_container_width=True)

st.markdown('---')
st.info(
    '**Notas metodológicas:** '
    '(1) O cenário global recalcula os scores e classes a partir das fórmulas base do modelo, '
    'mantendo Stock_Mínimo, Stock_Reposição e Stock_Atual constantes. '
    '(2) O cenário por SKU recalcula apenas para o artigo seleccionado. '
    '(3) Os limiares de classe são configuráveis para análise de sensibilidade.'
)

render_footer()
