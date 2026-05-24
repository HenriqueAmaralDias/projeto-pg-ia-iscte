"""
Geração de alertas críticos por email (RFC 5322).
Modo demo: produz EmailMessage que pode ser exportado como .eml.
Modo live: requer SMTP configurado em .streamlit/secrets.toml.
"""
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from datetime import datetime
import pandas as pd
import html as _html

BORDEAUX = '#722F37'
GOLD = '#C9A961'
CREAM = '#FAF4E1'
DANGER = '#DC2626'
WARNING = '#D97706'
SUCCESS = '#059669'
DARK = '#1F2937'
GRAY = '#6B7280'

CRITICAL_CLASSES = ['A_CRITICO', 'B_ALTO']


def _esc(v):
    if pd.isna(v):
        return '—'
    return _html.escape(str(v))


def _row_pa(r):
    cls = r.get('Classe_Risco', '')
    cls_color = DANGER if cls == 'A_CRITICO' else WARNING
    return (
        f'<tr>'
        f'<td style="padding:6px 8px; border-bottom:1px solid #E5E7EB; font-family:Consolas,monospace; font-size:11px;">{_esc(r["Cod_Artigo"])}</td>'
        f'<td style="padding:6px 8px; border-bottom:1px solid #E5E7EB; font-size:12px;">{_esc(r["Descricao"])[:40]}</td>'
        f'<td style="padding:6px 8px; border-bottom:1px solid #E5E7EB; font-size:12px; text-align:right;">{r["Stock_Atual"]:,.0f}</td>'
        f'<td style="padding:6px 8px; border-bottom:1px solid #E5E7EB; font-size:12px; text-align:right;">{r["Dias_Ate_Rutura_Com_OC"]:.1f}</td>'
        f'<td style="padding:6px 8px; border-bottom:1px solid #E5E7EB; font-size:12px; text-align:right;"><strong style="color:{cls_color};">{r["Score_Criticidade"]:.0f}</strong></td>'
        f'<td style="padding:6px 8px; border-bottom:1px solid #E5E7EB; font-size:11px;"><span style="background-color:{cls_color}; color:white; padding:2px 6px; border-radius:3px;">{_esc(cls)}</span></td>'
        f'</tr>'
    )


def _row_comp(r):
    cls = r.get('Classe_Risco', '')
    cls_color = DANGER if cls == 'A_CRITICO' else WARNING
    return (
        f'<tr>'
        f'<td style="padding:6px 8px; border-bottom:1px solid #E5E7EB; font-family:Consolas,monospace; font-size:11px;">{_esc(r["Cod_Artigo"])}</td>'
        f'<td style="padding:6px 8px; border-bottom:1px solid #E5E7EB; font-size:12px;">{_esc(r["Descricao"])[:40]}</td>'
        f'<td style="padding:6px 8px; border-bottom:1px solid #E5E7EB; font-size:12px; text-align:right;">{r.get("Centralidade_BOM", 0):.0f}</td>'
        f'<td style="padding:6px 8px; border-bottom:1px solid #E5E7EB; font-size:12px; text-align:right;">{r["Stock_Atual"]:,.0f}</td>'
        f'<td style="padding:6px 8px; border-bottom:1px solid #E5E7EB; font-size:12px; text-align:right;"><strong style="color:{cls_color};">{r.get("Score_Criticidade_Ponderado", 0):.0f}</strong></td>'
        f'<td style="padding:6px 8px; border-bottom:1px solid #E5E7EB; font-size:11px;"><span style="background-color:{cls_color}; color:white; padding:2px 6px; border-radius:3px;">{_esc(cls)}</span></td>'
        f'</tr>'
    )


def _row_compra(r):
    prob = r.get('Prob_Rutura_ML', 0)
    color = DANGER if prob >= 0.7 else WARNING
    qtd = r.get('Quantidade_a_Encomendar', 0)
    return (
        f'<tr>'
        f'<td style="padding:6px 8px; border-bottom:1px solid #E5E7EB; font-family:Consolas,monospace; font-size:11px;">{_esc(r["Cod_Artigo"])}</td>'
        f'<td style="padding:6px 8px; border-bottom:1px solid #E5E7EB; font-size:12px;">{_esc(r["Descricao"])[:35]}</td>'
        f'<td style="padding:6px 8px; border-bottom:1px solid #E5E7EB; font-size:12px; text-align:right; color:{color};"><strong>{prob*100:.1f}%</strong></td>'
        f'<td style="padding:6px 8px; border-bottom:1px solid #E5E7EB; font-size:12px; text-align:right;">{r.get("Dias_ate_Rutura", 0):.1f}d</td>'
        f'<td style="padding:6px 8px; border-bottom:1px solid #E5E7EB; font-size:12px; text-align:right;"><strong>{qtd:,.0f}</strong></td>'
        f'</tr>'
    )


def _kpi_card(label, value, color):
    return (
        f'<td width="25%" align="center" style="padding:8px;">'
        f'<div style="background-color:{color}1A; border:1px solid {color}; border-radius:6px; padding:10px;">'
        f'<div style="font-size:22px; font-weight:bold; color:{color};">{value}</div>'
        f'<div style="font-size:10px; color:{DARK}; text-transform:uppercase; letter-spacing:0.5px;">{label}</div>'
        f'</div>'
        f'</td>'
    )


def build_html(summary, pa_crit, comp_crit, top_compras, dashboard_url):
    rows_pa = ''.join(_row_pa(r) for _, r in pa_crit.iterrows()) or \
        f'<tr><td colspan="6" style="padding:12px; text-align:center; color:{GRAY};">Sem PA em risco crítico</td></tr>'
    rows_comp = ''.join(_row_comp(r) for _, r in comp_crit.iterrows()) or \
        f'<tr><td colspan="6" style="padding:12px; text-align:center; color:{GRAY};">Sem componentes em risco crítico</td></tr>'
    rows_compras = ''.join(_row_compra(r) for _, r in top_compras.iterrows()) or \
        f'<tr><td colspan="5" style="padding:12px; text-align:center; color:{GRAY};">Sem recomendações ML</td></tr>'

    cob_pa = f"{summary['cobertura_pa_med']:.1f} d" if summary['cobertura_pa_med'] is not None else '—'

    return f"""<!DOCTYPE html>
<html lang="pt-PT">
<head>
<meta charset="utf-8">
<title>Alerta de Cobertura de Stock</title>
</head>
<body style="margin:0; padding:0; font-family: Arial, Helvetica, sans-serif; background-color:{CREAM};">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:{CREAM};">
<tr><td align="center" style="padding:24px 12px;">
<table width="640" cellpadding="0" cellspacing="0" border="0" style="background-color:#ffffff; border-radius:8px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.08);">

<tr><td style="background-color:{BORDEAUX}; padding:24px;">
<h1 style="color:{GOLD}; margin:0; font-size:22px; font-weight:600;">Alerta de Cobertura de Stock</h1>
<p style="color:{CREAM}; margin:6px 0 0; font-size:13px;">Sistema BI/IA — Indústria Vitivinícola | {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</td></tr>

<tr><td style="padding:20px 24px 8px;">
<h2 style="color:{BORDEAUX}; margin:0 0 12px; font-size:16px; border-bottom:2px solid {GOLD}; padding-bottom:6px;">Resumo executivo</h2>
<table width="100%" cellpadding="0" cellspacing="0" border="0">
<tr>
{_kpi_card('PA em risco', summary['pa_critical_total'], DANGER)}
{_kpi_card('Componentes em risco', summary['comp_critical_total'], WARNING)}
{_kpi_card('A encomendar (ML)', summary['encomendar_total'], BORDEAUX)}
{_kpi_card('Cobertura mediana PA', cob_pa, SUCCESS)}
</tr>
</table>
</td></tr>

<tr><td style="padding:8px 24px;">
<p style="font-size:13px; color:{DARK}; line-height:1.5; margin:0;">
{summary['pa_critical_total'] + summary['comp_critical_total']} artigos requerem atenção imediata.
Stocks abaixo dos limiares operacionais; intervenção recomendada para evitar ruturas em produção.
</p>
</td></tr>

<tr><td style="padding:20px 24px 8px;">
<h2 style="color:{BORDEAUX}; margin:0 0 8px; font-size:15px;">Produto Acabado — Top {len(pa_crit)} em risco crítico</h2>
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="border:1px solid #E5E7EB; border-radius:4px; border-collapse:collapse;">
<thead>
<tr style="background-color:{CREAM};">
<th style="padding:8px; text-align:left; font-size:11px; color:{BORDEAUX}; border-bottom:2px solid {GOLD};">Código</th>
<th style="padding:8px; text-align:left; font-size:11px; color:{BORDEAUX}; border-bottom:2px solid {GOLD};">Descrição</th>
<th style="padding:8px; text-align:right; font-size:11px; color:{BORDEAUX}; border-bottom:2px solid {GOLD};">Stock</th>
<th style="padding:8px; text-align:right; font-size:11px; color:{BORDEAUX}; border-bottom:2px solid {GOLD};">Dias rutura</th>
<th style="padding:8px; text-align:right; font-size:11px; color:{BORDEAUX}; border-bottom:2px solid {GOLD};">Score</th>
<th style="padding:8px; text-align:left; font-size:11px; color:{BORDEAUX}; border-bottom:2px solid {GOLD};">Classe</th>
</tr>
</thead>
<tbody>{rows_pa}</tbody>
</table>
</td></tr>

<tr><td style="padding:20px 24px 8px;">
<h2 style="color:{BORDEAUX}; margin:0 0 8px; font-size:15px;">Componentes — Top {len(comp_crit)} em risco crítico</h2>
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="border:1px solid #E5E7EB; border-radius:4px; border-collapse:collapse;">
<thead>
<tr style="background-color:{CREAM};">
<th style="padding:8px; text-align:left; font-size:11px; color:{BORDEAUX}; border-bottom:2px solid {GOLD};">Código</th>
<th style="padding:8px; text-align:left; font-size:11px; color:{BORDEAUX}; border-bottom:2px solid {GOLD};">Descrição</th>
<th style="padding:8px; text-align:right; font-size:11px; color:{BORDEAUX}; border-bottom:2px solid {GOLD};">Centralidade BOM</th>
<th style="padding:8px; text-align:right; font-size:11px; color:{BORDEAUX}; border-bottom:2px solid {GOLD};">Stock</th>
<th style="padding:8px; text-align:right; font-size:11px; color:{BORDEAUX}; border-bottom:2px solid {GOLD};">Score pond</th>
<th style="padding:8px; text-align:left; font-size:11px; color:{BORDEAUX}; border-bottom:2px solid {GOLD};">Classe</th>
</tr>
</thead>
<tbody>{rows_comp}</tbody>
</table>
</td></tr>

<tr><td style="padding:20px 24px 8px;">
<h2 style="color:{BORDEAUX}; margin:0 0 8px; font-size:15px;">Top {len(top_compras)} recomendações ML de compra urgente</h2>
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="border:1px solid #E5E7EB; border-radius:4px; border-collapse:collapse;">
<thead>
<tr style="background-color:{CREAM};">
<th style="padding:8px; text-align:left; font-size:11px; color:{BORDEAUX}; border-bottom:2px solid {GOLD};">Código</th>
<th style="padding:8px; text-align:left; font-size:11px; color:{BORDEAUX}; border-bottom:2px solid {GOLD};">Descrição</th>
<th style="padding:8px; text-align:right; font-size:11px; color:{BORDEAUX}; border-bottom:2px solid {GOLD};">Prob rutura</th>
<th style="padding:8px; text-align:right; font-size:11px; color:{BORDEAUX}; border-bottom:2px solid {GOLD};">Horizonte</th>
<th style="padding:8px; text-align:right; font-size:11px; color:{BORDEAUX}; border-bottom:2px solid {GOLD};">Qtd recomendada</th>
</tr>
</thead>
<tbody>{rows_compras}</tbody>
</table>
</td></tr>

<tr><td style="padding:16px 24px;">
<table width="100%" cellpadding="0" cellspacing="0" border="0">
<tr><td align="center">
<a href="{dashboard_url}" style="display:inline-block; background-color:{BORDEAUX}; color:#ffffff; padding:10px 24px; text-decoration:none; border-radius:6px; font-size:13px; font-weight:600;">Abrir dashboard completo</a>
</td></tr>
</table>
</td></tr>

<tr><td style="background-color:{CREAM}; padding:14px 24px; text-align:center; font-size:11px; color:{GRAY}; border-top:1px solid #E5E7EB;">
Sistema Inteligente de Gestão de Cobertura de Stock<br>
PG em Tecnologias e IA Aplicadas aos Negócios | ISCTE Executive Education<br>
Carlos Mota + Henrique Amaral Dias + Vítor Ribeiro<br>
Email gerado automaticamente. Não responder.
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""


def build_text(summary, pa_crit, comp_crit, top_compras, dashboard_url):
    lines = [
        f'ALERTA DE COBERTURA DE STOCK',
        f'Sistema BI/IA — Indústria Vitivinícola',
        f'{datetime.now().strftime("%Y-%m-%d %H:%M")}',
        '=' * 60,
        '',
        f'RESUMO EXECUTIVO',
        f'  PA em risco alto/crítico:        {summary["pa_critical_total"]}',
        f'  Componentes em risco:            {summary["comp_critical_total"]}',
        f'  A encomendar (recomendação ML):  {summary["encomendar_total"]}',
        f'  Cobertura mediana PA (dias):     {summary["cobertura_pa_med"]:.1f}' if summary['cobertura_pa_med'] is not None else '  Cobertura mediana PA: —',
        '',
        f'TOP {len(pa_crit)} PRODUTO ACABADO EM RISCO CRÍTICO',
        '-' * 60,
    ]
    for _, r in pa_crit.iterrows():
        lines.append(
            f'  {r["Cod_Artigo"]:<10} {str(r["Descricao"])[:30]:<32} '
            f'stk={r["Stock_Atual"]:>7,.0f}  rut={r["Dias_Ate_Rutura_Com_OC"]:>5.1f}d  '
            f'score={r["Score_Criticidade"]:>3.0f} [{r["Classe_Risco"]}]'
        )
    lines += ['', f'TOP {len(comp_crit)} COMPONENTES EM RISCO CRÍTICO', '-' * 60]
    for _, r in comp_crit.iterrows():
        lines.append(
            f'  {r["Cod_Artigo"]:<10} {str(r["Descricao"])[:30]:<32} '
            f'BOM={r.get("Centralidade_BOM", 0):>3.0f}  stk={r["Stock_Atual"]:>7,.0f}  '
            f'score={r.get("Score_Criticidade_Ponderado", 0):>3.0f} [{r["Classe_Risco"]}]'
        )
    lines += ['', f'TOP {len(top_compras)} RECOMENDAÇÕES ML DE COMPRA URGENTE', '-' * 60]
    for _, r in top_compras.iterrows():
        lines.append(
            f'  {r["Cod_Artigo"]:<10} {str(r["Descricao"])[:30]:<32} '
            f'P={r.get("Prob_Rutura_ML", 0)*100:>5.1f}%  '
            f'rut={r.get("Dias_ate_Rutura", 0):>5.1f}d  '
            f'qtd={r.get("Quantidade_a_Encomendar", 0):>7,.0f}'
        )
    lines += [
        '',
        '=' * 60,
        f'Dashboard: {dashboard_url}',
        '',
        'PG em Tecnologias e IA Aplicadas aos Negócios | ISCTE Executive Education',
        'Carlos Mota + Henrique Amaral Dias + Vítor Ribeiro',
        'Email gerado automaticamente. Não responder.',
    ]
    return '\n'.join(lines)


def build_critical_alert_email(
    kpi_pa, kpi_comp, ia_rec,
    recipient,
    sender='alertas@stock-bi.local',
    n_top=10,
    dashboard_url='https://projeto-stock-iscte.streamlit.app/',
):
    """
    Constrói EmailMessage com alertas críticos.

    Args:
        kpi_pa, kpi_comp: DataFrames das sheets KPI
        ia_rec: DataFrame com recomendações ML (de IA_Previsoes_v1.xlsx)
        recipient: email destinatário
        sender: email remetente (default: local domain, não envia se não houver SMTP)
        n_top: número de linhas no topo de cada secção
        dashboard_url: URL do dashboard live

    Returns:
        (EmailMessage, summary_dict)
    """
    pa_crit = kpi_pa[kpi_pa['Classe_Risco'].isin(CRITICAL_CLASSES)].nlargest(n_top, 'Score_Criticidade')
    comp_crit = kpi_comp[kpi_comp['Classe_Risco'].isin(CRITICAL_CLASSES)].nlargest(
        n_top, 'Score_Criticidade_Ponderado' if 'Score_Criticidade_Ponderado' in kpi_comp.columns else 'Score_Criticidade'
    )
    top_compras = ia_rec[ia_rec['Accao'] == 'ENCOMENDAR'].nlargest(5, 'Score_Prioridade')

    cob_series = kpi_pa.loc[kpi_pa['Dias_Ate_Rutura_Com_OC'] < 999, 'Dias_Ate_Rutura_Com_OC']
    summary = {
        'pa_critical_total': int(kpi_pa['Classe_Risco'].isin(CRITICAL_CLASSES).sum()),
        'comp_critical_total': int(kpi_comp['Classe_Risco'].isin(CRITICAL_CLASSES).sum()),
        'encomendar_total': int((ia_rec['Accao'] == 'ENCOMENDAR').sum()),
        'cobertura_pa_med': float(cob_series.median()) if len(cob_series) else None,
        'top_pa_count': len(pa_crit),
        'top_comp_count': len(comp_crit),
        'top_compras_count': len(top_compras),
    }

    html = build_html(summary, pa_crit, comp_crit, top_compras, dashboard_url)
    text = build_text(summary, pa_crit, comp_crit, top_compras, dashboard_url)

    msg = EmailMessage()
    subj = f'[Stock] {summary["pa_critical_total"] + summary["comp_critical_total"]} artigos em risco crítico'
    msg['Subject'] = subj
    msg['From'] = sender
    msg['To'] = recipient
    msg['Date'] = formatdate(localtime=True)
    msg['Message-ID'] = make_msgid(domain='stock-bi.local')
    msg.set_content(text, charset='utf-8')
    msg.add_alternative(html, subtype='html', charset='utf-8')

    return msg, summary


def append_to_log(log_path, recipient, n_pa, n_comp, mode, status='generated'):
    """Append uma linha ao audit log (CSV)."""
    log_path = str(log_path)
    import os
    new_file = not os.path.exists(log_path)
    with open(log_path, 'a', encoding='utf-8', newline='') as f:
        if new_file:
            f.write('timestamp,recipient,n_pa_critical,n_comp_critical,mode,status\n')
        f.write(f'{datetime.now().isoformat()},{recipient},{n_pa},{n_comp},{mode},{status}\n')
