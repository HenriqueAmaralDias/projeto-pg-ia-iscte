"""
Carga centralizada de dados com cache do Streamlit.
Carrega o modelo consolidado e as previsões de IA.
"""
import streamlit as st
import pandas as pd
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'
PATH_MODELO = DATA_DIR / 'Modelo_Dados_Consolidado_v1.xlsx'
PATH_PREVISOES = DATA_DIR / 'IA_Previsoes_v1.xlsx'


@st.cache_data(ttl=300, show_spinner=False)
def load_dim_artigos():
    df = pd.read_excel(PATH_MODELO, sheet_name='02_Dim_Artigos', skiprows=2)
    return df


@st.cache_data(ttl=300, show_spinner=False)
def load_bom():
    df = pd.read_excel(PATH_MODELO, sheet_name='03_Fact_BOM', skiprows=2)
    return df


@st.cache_data(ttl=300, show_spinner=False)
def load_bom_alt():
    df = pd.read_excel(PATH_MODELO, sheet_name='04_Fact_BOM_Alt', skiprows=2)
    return df


@st.cache_data(ttl=300, show_spinner=False)
def load_ecf():
    df = pd.read_excel(PATH_MODELO, sheet_name='05_Fact_ECF', skiprows=2)
    if 'Data_1a_Entrega' in df.columns:
        df['Data_1a_Entrega'] = pd.to_datetime(df['Data_1a_Entrega'], errors='coerce')
    return df


@st.cache_data(ttl=300, show_spinner=False)
def load_kpi_pa():
    df = pd.read_excel(PATH_MODELO, sheet_name='06_KPI_PA', skiprows=2)
    return df


@st.cache_data(ttl=300, show_spinner=False)
def load_kpi_comp():
    df = pd.read_excel(PATH_MODELO, sheet_name='07_KPI_Comp', skiprows=2)
    return df


@st.cache_data(ttl=300, show_spinner=False)
def load_mrp_net():
    df = pd.read_excel(PATH_MODELO, sheet_name='08_MRP_Net', skiprows=2)
    return df


@st.cache_data(ttl=300, show_spinner=False)
def load_mrp_agg():
    df = pd.read_excel(PATH_MODELO, sheet_name='09_MRP_Agg', skiprows=2)
    return df


@st.cache_data(ttl=300, show_spinner=False)
def load_alertas():
    df = pd.read_excel(PATH_MODELO, sheet_name='10_Alertas', skiprows=2)
    return df


@st.cache_data(ttl=300, show_spinner=False)
def load_ia_rec_compras():
    df = pd.read_excel(PATH_PREVISOES, sheet_name='02_Rec_Compras')
    return df


@st.cache_data(ttl=300, show_spinner=False)
def load_ia_anomalias():
    df = pd.read_excel(PATH_PREVISOES, sheet_name='03_Anomalias')
    return df


@st.cache_data(ttl=300, show_spinner=False)
def load_ia_modelos():
    df = pd.read_excel(PATH_PREVISOES, sheet_name='01_Resumo_Modelos')
    return df


@st.cache_data(ttl=300, show_spinner=False)
def load_prob_rutura():
    df = pd.read_excel(PATH_PREVISOES, sheet_name='04_Prob_Rutura')
    return df


def clear_cache():
    """Limpa todas as caches de dados (força recarga)."""
    st.cache_data.clear()


def get_file_info():
    """Retorna metadados dos ficheiros de dados (data modificação, tamanho)."""
    info = {}
    for path in [PATH_MODELO, PATH_PREVISOES]:
        if path.exists():
            stat = path.stat()
            info[path.name] = {
                'tamanho_kb': stat.st_size / 1024,
                'modificado': pd.Timestamp(stat.st_mtime, unit='s'),
            }
    return info
