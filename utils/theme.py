"""
Tema e estilos partilhados.
Paleta inspirada na indústria vitivinícola: bordeaux + dourado + cremes.
"""

# Paleta de cores
COLOR_PRIMARY = '#722F37'     # Bordeaux
COLOR_SECONDARY = '#C9A961'   # Dourado
COLOR_DARK = '#1F2937'        # Navy escuro
COLOR_LIGHT = '#FAF4E1'       # Creme
COLOR_DANGER = '#DC2626'      # Vermelho alerta
COLOR_WARNING = '#D97706'     # Âmbar
COLOR_SUCCESS = '#059669'     # Verde
COLOR_INFO = '#0891B2'        # Teal
COLOR_NEUTRAL = '#6B7280'     # Cinza médio

CLASS_RISCO_COLORS = {
    'A_CRITICO': COLOR_DANGER,
    'B_ALTO': COLOR_WARNING,
    'C_MEDIO': '#F59E0B',
    'D_BAIXO': '#86EFAC',
    'E_SEM_RISCO': COLOR_SUCCESS,
    'Sem_Dados': COLOR_NEUTRAL,
}

# CSS global (injectado em cada página via st.markdown)
CUSTOM_CSS = """
<style>
    /* Compactar header */
    .block-container {padding-top: 2rem; padding-bottom: 1rem;}

    /* Cards de métricas */
    [data-testid="stMetric"] {
        background-color: rgba(114, 47, 55, 0.06);
        border: 1px solid rgba(114, 47, 55, 0.15);
        border-radius: 8px;
        padding: 12px 16px;
    }
    [data-testid="stMetricLabel"] {
        font-weight: 600;
        color: #722F37;
        white-space: normal;
        overflow: visible;
        text-overflow: clip;
    }
    [data-testid="stMetricLabel"] > div {
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: clip !important;
    }
    [data-testid="stMetricLabel"] p {
        white-space: normal !important;
        overflow-wrap: break-word !important;
        word-break: normal !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.6rem;
        font-weight: 700;
    }

    /* Sidebar — bordeaux muito clarinho (liga à identidade CARMIM #722F37) */
    [data-testid="stSidebar"] {
        background-color: #F5E8EA !important;
        border-right: 1px solid #E8D5D8;
    }
    [data-testid="stSidebar"] *,
    [data-testid="stSidebar"] a,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] li,
    [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {
        color: #1F2937 !important;
    }
    /* Links da navegação multi-page */
    [data-testid="stSidebarNav"] a span {
        color: #1F2937 !important;
        font-weight: 500 !important;
    }
    [data-testid="stSidebarNav"] a:hover {
        background-color: rgba(114, 47, 55, 0.15) !important;
    }
    /* Página activa */
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background-color: rgba(114, 47, 55, 0.22) !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] span {
        color: #722F37 !important;
        font-weight: 700 !important;
    }
    /* Inputs dentro da sidebar (selectbox, slider labels) */
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] [data-baseweb="select"] {
        color: #1F2937 !important;
    }

    /* Botões */
    .stButton > button {
        background-color: #722F37;
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 600;
    }
    .stButton > button:hover {
        background-color: #5A252C;
        color: #C9A961;
    }

    /* Tabelas mais compactas */
    .dataframe {
        font-size: 0.85rem;
    }

    /* Titulo H1 com sublinhado */
    h1 {
        color: #722F37;
        border-bottom: 3px solid #C9A961;
        padding-bottom: 0.5rem;
    }

    h2 {
        color: #1F2937;
        margin-top: 1.5rem;
    }

    h3 {
        color: #722F37;
    }

    /* Footer */
    .footer {
        font-size: 0.75rem;
        color: #6B7280;
        text-align: center;
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid #E5E7EB;
    }
</style>
"""


def class_color(classe):
    """Retorna a cor hex correspondente à classe de risco."""
    return CLASS_RISCO_COLORS.get(classe, COLOR_NEUTRAL)


PLOTLY_LAYOUT_DEFAULTS = {
    'font': {'family': 'Arial, sans-serif', 'size': 12, 'color': '#1F2937'},
    'paper_bgcolor': 'rgba(0,0,0,0)',
    'plot_bgcolor': 'rgba(250,244,225,0.3)',
    'colorway': [COLOR_PRIMARY, COLOR_SECONDARY, COLOR_INFO, COLOR_WARNING, COLOR_SUCCESS, COLOR_DARK],
    'margin': {'l': 50, 'r': 30, 't': 50, 'b': 50},
    'hoverlabel': {'bgcolor': 'white', 'font_size': 12, 'font_family': 'Arial'},
}
