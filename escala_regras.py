import pandas as pd
import random
from datetime import datetime
import urllib.parse
import io

# Mapa padrão para caso ocorra falha na leitura da planilha (conforme seu fallback original)
MAPA_REFERENCIA_FALLBACK = {
    "Abigail": "Dani", "Amanda": "Mijal", "Anna Laura": "Soledad", "Ariel": "Rafael", 
    "Bianca M.": "Ariel", "Bruna": "Anna Laura", "Bruno": "Bianca M.", "Dani": "Jesus", 
    "Debora": "Bruna", "Diana": "Julia", "Florencia": "Diana", "Gisele": "Thiago", 
    "Honorato": "Bruno", "Jazmin": "Abigail", "Jesus": "Luca", "Julia": "Honorato", 
    "Livia": "Amanda", "Luca": "Jazmin", "Mijal": "Livia", "Rafael": "Florencia", 
    "Renan": "Debora", "Soledad": "Gisele", "Thiago": "Renan"
}

def encontrar_backup_vivo(nome, nomes_ativos, mapa_referencia):
    """
    Encontra o backup vivo baseado no mapa de referências atualizado.
    """
    proximo = mapa_referencia.get(nome)
    tentativas = 0
    while proximo and proximo not in nomes_ativos and tentativas < len(mapa_referencia):
        proximo = mapa_referencia.get(proximo)
        tentativas += 1
    return proximo if proximo in nomes_ativos else "Sem Backup Ativo"

def gerar_escala_balanceada(nomes, mapa_referencia, t):
    """
    Gera a escala balanceada de reuniões para o ano de 2026.
    """
    random.seed(42)
    fila_base = nomes.copy()
    random.shuffle(fila_base)
    nomes_dor = [n for n in nomes if n not in ["Dani", "Rafael"]]
    random.shuffle(nomes_dor)
    cont_total = {n: 0 for n in nomes}
    cont_dor = {n: 0 for n in nomes_dor}
    dias_range = pd.date_range(datetime(2026, 1, 1), datetime(2026, 12, 31), freq='B')
    escala = []
    
    for dia in dias_range:
        data_s, sem, d_sem = dia.strftime("%d/%m/%Y"), dia.isocalendar()[1], dia.weekday()
        d_nome = t["dias"][d_sem]
        quem_ja_foi = [e['Apresentador'] for e in escala if e['Semana'] == sem]
        
        ap_m = min([n for n in fila_base if n not in quem_ja_foi], key=lambda x: cont_total[x])
        cont_total[ap_m] += 1
        quem_ja_foi.append(ap_m)
        escala.append({
            "Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": t["flash_m"],
            "Apresentador": ap_m, "Backup": encontrar_backup_vivo(ap_m, nomes, mapa_referencia),
            "Backup2": encontrar_backup_vivo(encontrar_backup_vivo(ap_m, nomes, mapa_referencia), nomes, mapa_referencia),
            "BackupOculto": encontrar_backup_vivo(encontrar_backup_vivo(encontrar_backup_vivo(ap_m, nomes, mapa_referencia), nomes, mapa_referencia), nomes, mapa_referencia),
            "Link": f"https://outlook.office.com/calendar/0/deeplink/compose?subject={urllib.parse.quote(t['flash_m'])}&startdt={dia.strftime('%Y-%m-%d')}T09:45:00"
        })

        tipo_t = "DOR" if d_sem in [1, 3] else "Flash Tarde"
        cand_t = [n for n in (nomes_dor if tipo_t == "DOR" else fila_base) if n not in quem_ja_foi]
        ap_t = min(cand_t, key=lambda x: cont_dor[x] if tipo_t == "DOR" else cont_total[x])
        if tipo_t == "DOR": cont_dor[ap_t] += 1
        cont_total[ap_t] += 1
        escala.append({
            "Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": tipo_t,
            "Apresentador": ap_t, "Backup": encontrar_backup_vivo(ap_t, nomes, mapa_referencia),
            "Backup2": encontrar_backup_vivo(encontrar_backup_vivo(ap_t, nomes, mapa_referencia), nomes, mapa_referencia),
            "BackupOculto": encontrar_backup_vivo(encontrar_backup_vivo(encontrar_backup_vivo(ap_t, nomes, mapa_referencia), nomes, mapa_referencia), nomes, mapa_referencia),
            "Link": f"https://outlook.office.com/calendar/0/deeplink/compose?subject={urllib.parse.quote(tipo_t)}&startdt={dia.strftime('%Y-%m-%d')}T15:00:00"
        })
    return pd.DataFrame(escala)

def exportar_excel_limpo(df_total, t, mes_nome=None):
    """
    Gera o buffer excel estruturado, com formatação e estilização de abas.
    """
    output = io.BytesIO()
    df_c = df_total.copy()
    df_c['dt_obj'] = pd.to_datetime(df_c['Data'], format='%d/%m/%Y')
    df_c = df_c.sort_values('dt_obj')
    meses_map = {i+1: nome for i, nome in enumerate(t["meses"])}
    df_c['Mês'] = df_c['dt_obj'].dt.month.map(meses_map)
    
    m = df_c[df_c['Reunião'] == t['flash_m']][['Mês', 'Data', 'Dia', 'Apresentador', 'Backup']].rename(columns={'Apresentador':t['resp_m'], 'Backup':t['backup'] + ' M'})
    t_df = df_c[df_c['Reunião'].isin(['Flash Tarde', 'DOR'])][['Data', 'Apresentador', 'Backup', 'Reunião']].rename(columns={'Apresentador':t['resp_t'], 'Backup':t['backup'] + ' T', 'Reunião':t['tipo_t']})
    
    df_f = pd.merge(m, t_df, on='Data', how='outer').fillna("")
    df_f['dt_sort'] = pd.to_datetime(df_f['Data'], format='%d/%m/%Y')
    df_f = df_f.sort_values('dt_sort')
    if mes_nome: df_f = df_f[df_f['Mês'] == mes_nome]

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook, worksheet = writer.book, writer.book.add_worksheet('Escala')
        h_fmt = workbook.add_format({'bold': True, 'bg_color': '#ff4b4b', 'font_color': 'white', 'border': 1, 'align': 'center'})
        m_fmt = workbook.add_format({'bold': True, 'bg_color': '#A6A6A6', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        c_fmt = workbook.add_format({'border': 1, 'align': 'center'})
        cols = ['Data', 'Dia', t['resp_m'], t['backup'] + ' M', t['tipo_t'], t['resp_t'], t['backup'] + ' T']
        for i, col in enumerate(cols): 
            worksheet.write(0, i, col, h_fmt)
            worksheet.set_column(i, i, 18)
            
        row_idx, mes_atual = 1, ""
        for _, row in df_f.iterrows():
            if row['Mês'] != mes_atual:
                mes_atual = row['Mês']
                worksheet.merge_range(row_idx, 0, row_idx, 6, mes_atual.upper(), m_fmt)
                row_idx += 1
            for j, c in enumerate(cols): worksheet.write(row_idx, j, row[c] if c in row else "", c_fmt)
            row_idx += 1
    return output.getvalue()
