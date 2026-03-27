import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MMD | Escala de Apresentações", layout="wide")

SHEET_ID = "1rFbrhxG72T2qhT2lMclAyLtjlHgtqvbxHFrVZ_KlmAU"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

USER_ACCESS = "MMD-Board"
PASS_ACCESS = "@MMD123#"

MAPA_BACKUPS = {
    "Abigail": "Dani", "Amanda": "Mijal", "Anna": "Soledad", 
    "Ariel": "Rafael", "Bianca M.": "Ariel", "Bianca S.": "Amanda", 
    "Bruna": "Anna Laura", "Bruno": "Bianca M.", "Enrique": "Jazmin", 
    "Dani": "Sonia", "Debora": "Bruna", "Diana": "Julia", 
    "Florencia": "Diana", "Gisele": "Thiago", 
    "Honorato": "Bruno", "Jazmin": "Abigail", "Jesus": "Luca", 
    "Julia": "Honorato", "Livia": "Bianca S.", "Luca": "Enrique", 
    "Mijal": "Livia", "Rafael": "Florencia", "Renan": "Debora", 
    "Sonia": "Jesus", "Soledad": "Gisele", "Thiago": "Renan"
}

# --- FUNÇÃO DE LEITURA COMPLETA ---
def ler_pagina_completa():
    if st.session_state.get("voz", False):
        components.html("""
            <script>
                function lerTudo() {
                    window.speechSynthesis.cancel();
                    // Seleciona textos de títulos, cards e informações do Streamlit
                    let textos = document.querySelectorAll('h1, h2, h3, b, span, .stMarkdown');
                    let conteudo = "";
                    textos.forEach(t => {
                        if(t.innerText.length > 2) conteudo += t.innerText + ". ";
                    });
                    var msg = new SpeechSynthesisUtterance(conteudo);
                    msg.lang = 'pt-BR';
                    msg.rate = 1.1;
                    window.speechSynthesis.speak(msg);
                }
                // Executa após um pequeno delay para carregar os elementos
                setTimeout(lerTudo, 1000);
            </script>
        """, height=0)

def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.markdown("<h2 style='text-align: center;'>Portal de Escalas MMD</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            with st.form("login_system"):
                user = st.text_input("Usuário").strip()
                password = st.text_input("Senha", type="password").strip()
                if st.form_submit_button("Acessar Painel", use_container_width=True):
                    if user == USER_ACCESS and password == PASS_ACCESS:
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")
        return False
    return True

def criar_link_outlook(data_str, reuniao, apresentador):
    try:
        data_obj = datetime.strptime(data_str, "%d/%m/%Y")
        data_iso = data_obj.strftime("%Y-%m-%d")
        hora_start = "09:45:00" if "Manhã" in reuniao else "15:00:00"
        hora_end = "10:15:00" if "Manhã" in reuniao else "15:30:00"
        assunto = urllib.parse.quote(f"🔔 Apresentação MMD: {reuniao}")
        corpo = urllib.parse.quote(f"Apresentador: {apresentador}")
        return f"https://outlook.office.com/calendar/0/deeplink/compose?subject={assunto}&body={corpo}&startdt={data_iso}T{hora_start}&enddt={data_iso}T{hora_end}"
    except: return "#"

@st.cache_data(ttl=60)
def carregar_nomes():
    try:
        df_sheets = pd.read_csv(SHEET_URL)
        return sorted(df_sheets['Funcionario'].dropna().unique().tolist())
    except: return []

def gerar_escala_final(nomes):
    ano_atual = 2026
    data_inicio = datetime(ano_atual, 1, 1)
    data_fim = datetime(ano_atual, 12, 31)
    dias = pd.date_range(data_inicio, data_fim, freq='B')
    fila_flash = nomes.copy()
    fila_dor = [n for n in nomes if n not in ["Dani", "Rafael"]]
    idx_f, idx_d, escala = 0, 0, []
    for dia in dias:
        data_s = dia.strftime("%d/%m/%Y")
        sem = dia.isocalendar()[1]
        dia_semana = dia.weekday()
        dia_nome = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"][dia_semana]
        apresentadores_na_semana = [item['Apresentador'] for item in escala if item['Semana'] == sem]
        while fila_flash[idx_f % len(fila_flash)] in apresentadores_na_semana: idx_f += 1
        ap_m = fila_flash[idx_f % len(fila_flash)]
        escala.append({"Semana": sem, "Data": data_s, "Dia": dia_nome, "Reunião": "Flash Manhã", "Apresentador": ap_m, "Backup": MAPA_BACKUPS.get(ap_m, "N/A"), "Link": criar_link_outlook(data_s, "Flash Manhã", ap_m)})
        apresentadores_na_semana.append(ap_m)
        idx_f += 1
        if dia_semana in [1, 3]: 
            while fila_dor[idx_d % len(fila_dor)] in apresentadores_na_semana: idx_d += 1
            ap_d = fila_dor[idx_d % len(fila_dor)]
            escala.append({"Semana": sem, "Data": data_s, "Dia": dia_nome, "Reunião": "DOR", "Apresentador": ap_d, "Backup": MAPA_BACKUPS.get(ap_d, "N/A"), "Link": criar_link_outlook(data_s, "DOR", ap_d)})
            idx_d += 1
        elif dia_semana in [0, 2, 4]: 
            while fila_flash[idx_f % len(fila_flash)] in apresentadores_na_semana: idx_f += 1
            ap_t = fila_flash[idx_f % len(fila_flash)]
            escala.append({"Semana": sem, "Data": data_s, "Dia": dia_nome, "Reunião": "Flash Tarde", "Apresentador": ap_t, "Backup": MAPA_BACKUPS.get(ap_t, "N/A"), "Link": criar_link_outlook(data_s, "Flash Tarde", ap_t)})
            idx_f += 1
    return pd.DataFrame(escala)

def renderizar_card(row):
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-bottom: 10px;">
        <b style="font-size: 14px;">{row['Reunião']}</b><br>
        <span style="font-size: 18px; font-weight: bold;">🏆 {row['Apresentador']}</span><br>
        <span style="font-size: 13px;">🔄 Backup: {row['Backup']}</span>
    </div>
    """, unsafe_allow_html=True)

if check_login():
    nomes_lista = carregar_nomes()
    if nomes_lista:
        df_total = gerar_escala_final(nomes_lista)
        
        # Sidebar
        if "voz" not in st.session_state: st.session_state.voz = False
        btn_voz = "🔴 Desativar Leitura" if st.session_state.voz else "🔊 Ativar Leitura Completa"
        if st.sidebar.button(btn_voz):
            st.session_state.voz = not st.session_state.voz
            st.rerun()
        
        if st.sidebar.button("🚪 Sair"):
            st.session_state.logged_in = False
            st.rerun()

        st.title("🚀 MMD | Dashboard de Apresentações")
        
        # Executa a leitura se a voz estiver ligada
        ler_pagina_completa()

        # Filtro
        filtro_nome = st.selectbox("🔍 Buscar por Apresentador:", ["Todos"] + nomes_lista)
        
        if filtro_nome != "Todos":
            df_pessoal = df_total[df_total["Apresentador"] == filtro_nome]
            st.info(f"📊 {filtro_nome} possui {len(df_pessoal)} apresentações em 2026.")
            st.dataframe(df_pessoal[["Data", "Dia", "Reunião", "Backup"]], hide_index=True, use_container_width=True)

        st.subheader("🗓️ Visualização por Semana")
        sem_atual = datetime.now().isocalendar()[1]
        sem_busca = st.select_slider("Selecione a Semana:", options=sorted(df_total["Semana"].unique()), value=sem_atual)
        
        df_semana = df_total[df_total["Semana"] == sem_busca]
        
        for d_label, group in df_semana.groupby("Data", sort=False):
            st.markdown(f"**{group['Dia'].iloc[0]} - {d_label}**")
            cols = st.columns(len(group))
            for i, (_, row) in enumerate(group.iterrows()):
                with cols[i]:
                    renderizar_card(row)
