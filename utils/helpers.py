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
        'Projeto Final | PG em IA | ISCTE | Henrique Amaral Dias | '
        'Sistema Inteligente de Gestão de Cobertura de Stock e Planeamento de Produção'
        '</div>',
        unsafe_allow_html=True
    )


def header_with_refresh(title, subtitle=None):
    """Cabeçalho padrão com botão de refresh."""
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(f'# {title}')
        if subtitle:
            st.caption(subtitle)
    with col2:
        if st.button('Actualizar dados', use_container_width=True):
            st.cache_data.clear()
            st.rerun()
