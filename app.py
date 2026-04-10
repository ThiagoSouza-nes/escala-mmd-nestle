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

# MAPA DE HERANÇA (Bianca S. Removida -> Livia aponta para Amanda)
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

# --- ACESSIBILIDADE ---
def injetar_leitor_acessibilidade():
    components.html("""
        <script>
            const synth = window.speechSynthesis;
            let ultimoTexto = "";
            function falar(texto) {
                if (!texto || texto === ultimoTexto) return;
                synth.cancel(); 
                const ut = new SpeechSynthesisUtterance(texto);
                ut.lang = 'pt-BR';
                ut.rate = 1.1;
                ultimoTexto = texto;
                synth.speak(ut);
                setTimeout(() => { ultimoTexto = ""; }, 800);
            }
            const docAlvo = window.parent.document;
            docAlvo.addEventListener('mouseover', (e) => {
                const el = e.target;
                const textoParaLer = (el.innerText || el.textContent).trim();
                if (textoParaLer.length > 0 && !textoParaLer.includes("http")) {
                    falar(textoParaLer);
                }
            }, true);
            docAlvo.addEventListener('mouseout', () => { synth.cancel(); }, true);
        </script>
    """, height=0, width=0)

# --- LOGIN ---
def check_login():
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.markdown("<h2 style='text-align: center;'>Portal de Escalas MMD</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            with st.form("login"):
                u = st.text_input("Usuário").strip()
                p = st.text_input("Senha", type="password").strip()
                if st.form_submit_button("Acessar Painel", use_container_width=True):
                    if u == USER_ACCESS and p == PASS_ACCESS:
                        st.session_state.logged_in = True
                        st.rerun()
                    else: st.error("Incorreto.")
        return False
    return True

# --- GERAÇÃO DE ESCALA ---
def gerar_escala_final(nomes):
    random.seed(42) # Semente para embaralhamento fixo (não muda ao dar refresh)
    fila_flash = nomes.copy()
    random.shuffle(fila_flash)
    
    nomes_dor = [n for n in nomes if n not in ["Dani", "Rafael"]]
    random.shuffle(nomes_dor)
    
    ano = datetime.now().year
    dias = pd.date_range(datetime(ano, 1, 1), datetime(ano, 12, 31), freq='B')
    escala = []
    
    p_f, p_d = 0, 0
    
    for dia in dias:
        data_s = dia.strftime("%d/%m/%Y")
        sem = dia.isocalendar()[1]
        d_sem = dia.weekday()
        d_nome = ["Segunda-Feira", "Terça-Feira", "Quarta-Feira", "Quinta-Feira", "Sexta-Feira"][d_sem]
        
        # Filtra quem já apresentou nesta semana específica
        apresentaram_na_semana = [e['Apresentador'] for e in escala if e['Semana'] == sem]
        
        # 1. FLASH MANHÃ
        tentativas = 0
        while fila_flash[p_f % len(fila_flash)] in apresentaram_na_semana and tentativas < len(fila_flash):
            p_f += 1
            tentativas += 1
        
        ap_m = fila_flash[p_f % len(fila_flash)]
        b1_m = encontrar_backup_vivo(ap_m, nomes); b2_m = encontrar_backup_vivo(b1_m, nomes)
        
        escala.append({
            "Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": "Flash Manhã",
            "Apresentador": ap_m, "Backup": b1_m, "Backup2": b2_m, "Backup3": encontrar_backup_vivo(b2_m, nomes),
            "Link": f"https://outlook.office.com/calendar/0/deeplink/compose?subject=Flash%20Manhã&startdt={dia.strftime('%Y-%m-%d')}T09:45:00"
        })
        apresentaram_na_semana.append(ap_m)
        p_f += 1

        # 2. TARDE (DOR ou FLASH)
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

# --- EXPORTAÇÃO EXCEL ---
def exportar_excel(df_total, mes_nome=None):
    output = io.BytesIO()
    df_copy = df_total.copy()
    df_copy['dt_aux'] = pd.to_datetime(df_copy['Data'], format='%d/%m/%Y')
    
    m = df_copy[df_copy['Reunião'] == 'Flash Manhã'][['Data', 'Dia', 'Apresentador', 'Backup']].rename(columns={'Apresentador':'Responsável Manhã', 'Backup':'Backup Manhã'})
    t = df_copy[df_copy['Reunião'].isin(['Flash Tarde', 'DOR'])][['Data', 'Apresentador', 'Backup', 'Reunião']].rename(columns={'Apresentador':'Responsável Tarde', 'Backup':'Backup Tarde', 'Reunião':'Tipo Tarde/DOR'})
    
    df_final = pd.merge(m, t, on='Data', how='outer').fillna("")
    df_final['dt_obj'] = pd.to_datetime(df_final['Data'], format='%d/%m/%Y')
    df_final = df_final.sort_values('dt_obj')
    
    if mes_nome: df_final = df_final[df_final['dt_obj'].dt.month == MESES_NOMES[mes_nome]]

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook, worksheet = writer.book, writer.book.add_worksheet('Escala')
        f_mes = workbook.add_format({'bold': True, 'bg_color': '#D9EAD3', 'align': 'center', 'border': 1})
        f_hd = workbook.add_format({'bold': True, 'bg_color': '#ff4b4b', 'font_color': 'white', 'border': 1})
        f_cl = workbook.add_format({'border': 1})
        
        cols = ['Data', 'Dia', 'Responsável Manhã', 'Backup Manhã', 'Tipo Tarde/DOR', 'Responsável Tarde', 'Backup Tarde']
        for i, v in enumerate(cols): 
            worksheet.write(0, i, v, f_hd)
            worksheet.set_column(i, i, 18)
            
        cur_row = 1
        meses_lista = [mes_nome] if mes_nome else list(MESES_NOMES.keys())
        for mes in meses_lista:
            df_m = df_final[df_final['dt_obj'].dt.month == MESES_NOMES[mes]]
            if df_m.empty: continue
            worksheet.merge_range(cur_row, 0, cur_row, 6, mes.upper(), f_mes)
            cur_row += 1
            for _, r in df_m.iterrows():
                for i, c in enumerate(cols): worksheet.write(cur_row, i, str(r[c]), f_cl)
                cur_row += 1
    return output.getvalue()

def renderizar_card(row):
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; min-height: 220px; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
        <b style="font-size: 14px; color: #31333F;">{row['Reunião']}</b><br><br>
        <span style="font-size: 18px; color: #333; font-weight: bold;">🏆 {row['Apresentador']}</span><br><br>
        <span style="font-size: 13px; color: #666;">🔄 Backup: {row['Backup']}</span><br>
        <span style="font-size: 13px; color: #777;">🛡️ Backup 2: {row['Backup2']}</span><br>
        <span title="Backup 3: {row['Backup3']}" style="font-size: 11px; color: #bbb; cursor: help;">🔍 Backup 3 (Hover)</span>
        <div style="margin-top: 15px;">
            <a href="{row['Link']}" target="_blank" style="display: block; text-decoration: none; color: white; background-color: #0078d4; padding: 8px; border-radius: 5px; font-size: 11px; text-align: center; font-weight: bold;">📅 AGENDAR</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- EXECUÇÃO ---
if check_login():
    try:
        df_csv = pd.read_csv(SHEET_URL)
        nomes_limpos = sorted([n for n in df_csv['Funcionario'].dropna().unique() if n not in ["Faiha", "Sonia", "Enrique", "Bianca S."]])
    except: nomes_limpos = list(MAPA_REFERENCIA.keys())

    st.sidebar.title("⚙️ Configurações")
    if st.sidebar.toggle("♿ Ativar Acessibilidade", value=False): injetar_leitor_acessibilidade()
    
    df_total = gerar_escala_final(nomes_limpos)
    st.title(f"🚀 MMD | Portal de Escalas {datetime.now().year}")

    c1, c2 = st.columns(2)
    with c1:
        with st.expander("📂 Exportar Mês"):
            m = st.selectbox("Mês:", list(MESES_NOMES.keys()))
            st.download_button(f"Baixar {m}", exportar_excel(df_total, m), f"Escala_{m}.xlsx", use_container_width=True)
    with c2:
        with st.expander("📅 Exportar Ano"):
            st.download_button("Baixar Ano Completo", exportar_excel(df_total), "Escala_Anual.xlsx", use_container_width=True)

    st.divider()
    busca = st.selectbox("🔍 Buscar por Apresentador:", ["Todos"] + nomes_limpos)
    if busca != "Todos":
        df_b = df_total[df_total["Apresentador"] == busca]
        st.info(f"📊 {busca}: {len(df_b[df_b['Reunião']=='DOR'])} reuniões DOR no ano.")
        st.dataframe(df_b[["Data", "Dia", "Reunião", "Backup", "Link"]], column_config={"Link": st.column_config.LinkColumn("Outlook")}, use_container_width=True, hide_index=True)

    st.divider()
    sem_idx = st.select_slider("Semana:", options=sorted(df_total["Semana"].unique()), value=datetime.now().isocalendar()[1])
    df_s = df_total[df_total["Semana"] == sem_idx]
    
    for dt, gp in df_s.groupby("Data", sort=False):
        st.markdown(f"**{gp['Dia'].iloc[0]} - {dt}**")
        cols = st.columns(len(gp))
        for i, (_, r) in enumerate(gp.iterrows()):
            with cols[i]: renderizar_card(r)
