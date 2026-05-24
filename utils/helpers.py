"""
Filtros e helpers reutilizáveis em todas as páginas.
"""
import streamlit as st
import pandas as pd


def sidebar_filters_pa(df, key_prefix='pa'):
    """Filtros de sidebar para Produto Acabado. Devolve df filtrado."""
    with st.sidebar:
        st.markdown('### Filtros — Produto Acabado')

        subfamilias = ['(Todas)'] + sorted(df['Subfamilia'].dropna().unique().tolist())
        sel_sub = st.selectbox('Subfamília', subfamilias, key=f'{key_prefix}_sub')

        classes = ['(Todas)'] + sorted(df['Classe_Risco'].dropna().unique().tolist())
        sel_cls = st.multiselect('Classe de risco', classes[1:], default=[],
                                  key=f'{key_prefix}_cls')

        recom = ['(Todas)'] + sorted(df['Recomendacao'].dropna().unique().tolist())
        sel_rec = st.multiselect('Recomendação operacional', recom[1:], default=[],
                                  key=f'{key_prefix}_rec')

        score_min, score_max = st.slider('Score de Criticidade', 0, 100, (0, 100),
                                          key=f'{key_prefix}_score')

    out = df.copy()
    if sel_sub != '(Todas)':
        out = out[out['Subfamilia'] == sel_sub]
    if sel_cls:
        out = out[out['Classe_Risco'].isin(sel_cls)]
    if sel_rec:
        out = out[out['Recomendacao'].isin(sel_rec)]
    out = out[(out['Score_Criticidade'] >= score_min) &
              (out['Score_Criticidade'] <= score_max)]
    return out


def sidebar_filters_comp(df, key_prefix='comp'):
    """Filtros de sidebar para Componentes."""
    with st.sidebar:
        st.markdown('### Filtros — Componentes')

        tipos = ['(Todos)'] + sorted(df['Tipo_Artigo'].dropna().unique().tolist())
        sel_tipo = st.selectbox('Tipo de artigo', tipos, key=f'{key_prefix}_tipo')

        subfamilias = ['(Todas)'] + sorted(df['Subfamilia'].dropna().unique().tolist())
        sel_sub = st.selectbox('Subfamília', subfamilias, key=f'{key_prefix}_sub')

        classes = sorted(df['Classe_Risco'].dropna().unique().tolist())
        sel_cls = st.multiselect('Classe de risco', classes, default=[],
                                  key=f'{key_prefix}_cls')

        cen_min = st.slider('Centralidade BOM mínima', 0,
                            int(df['Centralidade_BOM'].max()) if len(df) else 50, 0,
                            key=f'{key_prefix}_cen')

    out = df.copy()
    if sel_tipo != '(Todos)':
        out = out[out['Tipo_Artigo'] == sel_tipo]
    if sel_sub != '(Todas)':
        out = out[out['Subfamilia'] == sel_sub]
    if sel_cls:
        out = out[out['Classe_Risco'].isin(sel_cls)]
    out = out[out['Centralidade_BOM'] >= cen_min]
    return out


def metric_safe(value, fmt='{:,.0f}', default='—'):
    """Formata valor numérico com fallback."""
    try:
        if pd.isna(value):
            return default
        return fmt.format(value)
    except (ValueError, TypeError):
        return default


def render_download(df, filename, label='Exportar dados (CSV)'):
    """Botão de download para um DataFrame."""
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label=label,
        data=csv,
        file_name=filename,
        mime='text/csv',
    )


def render_footer():
    """Footer comum em todas as páginas."""
    st.markdown(
        '<div class="footer">'
        'PG em Tecnologias e IA Aplicadas aos Negócios | ISCTE Executive Education | '
        'Carlos Mota + Henrique Amaral Dias + Vítor Ribeiro | '
        'Sistema Inteligente de Gestão de Cobertura de Stock e Planeamento de Produção'
        '</div>',
        unsafe_allow_html=True
    )


def header_with_refresh(title, subtitle=None, show_home=True):
    """Cabeçalho padrão: botão Home (esq) + título + botão Actualizar (dir).

    O refresh limpa a cache de dados, força rerun, mostra toast e regista
    timestamp visível na sidebar (modo demo durante apresentação).
    """
    col_home, col_title, col_refresh = st.columns([0.6, 4.4, 1.2])

    with col_home:
        if show_home:
            st.page_link('app.py', label='Home', icon='🏠')

    with col_title:
        st.markdown(f'# {title}')
        if subtitle:
            st.caption(subtitle)

    with col_refresh:
        if st.button('🔄 Actualizar dados', use_container_width=True, type='primary'):
            st.cache_data.clear()
            ts = pd.Timestamp.now().strftime('%H:%M:%S')
            st.session_state['last_refresh'] = ts
            st.toast(f'Dados actualizados às {ts}', icon='✅')
            st.rerun()

    # Banner "última actualização" sempre visível (canto sup. direito)
    last_ts = st.session_state.get('last_refresh')
    if last_ts:
        st.markdown(
            f'<div style="text-align:right; font-size:0.78rem; color:#059669; '
            f'margin-top:-0.5rem; margin-bottom:0.5rem;">'
            f'● Dados actualizados às <strong>{last_ts}</strong></div>',
            unsafe_allow_html=True,
        )
