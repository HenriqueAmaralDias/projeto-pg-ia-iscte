"""
Dashboard 6 — Simulador What-If (Extensão)
Permite simulação interactiva de cenários:
1. Cenário global — parâmetros operacionais
2. Cenário por SKU — variações pontuais
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import load_kpi_pa, load_kpi_comp
from utils.theme import (
    CUSTOM_CSS, CLASS_RISCO_COLORS, PLOTLY_LAYOUT_DEFAULTS,
    COLOR_PRIMARY, COLOR_DANGER, COLOR_WARNING, COLOR_SUCCESS, COLOR_SECONDARY,
    COLOR_NEUTRAL,
)
from utils.helpers import render_footer, header_with_refresh

st.set_page_config(page_title='Simulador', page_icon='🎛️', layout='wide')
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

header_with_refresh(
    'Simulador de Cenários (What-If)',
    'Simulação interactiva: parâmetros globais e variações por SKU'
)

# Carga
kpi_pa = load_kpi_pa()
kpi_comp = load_kpi_comp()

# ============================================================
# Defaults canónicos (correspondem ao modelo de dados)
# ============================================================
DEFAULTS = {
    'cob_obj_pa': 30,
    'cob_obj_comp': 21,
    'lead_time': 14,
    'safety': 1.20,
    'lim_critico': 75,
    'lim_alto': 50,
    'lim_medio': 25,
}

# Cenários pré-definidos
PRESETS = {
    'Conservador':  {'cob_obj_pa': 45, 'cob_obj_comp': 30, 'lead_time': 21, 'safety': 1.50,
                     'lim_critico': 65, 'lim_alto': 40, 'lim_medio': 20},
    'Equilibrado':  DEFAULTS.copy(),
    'Agressivo':    {'cob_obj_pa': 15, 'cob_obj_comp': 14, 'lead_time': 10, 'safety': 1.00,
                     'lim_critico': 85, 'lim_alto': 60, 'lim_medio': 30},
}


def init_session():
    for k, v in DEFAULTS.items():
        st.session_state.setdefault(k, v)


def apply_preset(preset_name):
    for k, v in PRESETS[preset_name].items():
        st.session_state[k] = v


def reset_defaults():
    apply_preset('Equilibrado')


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


init_session()

# ============================================================
# Introdução
# ============================================================
st.markdown("""
Esta página permite testar **duas dimensões** de cenários:

| Dimensão | O que faz | Quando usar |
|---|---|---|
| **1. Cenário global** | Altera parâmetros operacionais (cobertura, lead time, safety) e recalcula a classificação de todos os PA e componentes | Análise de sensibilidade da política de gestão |
| **2. Cenário por SKU** | Simula variações pontuais (stock, consumo, OC) num artigo específico | Negociação com fornecedor, simulação de campanha |
""")

st.markdown('---')

# ============================================================
# Parte 1 — Cenário Global
# ============================================================
st.markdown('## 1. Cenário global')

# Barra de presets + reset
cprs1, cprs2, cprs3, cprs4, _ = st.columns([1, 1, 1, 1, 4])
with cprs1:
    if st.button('🛡️ Conservador', use_container_width=True,
                 help='Cobertura PA 45d, comp 30d, lead 21d, safety 1.5×, limiares mais sensíveis'):
        apply_preset('Conservador')
        st.rerun()
with cprs2:
    if st.button('⚖️ Equilibrado', use_container_width=True,
                 help='Defaults: cobertura PA 30d, comp 21d, lead 14d, safety 1.2×'):
        apply_preset('Equilibrado')
        st.rerun()
with cprs3:
    if st.button('⚡ Agressivo', use_container_width=True,
                 help='Cobertura PA 15d, comp 14d, lead 10d, safety 1.0×, limiares mais tolerantes'):
        apply_preset('Agressivo')
        st.rerun()
with cprs4:
    if st.button('↺ Reset', use_container_width=True,
                 help='Voltar aos valores do modelo (Equilibrado)'):
        reset_defaults()
        st.rerun()

# Indicador de cenário desviado dos defaults
diffs = sum(1 for k, v in DEFAULTS.items() if st.session_state[k] != v)
if diffs > 0:
    st.caption(f'**Cenário alterado**: {diffs} parâmetro(s) diferente(s) do default')

c1, c2 = st.columns([1, 2])

with c1:
    with st.expander('Parâmetros operacionais', expanded=True):
        cob_obj_pa = st.slider(
            'Cobertura objectivo PA (dias)', 7, 90, key='cob_obj_pa', step=1,
            help='Quantos dias de cobertura o stock de PA deve garantir. Subir relaxa, descer aperta.'
        )
        cob_obj_comp = st.slider(
            'Cobertura objectivo Comp (dias)', 7, 60, key='cob_obj_comp', step=1,
            help='Idem para componentes. Tipicamente menor que PA porque depende do lead time.'
        )
        lead_time = st.slider(
            'Lead time componentes (dias)', 7, 30, key='lead_time', step=1,
            help='Tempo médio entre encomenda e recepção. Subir aumenta consumo implícito derivado.'
        )
        safety = st.slider(
            'Safety factor', 1.0, 2.0, key='safety', step=0.05,
            help='Multiplicador de segurança sobre consumo médio. 1.2 = +20% margem. Subir torna mais artigos críticos.'
        )

    with st.expander('Limiares de classe de risco', expanded=False):
        lim_critico = st.slider(
            'Limiar A_CRITICO', 50, 95, key='lim_critico',
            help='Score mínimo para classificar como A_CRITICO (default 75)'
        )
        lim_alto = st.slider(
            'Limiar B_ALTO', 25, lim_critico - 1, key='lim_alto',
            help='Score mínimo para B_ALTO (default 50)'
        )
        lim_medio = st.slider(
            'Limiar C_MEDIO', 5, lim_alto - 1, key='lim_medio',
            help='Score mínimo para C_MEDIO (default 25)'
        )

    # Card de instruções
    st.info(
        '💡 **Interpretação rápida**\n\n'
        '- Mais artigos críticos = política mais conservadora detecta mais risco\n'
        '- Menos artigos críticos = política tolera mais cobertura curta\n'
        '- O **safety factor** multiplica o consumo, encurtando cobertura efectiva'
    )

with c2:
    # ============================================================
    # Recalcular KPIs com novos parâmetros
    # Safety factor: multiplica consumo → reduz cobertura efectiva → mais críticos
    # ============================================================

    # PA
    pa_sim = kpi_pa.copy()
    pa_sim['Consumo_Base'] = np.where(
        pa_sim['Stock_Minimo'] > 0,
        pa_sim['Stock_Minimo'] / cob_obj_pa,
        np.nan
    )
    pa_sim['Consumo_Efectivo'] = pa_sim['Consumo_Base'] * safety  # ← safety aplicado
    pa_sim['Saldo'] = pa_sim['Stock_Atual'] + pa_sim['OC_Qtd_Total']
    pa_sim['Dias_Rutura_Sim'] = np.where(
        pa_sim['Consumo_Efectivo'] > 0,
        pa_sim['Saldo'] / pa_sim['Consumo_Efectivo'],
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
    comp_sim['Consumo_Base'] = np.where(
        (comp_sim['Stock_Reposicao'] > comp_sim['Stock_Minimo']) & (comp_sim['Stock_Reposicao'] > 0),
        (comp_sim['Stock_Reposicao'] - comp_sim['Stock_Minimo']) / lead_time,
        np.where(comp_sim['Stock_Minimo'] > 0,
                 comp_sim['Stock_Minimo'] / lead_time,
                 np.nan)
    )
    comp_sim['Consumo_Efectivo'] = comp_sim['Consumo_Base'] * safety  # ← safety aplicado
    comp_sim['Saldo'] = comp_sim['Stock_Atual'] + comp_sim['OC_Qtd_Total']
    comp_sim['Dias_Rutura_Sim'] = np.where(
        comp_sim['Consumo_Efectivo'] > 0,
        comp_sim['Saldo'] / comp_sim['Consumo_Efectivo'],
        999
    )
    comp_sim['Score_Sim'] = np.where(
        comp_sim['Dias_Rutura_Sim'] >= 999, 0,
        np.clip(100 * (1 - comp_sim['Dias_Rutura_Sim'] / cob_obj_comp), 0, 100)
    )
    comp_sim['Score_Pond_Sim'] = np.clip(
        comp_sim['Score_Sim'] * (1 + comp_sim['Centralidade_BOM'] / 20), 0, 100
    )
    comp_sim['Classe_Sim'] = comp_sim['Score_Pond_Sim'].apply(
        lambda s: reclassify(s, lim_critico, lim_alto, lim_medio)
    )

    # Painel comparativo
    st.markdown('### Impacto do cenário simulado')

    classes_ordem = ['A_CRITICO', 'B_ALTO', 'C_MEDIO', 'D_BAIXO', 'E_SEM_RISCO']

    pa_orig = kpi_pa['Classe_Risco'].value_counts()
    pa_new = pa_sim['Classe_Sim'].value_counts()
    pa_df = pd.DataFrame({
        'Classe': classes_ordem,
        'Actual': [int(pa_orig.get(c, 0)) for c in classes_ordem],
        'Simulado': [int(pa_new.get(c, 0)) for c in classes_ordem],
    })
    pa_df['Δ'] = pa_df['Simulado'] - pa_df['Actual']

    comp_orig = kpi_comp['Classe_Risco'].value_counts()
    comp_new = comp_sim['Classe_Sim'].value_counts()
    comp_df2 = pd.DataFrame({
        'Classe': classes_ordem,
        'Actual': [int(comp_orig.get(c, 0)) for c in classes_ordem],
        'Simulado': [int(comp_new.get(c, 0)) for c in classes_ordem],
    })
    comp_df2['Δ'] = comp_df2['Simulado'] - comp_df2['Actual']

    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown('#### Produto Acabado')
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Actual', x=pa_df['Classe'], y=pa_df['Actual'],
                              marker_color='#6B7280'))
        fig.add_trace(go.Bar(name='Simulado', x=pa_df['Classe'], y=pa_df['Simulado'],
                              marker_color=COLOR_PRIMARY))
        fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS, barmode='group', height=300,
                          title='Distribuição de classes (PA)')
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(pa_df, use_container_width=True, hide_index=True)

    with cc2:
        st.markdown('#### Componentes')
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Actual', x=comp_df2['Classe'], y=comp_df2['Actual'],
                              marker_color='#6B7280'))
        fig.add_trace(go.Bar(name='Simulado', x=comp_df2['Classe'], y=comp_df2['Simulado'],
                              marker_color=COLOR_SECONDARY))
        fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS, barmode='group', height=300,
                          title='Distribuição de classes (Componentes)')
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(comp_df2, use_container_width=True, hide_index=True)

# Métricas-resumo do cenário (delta vs actual)
st.markdown('### Síntese do impacto')
m1, m2, m3, m4 = st.columns(4)

n_pa_critico_orig = int(kpi_pa['Classe_Risco'].isin(['A_CRITICO', 'B_ALTO']).sum())
n_pa_critico_sim = int(pa_sim['Classe_Sim'].isin(['A_CRITICO', 'B_ALTO']).sum())
delta_pa = n_pa_critico_sim - n_pa_critico_orig

n_comp_critico_orig = int(kpi_comp['Classe_Risco'].isin(['A_CRITICO', 'B_ALTO']).sum())
n_comp_critico_sim = int(comp_sim['Classe_Sim'].isin(['A_CRITICO', 'B_ALTO']).sum())
delta_comp = n_comp_critico_sim - n_comp_critico_orig

m1.metric('PA risco alto/crítico (actual)', n_pa_critico_orig)
m2.metric('PA risco alto/crítico (simulado)', n_pa_critico_sim,
          delta=f'{delta_pa:+d}', delta_color='inverse')
m3.metric('Componentes em risco (actual)', n_comp_critico_orig)
m4.metric('Componentes em risco (simulado)', n_comp_critico_sim,
          delta=f'{delta_comp:+d}', delta_color='inverse')

# ============================================================
# Parte 2 — Cenário por SKU
# ============================================================
st.markdown('---')
st.markdown('## 2. Cenário por SKU')

st.caption(
    'Selecciona um SKU e simula variações pontuais para ver como muda a sua classificação. '
    'Os parâmetros globais acima (cobertura, safety) continuam a aplicar-se a este SKU.'
)

c1, c2 = st.columns([1, 2])

with c1:
    tipo_sku = st.radio('Tipo de SKU', ['Produto Acabado', 'Componente'],
                         horizontal=True, key='tipo_sku')
    df_pick = kpi_pa if tipo_sku == 'Produto Acabado' else kpi_comp
    score_col = 'Score_Criticidade' if 'Score_Criticidade' in df_pick.columns else 'Score_Criticidade_Ponderado'
    df_pick = df_pick.sort_values(score_col, ascending=False)
    options = (df_pick['Cod_Artigo'] + ' — ' + df_pick['Descricao'].str[:50]).tolist()
    sel = st.selectbox('SKU (ordenado por score actual descendente):', options, index=0, key='sku_sel')
    cod_sel = sel.split(' — ')[0]
    art = df_pick[df_pick['Cod_Artigo'] == cod_sel].iloc[0]

    st.markdown('#### Variações what-if')

    # Reset variations
    if st.button('↺ Limpar variações', use_container_width=True):
        for k in ('delta_stock', 'delta_consumo', 'delta_oc'):
            st.session_state[k] = 0
        st.rerun()

    delta_stock = st.slider(
        'Δ Stock atual (%)', -50, 200, key='delta_stock', step=5,
        help='+20% simula entrada extra de mercadoria; −30% simula consumo extra desconhecido'
    )
    delta_consumo = st.slider(
        'Δ Consumo médio (%)', -50, 100, key='delta_consumo', step=5,
        help='+50% simula campanha promocional ou aumento de procura'
    )
    delta_oc = st.slider(
        'Δ Ordens de compra (%)', -100, 300, key='delta_oc', step=10,
        help='+100% simula encomenda urgente extra; −100% cancela todas as OCs pendentes'
    )

with c2:
    # Estado base e simulado
    stock_base = float(art['Stock_Atual'])
    stock_min = float(art['Stock_Minimo'])
    oc_base = float(art.get('OC_Qtd_Total', 0))
    consumo_implic = art.get('Consumo_Diario_Implic', 0)
    consumo_base = float(consumo_implic) if pd.notna(consumo_implic) else 0.0
    consumo_efectivo_base = consumo_base * safety  # safety global aplica-se aqui também

    stock_sim = stock_base * (1 + delta_stock / 100)
    consumo_sim = consumo_base * (1 + delta_consumo / 100)
    consumo_efectivo_sim = consumo_sim * safety
    oc_sim = oc_base * (1 + delta_oc / 100)

    saldo_base = stock_base + oc_base
    saldo_sim = stock_sim + oc_sim

    dias_base = saldo_base / consumo_efectivo_base if consumo_efectivo_base > 0 else 999
    dias_sim = saldo_sim / consumo_efectivo_sim if consumo_efectivo_sim > 0 else 999

    cob_obj_use = cob_obj_pa if tipo_sku == 'Produto Acabado' else cob_obj_comp
    score_base = max(0, min(100, 100 * (1 - dias_base / cob_obj_use))) if dias_base < 999 else 0
    score_sim = max(0, min(100, 100 * (1 - dias_sim / cob_obj_use))) if dias_sim < 999 else 0

    classe_base = reclassify(score_base, lim_critico, lim_alto, lim_medio)
    classe_sim = reclassify(score_sim, lim_critico, lim_alto, lim_medio)

    # Painel
    st.markdown(f'### {cod_sel}')
    st.caption(art['Descricao'])

    # Aviso se SKU não tem consumo definido
    if consumo_base <= 0:
        st.warning('Este SKU não tem stock mínimo definido → consumo implícito = 0. '
                   'Simulação limitada (score sempre 0).')

    cc1, cc2 = st.columns(2)

    with cc1:
        st.markdown('#### Estado actual')
        st.metric('Stock atual', f'{stock_base:,.0f}')
        st.metric('Consumo médio diário', f'{consumo_base:,.2f}',
                  help=f'Consumo efectivo (×{safety:.2f} safety): {consumo_efectivo_base:.2f}')
        st.metric('Ordens de compra', f'{oc_base:,.0f}')
        st.metric('Dias até rutura',
                  f'{dias_base:.1f}' if dias_base < 999 else 'N/D')
        st.metric('Score', f'{score_base:.1f}')
        st.markdown(f'**Classe:** :red[{classe_base}]' if classe_base in ('A_CRITICO', 'B_ALTO')
                    else f'**Classe:** :green[{classe_base}]')

    with cc2:
        st.markdown('#### Estado simulado')
        st.metric('Stock atual', f'{stock_sim:,.0f}',
                  delta=f'{stock_sim - stock_base:+,.0f}')
        st.metric('Consumo médio diário', f'{consumo_sim:,.2f}',
                  delta=f'{consumo_sim - consumo_base:+,.2f}', delta_color='inverse')
        st.metric('Ordens de compra', f'{oc_sim:,.0f}',
                  delta=f'{oc_sim - oc_base:+,.0f}')
        st.metric('Dias até rutura',
                  f'{dias_sim:.1f}' if dias_sim < 999 else 'N/D',
                  delta=f'{dias_sim - dias_base:+.1f}'
                        if dias_sim < 999 and dias_base < 999 else None)
        st.metric('Score', f'{score_sim:.1f}',
                  delta=f'{score_sim - score_base:+.1f}', delta_color='inverse')
        st.markdown(f'**Classe:** :red[{classe_sim}]' if classe_sim in ('A_CRITICO', 'B_ALTO')
                    else f'**Classe:** :green[{classe_sim}]')

    # Gauge visual
    fig = go.Figure(go.Indicator(
        mode='gauge+number+delta',
        value=score_sim,
        delta={'reference': score_base, 'increasing': {'color': COLOR_DANGER},
               'decreasing': {'color': COLOR_SUCCESS}},
        title={'text': 'Score de Criticidade (simulado vs actual)'},
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
    fig.update_layout(height=320, margin={'l': 20, 'r': 20, 't': 50, 'b': 20})
    st.plotly_chart(fig, use_container_width=True)

st.markdown('---')

with st.expander('Notas metodológicas e fórmulas'):
    st.markdown(f"""
**Fórmulas aplicadas (correspondem ao modelo de dados)**

- **Consumo diário PA**: `μ = Stock_Mínimo / Cob_Obj_PA`
- **Consumo diário Comp**: `μ = (Stock_Reposição − Stock_Mínimo) / Lead_Time` (Wilson invertido); senão `μ = Stock_Mínimo / Lead_Time`
- **Consumo efectivo**: `μ_eff = μ × Safety` ← este é o consumo usado para calcular dias até rutura
- **Saldo**: `Stock_Actual + OC_Pendente`
- **Dias até rutura**: `Saldo / μ_eff`
- **Score**: `100 × (1 − Dias_Rutura / Cob_Obj)`, com cap [0, 100]
- **Score ponderado (Comp)**: `Score × (1 + Centralidade_BOM / 20)`
- **Classe**: A_CRITICO se Score ≥ {lim_critico}, B_ALTO ≥ {lim_alto}, C_MEDIO ≥ {lim_medio}, D_BAIXO > 0, E_SEM_RISCO caso contrário

**O cenário global** mantém Stock_Mínimo, Stock_Reposição e Stock_Atual constantes; varia apenas parâmetros de gestão.

**O cenário por SKU** mantém os parâmetros globais; varia apenas a situação observável (stock, consumo, OC) do artigo seleccionado.

**O safety factor de {safety:.2f}** está activo em ambos os cenários: multiplica o consumo médio para representar margem de segurança operacional. Valor 1.0 = sem margem; valores >1.0 tornam mais artigos críticos (cobertura efectiva é menor).
""")

render_footer()
