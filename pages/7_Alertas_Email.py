"""
Dashboard 7 — Alertas Críticos por Email (Extensão opcional)
Gera ficheiros .eml com alertas críticos prontos para envio executivo.
Modo demo apenas: sem envio SMTP real, gera ficheiro para o utilizador.
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
from pathlib import Path
from utils.data_loader import load_kpi_pa, load_kpi_comp, load_ia_rec_compras
from utils.theme import (
    CUSTOM_CSS, COLOR_PRIMARY, COLOR_DANGER, COLOR_WARNING, COLOR_SUCCESS, COLOR_SECONDARY
)
from utils.helpers import render_footer, header_with_refresh
from utils.email_sender import build_critical_alert_email, append_to_log, CRITICAL_CLASSES

st.set_page_config(page_title='Alertas por Email', page_icon='📧', layout='wide')
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

header_with_refresh(
    'Alertas Críticos por Email',
    'Geração de notificações executivas — extensão "Alertas automáticos email/Teams"'
)

st.info(
    'Modo demo: gera ficheiro `.eml` (formato standard RFC 5322) com os alertas críticos, '
    'pronto a abrir no Outlook ou cliente de mail. **Não envia emails reais.** '
    'Esta extensão fecha o ponto "Alertas automáticos por email/Teams" da secção 13 do caderno de encargos.'
)

# ============================================================
# Sidebar — configuração
# ============================================================
with st.sidebar:
    st.markdown('### Configuração do alerta')

    recipient = st.text_input(
        'Destinatário (email)',
        value='',
        placeholder='nome@empresa.pt',
        help='Endereço de email do destinatário do alerta',
    )

    sender = st.text_input(
        'Remetente',
        value='alertas@stock-bi.local',
        help='Endereço de origem (usado no header From). Em modo demo é apenas decorativo.',
    )

    n_top = st.slider(
        'Top N por categoria',
        min_value=5, max_value=25, value=10, step=1,
        help='Número de linhas a incluir em cada tabela (PA, componentes, recomendações)',
    )

    dashboard_url = st.text_input(
        'URL do dashboard',
        value='https://projeto-stock-iscte.streamlit.app/',
        help='Link clicável no email para o destinatário aceder ao dashboard live',
    )

    st.markdown('---')
    st.markdown('### Critério de criticidade')
    st.caption(f'Classes incluídas: `{"`, `".join(CRITICAL_CLASSES)}`')

# ============================================================
# Carga de dados
# ============================================================
kpi_pa = load_kpi_pa()
kpi_comp = load_kpi_comp()
ia_rec = load_ia_rec_compras()

# ============================================================
# Resumo do que será incluído
# ============================================================
st.markdown('### Resumo do conteúdo')

c1, c2, c3, c4 = st.columns(4)

n_pa_crit = int(kpi_pa['Classe_Risco'].isin(CRITICAL_CLASSES).sum())
n_comp_crit = int(kpi_comp['Classe_Risco'].isin(CRITICAL_CLASSES).sum())
n_encomendar = int((ia_rec['Accao'] == 'ENCOMENDAR').sum())
cob_pa_series = kpi_pa.loc[kpi_pa['Dias_Ate_Rutura_Com_OC'] < 999, 'Dias_Ate_Rutura_Com_OC']
cob_med = cob_pa_series.median() if len(cob_pa_series) else None

c1.metric('PA em risco', n_pa_crit, delta_color='inverse')
c2.metric('Componentes em risco', n_comp_crit, delta_color='inverse')
c3.metric('Recomendações ML', n_encomendar)
c4.metric('Cobertura mediana PA',
          f'{cob_med:.1f} d' if cob_med is not None else '—')

st.caption(
    f'O email vai incluir o top {n_top} de PA, top {n_top} de componentes, '
    f'e top 5 recomendações ML de compra urgente.'
)

st.markdown('---')

# ============================================================
# Geração + preview
# ============================================================
if not recipient:
    st.warning('Define o destinatário na sidebar para gerar o preview do email.')
    st.stop()

if '@' not in recipient or '.' not in recipient.split('@')[-1]:
    st.error('Email do destinatário parece inválido. Verifica antes de avançar.')
    st.stop()

msg, summary = build_critical_alert_email(
    kpi_pa=kpi_pa,
    kpi_comp=kpi_comp,
    ia_rec=ia_rec,
    recipient=recipient,
    sender=sender,
    n_top=n_top,
    dashboard_url=dashboard_url,
)

# Cabeçalho do email
st.markdown('### Cabeçalho')
cc1, cc2 = st.columns(2)
with cc1:
    st.text(f'De:       {msg["From"]}')
    st.text(f'Para:     {msg["To"]}')
with cc2:
    st.text(f'Assunto:  {msg["Subject"]}')
    st.text(f'Data:     {msg["Date"]}')

# Preview HTML
st.markdown('### Preview HTML')

html_body = None
for part in msg.walk():
    if part.get_content_type() == 'text/html':
        html_body = part.get_content()
        break

if html_body:
    components.html(html_body, height=900, scrolling=True)
else:
    st.error('Falha a extrair HTML do email.')

# Versão plain text (collapsed)
with st.expander('Versão plain text (fallback para clientes sem HTML)'):
    text_body = None
    for part in msg.walk():
        if part.get_content_type() == 'text/plain':
            text_body = part.get_content()
            break
    if text_body:
        st.code(text_body, language=None)

st.markdown('---')

# ============================================================
# Acções: download + log
# ============================================================
st.markdown('### Acções')

cc1, cc2, cc3 = st.columns([1, 1, 2])

eml_bytes = bytes(msg)
filename = f'alerta_stock_{datetime.now().strftime("%Y%m%d_%H%M%S")}.eml'

with cc1:
    if st.download_button(
        label='Descarregar .eml',
        data=eml_bytes,
        file_name=filename,
        mime='message/rfc822',
        type='primary',
        use_container_width=True,
    ):
        log_path = Path(__file__).parent.parent / 'data' / 'email_log.csv'
        append_to_log(log_path, recipient, n_pa_crit, n_comp_crit, mode='demo', status='downloaded')

with cc2:
    st.button('Enviar via SMTP', disabled=True, use_container_width=True,
              help='Desactivado em modo demo. Para activar, configurar SMTP em .streamlit/secrets.toml')

with cc3:
    st.caption(
        f'Tamanho: {len(eml_bytes)/1024:.1f} KB | '
        f'Conteúdo: {summary["top_pa_count"]} PA + {summary["top_comp_count"]} comp + '
        f'{summary["top_compras_count"]} recomendações ML'
    )

# ============================================================
# Audit log
# ============================================================
st.markdown('---')
st.markdown('### Histórico de gerações')

log_path = Path(__file__).parent.parent / 'data' / 'email_log.csv'
if log_path.exists():
    log_df = pd.read_csv(log_path)
    log_df = log_df.sort_values('timestamp', ascending=False)
    st.dataframe(log_df, use_container_width=True, hide_index=True, height=240)
    st.caption(f'Total de gerações registadas: {len(log_df)}')
else:
    st.info('Ainda não há registos. Cada download é registado neste log para auditoria.')

# ============================================================
# Notas operacionais
# ============================================================
with st.expander('Como activar envio SMTP real (produção)'):
    st.markdown(
        """
**Passos para activar envio real (fora do âmbito desta defesa)**:

1. Criar `.streamlit/secrets.toml` na raiz da app com:
```toml
[smtp]
host = "smtp.gmail.com"
port = 587
user = "alerts@empresa.pt"
password = "..."  # use App Password se for Gmail
use_tls = true
```
2. Adicionar `.streamlit/secrets.toml` ao `.gitignore` (CRÍTICO — nunca comitar).
3. Implementar `send_via_smtp(msg)` em `utils/email_sender.py` usando `smtplib.SMTP(...)`.
4. Remover `disabled=True` do botão "Enviar via SMTP" neste ficheiro.
5. Testar primeiro com um destinatário de teste antes de produção.

**Alternativas a SMTP** (mais seguras para produção):
- Microsoft Graph API (Teams + email corporativo, OAuth) — para empresas em ambiente 365.
- SendGrid / Mailgun / AWS SES — APIs HTTP com tracking, melhor entrega.
- Webhook Teams (Incoming Webhook) — mais rápido para notificação interna.
"""
    )

render_footer()
