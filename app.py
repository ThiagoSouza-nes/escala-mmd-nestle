import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import streamlit.components.v1 as components
import io
import random

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MMD | Portal de Escalas", layout="wide")

SHEET_ID = "1rFbrhxG72T2qhT2lMclAyLtjlHgtqvbxHFrVZ_KlmAU"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

USER_ACCESS = "MMD-Board"
PASS_ACCESS = "@MMD123#"

MESES_NOMES = {
    "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4, 
    "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8, 
    "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
}

# MAPA ATUALIZADO (Sem Bianca S. - Livia herda Amanda)
MAPA_REFERENCIA = {
    "Abigail": "Dani", "Amanda": "Mijal", "Anna Laura": "Soledad", 
    "Ariel": "Rafael", "Bianca M.": "Ariel", "Bruna": "Anna Laura", 
    "Bruno": "Bianca M.", "Dani": "Jesus", "Debora": "Bruna", 
    "Diana": "Julia", "Florencia": "Diana", "Gisele": "Thiago", 
    "Honorato": "Bruno", "Jazmin": "Abigail", "Jesus": "Luca", 
    "Julia": "Honorato", "Livia": "Amanda", "Luca": "Jazmin", 
    "Mijal": "Livia", "Rafael": "Florencia", "Renan": "Debora", 
    "Soledad": "Gisele", "Thiago": "Renan"
}

def encontrar_backup_vivo(nome_apresentador, nomes_ativos):
    proximo = MAPA_REFERENCIA.get(nome_apresentador)
    tentativas = 0
    while proximo and proximo not in nomes_ativos and tentativas < len(MAPA_REFERENCIA):
        proximo = MAPA_REFERENCIA.get(proximo)
        tentativas += 1
    return proximo if proximo in nomes_ativos else "Sem Backup Ativo"

# --- LOGIN (Simplificado para o código) ---
def check_login():
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.markdown("<h2 style='text-align: center;'>Portal de Escalas MMD</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            with st.form("login"):
                u, p = st.text_input("Usuário"), st.text_input("Senha", type="password")
                if st.form_submit_button("Acessar"):
                    if u == USER_ACCESS and p == PASS_ACCESS:
                        st.session_state.logged_in = True; st.rerun()
        return False
    return True

# --- EXPORTAÇÃO EXCEL ---
def exportar_excel_mmd(df_total, apenas_um_mes=None):
    output = io.BytesIO()
    df_input = df_total.copy()
    df_input['dt_aux'] = pd.to_datetime(df_input['Data'], format='%d/%m/%Y')
    
    manha = df_input[df_input['Reunião'] == 'Flash Manhã'][['Data', 'Dia', 'Apresentador', 'Backup']].copy()
    manha.columns = ['Data', 'Dia', 'Responsável Manhã', 'Backup Manhã']
    tarde = df_input[df_input['Reunião'].isin(['Flash Tarde', 'DOR'])][['Data', 'Apresentador', 'Backup', 'Reunião']].copy()
    tarde.columns = ['Data', 'Responsável Tarde', 'Backup Tarde', 'Tipo Tarde/DOR']
    
    df_base = pd.merge(manha, tarde, on='Data', how='outer').fillna("")
    df_base['dt_obj'] = pd.to_datetime(df_base['Data'], format='%d/%m/%Y')
    df_base = df_base.sort_values('dt_obj')
    
    if apenas_um_mes:
        df_base = df_base[df_base['dt_obj'].dt.month == MESES_NOMES[apenas_um_mes]]

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook, worksheet = writer.book, writer.book.add_worksheet('Escala')
        f_mes = workbook.add_format({'bold': True, 'bg_color': '#D9EAD3', 'align': 'center', 'border': 1})
        f_hd = workbook.add_format({'bold': True, 'bg_color': '#ff4b4b', 'font_color': 'white', 'border': 1})
        f_cl = workbook.add_format({'border': 1})
        cols = ['Data', 'Dia', 'Responsável Manhã', 'Backup Manhã', 'Tipo Tarde/DOR', 'Responsável Tarde', 'Backup Tarde']
        for i, v in enumerate(cols): 
            worksheet.write(0, i, v, f_hd)
            worksheet.set_column(i, i, 18)
        
        row_idx = 1
        for mes in ([apenas_um_mes] if apenas_um_mes else list(MESES_NOMES.keys())):
            df_m = df_base[df_base['dt_obj'].dt.month == MESES_NOMES[mes]]
            if df_m.empty: continue
            worksheet.merge_range(row_idx, 0, row_idx, 6, mes.upper(), f_mes)
            row_idx += 1
            for _, r in df_m.iterrows():
                for i, c in enumerate(cols): worksheet.write(row_idx, i, str(r[c]), f_cl)
                row_idx += 1
    return output.getvalue()

# --- GERAÇÃO DE ESCALA COM NOVAS REGRAS ---
def gerar_escala_inteligente(nomes):
    # 1. Embaralhamento Não-Alfabético (Semente fixa para consistência)
    random.seed(42) 
    fila_flash = nomes.copy()
    random.shuffle(fila_flash)
    
    nomes_dor = [n for n in nomes if n not in ["Dani", "Rafael"]]
    random.shuffle(nomes_dor)
    
    ano = datetime.now().year
    dias = pd.date_range(datetime(ano, 1, 1), datetime(ano, 12, 31), freq='B')
    escala = []
    
    # Ponteiros
    p_f, p_d = 0, 0
    
    for dia in dias:
        data_s = dia.strftime("%d/%m/%Y")
        sem = dia.isocalendar()[1]
        d_sem = dia.weekday()
        d_nome = ["Segunda-Feira", "Terça-Feira", "Quarta-Feira", "Quinta-Feira", "Sexta-Feira"][d_sem]
        
        # Lista de quem já apresentou NESTA semana
        apresentaram_na_semana = [e['Apresentador'] for e in escala if e['Semana'] == sem]
        
        # --- FLASH MANHÃ ---
        tentativas = 0
        while fila_flash[p_f % len(fila_flash)] in apresentaram_na_semana and tentativas < len(fila_flash):
            p_f += 1
            tentativas += 1
        
        ap_m = fila_flash[p_f % len(fila_flash)]
        b1_m = encontrar_backup_vivo(ap_m, nomes)
        b2_m = encontrar_backup_vivo(b1_m, nomes)
        
        escala.append({
            "Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": "Flash Manhã",
            "Apresentador": ap_m, "Backup": b1_m, "Backup2": b2_m, "Backup3": encontrar_backup_vivo(b2_m, nomes),
            "Link": f"https://outlook.office.com/calendar/0/deeplink/compose?subject=Flash%20Manhã&startdt={dia.strftime('%Y-%m-%d')}T09:45:00"
        })
        apresentaram_na_semana.append(ap_m)
        p_f += 1

        # --- TARDE (DOR ou FLASH) ---
        tipo_t = "DOR" if d_sem in [1, 3] else "Flash Tarde"
        alvo_lista = nomes_dor if tipo_t == "DOR" else fila_flash
        ptr = p_d if tipo_t == "DOR" else p_f
        
        tentativas = 0
        while alvo_lista[ptr % len(alvo_lista)] in apresentaram_na_semana and tentativas < len(alvo_lista):
            ptr += 1
            tentativas += 1
            
        ap_t = alvo_lista[ptr % len(alvo_lista)]
        b1_t = encontrar_backup_vivo(ap_t, nomes)
        
        escala.append({
            "Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": tipo_t,
            "Apresentador": ap_t, "Backup": b1_t, "Backup2": encontrar_backup_vivo(b1_t, nomes),
            "Backup3": encontrar_backup_vivo(encontrar_backup_vivo(b1_t, nomes), nomes),
            "Link": f"https://outlook.office.com/calendar/0/deeplink/compose?subject={tipo_t}&startdt={dia.strftime('%Y-%m-%d')}T15:00:00"
        })
        
        if tipo_t == "DOR": p_d = ptr + 1
        else: p_f = ptr + 1
            
    return pd.DataFrame(escala)

# --- UI PRINCIPAL ---
if check_login():
    # Carregando e limpando Bianca S.
    try:
        df_csv = pd.read_csv(SHEET_URL)
        nomes_brutos = df_csv['Funcionario'].dropna().unique().tolist()
        nomes_limpos = sorted([n for n in nomes_brutos if n not in ["Faiha", "Sonia", "Enrique", "Bianca S."]])
    except:
        nomes_limpos = list(MAPA_REFERENCIA.keys())

    df_total = gerar_escala_inteligente(nomes_limpos)
    
    st.title(f"🚀 MMD | Portal de Escalas {datetime.now().year}")
    
    c1, c2 = st.columns(2)
    with c1:
        with st.expander("📂 Exportar Mês"):
            m = st.selectbox("Mês:", list(MESES_NOMES.keys()))
            st.download_button(f"Baixar {m}", exportar_excel_mmd(df_total, m), f"Escala_{m}.xlsx")
    with c2:
        with st.expander("📅 Exportar Ano"):
            st.download_button("Baixar Ano Completo", exportar_excel_mmd(df_total), "Escala_Anual.xlsx")

    st.divider()
    busca = st.selectbox("🔍 Buscar por Apresentador:", ["Todos"] + nomes_limpos)
    if busca != "Todos":
        df_b = df_total[df_total["Apresentador"] == busca]
        st.info(f"📊 {busca} tem {len(df_b[df_b['Reunião']=='DOR'])} reuniões DOR no ano.")
        st.dataframe(df_b[["Data", "Dia", "Reunião", "Backup", "Link"]], 
                     column_config={"Link": st.column_config.LinkColumn("Outlook")}, use_container_width=True, hide_index=True)

    st.divider()
    sem_idx = st.select_slider("Semana:", options=sorted(df_total["Semana"].unique()), value=datetime.now().isocalendar()[1])
    df_s = df_total[df_total["Semana"] == sem_idx]
    
    for dt, gp in df_s.groupby("Data", sort=False):
        st.markdown(f"**{gp['Dia'].iloc[0]} - {dt}**")
        cols = st.columns(len(gp))
        for i, (_, r) in enumerate(gp.iterrows()):
            with cols[i]:
                st.markdown(f"""
                <div style="background:#f0f2f6; padding:15px; border-radius:10px; border-left:5px solid #ff4b4b;">
                    <small>{r['Reunião']}</small><br>
                    <b>🏆 {r['Apresentador']}</b><br>
                    <small>🔄 B1: {r['Backup']}</small><br>
                    <small>🛡️ B2: {r['Backup2']}</small>
                </div>""", unsafe_allow_html=True)
                st.link_button("📅 Agendar", r['Link'], use_container_width=True)
